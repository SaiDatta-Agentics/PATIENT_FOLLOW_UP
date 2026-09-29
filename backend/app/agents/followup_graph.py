from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import START, END, StateGraph

from app.agents.intent_classifier import classify_intent, is_urgent
from app.agents.response_generator import generate_response
from app.core.config import settings
from app.models.models import (
    Conversation,
    Intent,
    Patient,
    PatientStatus,
)
from app.services.ai import azure_ai_reply


class FollowUpState(TypedDict, total=False):
    db: Any

    patient_id: int
    message: str
    channel: str

    patient: Any
    context: dict[str, Any]

    intent: Intent
    urgent: bool
    action: str

    escalated: bool
    reply: str

    trace: list[str]


def add_trace(state: FollowUpState, step: str):
    return [*(state.get("trace") or []), step]


def build_followup_graph(agent):

    # ------------------------------------------------
    # NODE 1 - Load patient context
    # ------------------------------------------------

    async def load_context(state: FollowUpState):

        db = state["db"]
        patient_id = state["patient_id"]

        patient = await db.get(
            Patient,
            patient_id
        )

        context = {}

        if patient:
            context = await agent.get_patient_context(
                db,
                patient_id
            )

        return {
            "patient": patient,
            "context": context,
            "trace": add_trace(
                state,
                "load_context"
            ),
        }


    def patient_exists(state: FollowUpState):

        if state.get("patient") is None:
            return "missing"

        return "continue"


    async def missing_patient(state: FollowUpState):

        return {
            "reply": "Patient not found.",
            "action": "NONE",
            "escalated": False,
            "trace": add_trace(
                state,
                "patient_not_found"
            ),
        }


    # ------------------------------------------------
    # NODE 2 - Intent + safety classification
    # ------------------------------------------------

    async def classify(state: FollowUpState):

        intent = classify_intent(
            state["message"]
        )

        urgent = is_urgent(
            intent,
            state["message"]
        )

        return {
            "intent": intent,
            "urgent": urgent,
            "action": agent._action(intent),
            "trace": add_trace(
                state,
                "classify_intent"
            ),
        }


    # ------------------------------------------------
    # NODE 3 - Clinic business rules
    # ------------------------------------------------

    async def apply_rules(state: FollowUpState):

        db = state["db"]
        patient = state["patient"]

        intent = state["intent"]
        action = state["action"]

        channel = state.get(
            "channel",
            "SMS"
        )

        message = state["message"]

        # Store patient message
        db.add(
            Conversation(
                patient_id=state["patient_id"],
                channel=channel,
                direction="INBOUND",
                message=message,
                intent=intent.value,
                agent_action=action,
                delivery_status="RECEIVED",
            )
        )

        escalated = False

        if (
            intent in agent.ESCALATION_INTENTS
            or state.get("urgent", False)
        ):

            escalated = True

            await agent._escalate(
                db,
                patient,
                intent,
                message,
                state.get("urgent", False),
            )

        elif intent == Intent.CONFIRM_APPOINTMENT:

            patient.follow_up_status = (
                PatientStatus.BOOKED.value
            )

        elif intent == Intent.NOT_INTERESTED:

            patient.follow_up_status = (
                PatientStatus.COMPLETED.value
            )

        elif patient.follow_up_status in (
            PatientStatus.DUE.value,
            PatientStatus.CONTACTED.value,
            PatientStatus.OVERDUE.value,
        ):

            patient.follow_up_status = (
                PatientStatus.RESPONDED.value
            )

        return {
            "escalated": escalated,
            "trace": add_trace(
                state,
                "apply_business_rules"
            ),
        }


    # ------------------------------------------------
    # NODE 4 - Clinic approved response
    # ------------------------------------------------

    async def draft_response(state: FollowUpState):

        reply = generate_response(
            state["intent"],
            state["context"]
        )

        return {
            "reply": reply,
            "trace": add_trace(
                state,
                "draft_safe_response"
            ),
        }


    # ------------------------------------------------
    # ROUTER - Does this need Azure OpenAI?
    # ------------------------------------------------

    def ai_router(state: FollowUpState):

        if (
            state["intent"] in (
                Intent.TREATMENT_QUESTION,
                Intent.OTHER,
            )
            and settings.AZURE_OPENAI_ENDPOINT
            and settings.AZURE_OPENAI_KEY
        ):
            return "azure_ai"

        return "persist"


    # ------------------------------------------------
    # NODE 5 - Azure OpenAI
    # ------------------------------------------------

    async def azure_ai(state: FollowUpState):

        reply = state["reply"]

        system = (
            "You are the patient follow-up assistant "
            "for a dental clinic. "
            "Write concise professional English. "
            "Use the supplied patient context. "
            "Do not diagnose. "
            "Do not invent fees. "
            "Do not replace a dentist. "
            "Symptoms and uncertain clinical issues "
            "must be referred to clinic staff. "
            "Encourage dentist-recommended treatment "
            "without coercion."
        )

        prompt = (
            f"Patient context: {state['context']}\n"
            f"Patient message: {state['message']}\n"
            f"Intent: {state['intent'].value}\n"
            f"Approved draft: {state['reply']}"
        )

        try:

            generated = await azure_ai_reply(
                system,
                prompt
            )

            if generated:
                reply = generated

        except Exception:
            # Important:
            # Azure/OpenAI failure must NEVER
            # break patient chat.
            pass

        return {
            "reply": reply,
            "trace": add_trace(
                state,
                "azure_openai"
            ),
        }


    # ------------------------------------------------
    # NODE 6 - Persist final result
    # ------------------------------------------------

    async def persist(state: FollowUpState):

        db = state["db"]

        channel = state.get(
            "channel",
            "SMS"
        )

        db.add(
            Conversation(
                patient_id=state["patient_id"],
                channel=channel,
                direction="OUTBOUND",
                message=state["reply"],
                intent=state["intent"].value,
                agent_action=state["action"],
                delivery_status=(
                    "WEB_REPLY"
                    if channel == "WEB"
                    else "RECORDED"
                ),
            )
        )

        await db.commit()

        return {
            "trace": add_trace(
                state,
                "persist_response"
            ),
        }


    # =================================================
    # BUILD GRAPH
    # =================================================

    graph = StateGraph(FollowUpState)

    graph.add_node(
        "load_context",
        load_context
    )

    graph.add_node(
        "missing_patient",
        missing_patient
    )

    graph.add_node(
        "classify_intent",
        classify
    )

    graph.add_node(
        "apply_business_rules",
        apply_rules
    )

    graph.add_node(
        "draft_response",
        draft_response
    )

    graph.add_node(
        "azure_openai",
        azure_ai
    )

    graph.add_node(
        "persist_response",
        persist
    )


    # Start
    graph.add_edge(
        START,
        "load_context"
    )


    # Patient validation
    graph.add_conditional_edges(
        "load_context",
        patient_exists,
        {
            "missing": "missing_patient",
            "continue": "classify_intent",
        },
    )


    graph.add_edge(
        "missing_patient",
        END
    )


    # Standard processing
    graph.add_edge(
        "classify_intent",
        "apply_business_rules"
    )

    graph.add_edge(
        "apply_business_rules",
        "draft_response"
    )


    # AI or deterministic response
    graph.add_conditional_edges(
        "draft_response",
        ai_router,
        {
            "azure_ai": "azure_openai",
            "persist": "persist_response",
        },
    )


    graph.add_edge(
        "azure_openai",
        "persist_response"
    )

    graph.add_edge(
        "persist_response",
        END
    )


    return graph.compile()
