from datetime import datetime, timezone

from app.models.models import (
    Patient,
    Conversation,
    Escalation,
    Appointment,
    Intent,
    PatientStatus,
    Priority,
    EscalationType,
)

from app.agents.response_generator import generate_initial_followup
from app.services.communication import communication_service
from app.core.config import settings


ESCALATION_INTENTS = {
    Intent.PAIN_OR_SYMPTOM:
        EscalationType.CLINICAL,

    Intent.FEE_QUESTION:
        EscalationType.FINANCIAL,

    Intent.PAYMENT_ISSUE:
        EscalationType.FINANCIAL,

    Intent.REQUEST_HUMAN:
        EscalationType.ADMINISTRATIVE,
}


class PatientFollowUpAgent:

    ESCALATION_INTENTS = ESCALATION_INTENTS


    def __init__(self):

        from app.agents.followup_graph import (
            build_followup_graph
        )

        self.graph = build_followup_graph(self)


    async def get_patient_context(
        self,
        db,
        patient_id
    ):

        p = await db.get(
            Patient,
            patient_id
        )

        if not p:
            return {}

        return {
            "patient_id": p.id,
            "name": p.name,
            "phone": p.phone,
            "treatment": p.treatment,
            "treatment_status":
                p.treatment_status,
            "follow_up_status":
                p.follow_up_status,
            "follow_up_date":
                str(p.follow_up_date)
                if p.follow_up_date
                else None,
            "last_visit":
                str(p.last_visit)
                if p.last_visit
                else None,
            "contact_attempts":
                p.contact_attempts,
            "clinic_name":
                settings.CLINIC_NAME,
        }


    # =================================================
    # LANGGRAPH ENTRY POINT
    # =================================================

    async def process_message(
        self,
        db,
        patient_id,
        message,
        channel="SMS"
    ):

        result = await self.graph.ainvoke(
            {
                "db": db,
                "patient_id": patient_id,
                "message": message,
                "channel": channel,
                "trace": [],
            }
        )

        return {
            "reply":
                result.get(
                    "reply",
                    "Unable to process message."
                ),

            "intent":
                (
                    result["intent"].value
                    if result.get("intent")
                    else "OTHER"
                ),

            "action":
                result.get(
                    "action",
                    "NONE"
                ),

            "escalated":
                result.get(
                    "escalated",
                    False
                ),

            # Useful for debugging and demonstrating
            # that LangGraph is actually executing.
            "graph_trace":
                result.get(
                    "trace",
                    []
                ),
        }


    async def send_initial_followup(
        self,
        db,
        patient_id,
        channel=None
    ):

        ctx = await self.get_patient_context(
            db,
            patient_id
        )

        if not ctx:
            return None

        p = await db.get(
            Patient,
            patient_id
        )

        channel = (
            channel
            or p.preferred_channel
            or "SMS"
        )

        msg = generate_initial_followup(ctx)

        if channel.upper() == "VOICE":

            delivery = (
                await communication_service
                .start_voice_call(
                    p.phone
                )
            )

        else:

            delivery = (
                await communication_service
                .send_sms(
                    p.phone,
                    msg
                )
            )

        p.follow_up_status = (
            PatientStatus.CONTACTED.value
        )

        p.contact_attempts = (
            p.contact_attempts or 0
        ) + 1

        p.last_contact = datetime.now(
            timezone.utc
        )

        db.add(
            Conversation(
                patient_id=patient_id,
                channel=channel,
                direction="OUTBOUND",
                message=msg,
                intent="INITIAL_FOLLOWUP",
                agent_action="SEND_FOLLOWUP",
                delivery_status=
                    delivery["status"],
                provider_message_id=
                    delivery.get(
                        "message_id"
                    ),
            )
        )

        await db.commit()

        return msg


    async def check_available_slots(
        self,
        db,
        date_str,
        time_range=None
    ):

        from datetime import datetime

        base = datetime.strptime(
            date_str,
            "%Y-%m-%d"
        )

        hours = [
            9, 10, 11,
            14, 15, 16
        ]

        return [
            base.replace(
                hour=h
            ).strftime(
                "%Y-%m-%d %H:%M"
            )
            for h in hours
            if not (
                time_range == "morning"
                and h >= 12
            )
            and not (
                time_range == "afternoon"
                and h < 12
            )
        ]


    async def book_appointment(
        self,
        db,
        patient_id,
        date,
        treatment_type=None
    ):

        p = await db.get(
            Patient,
            patient_id
        )

        a = Appointment(
            patient_id=patient_id,
            date=date,
            treatment_type=(
                treatment_type
                or p.treatment
            ),
            status="CONFIRMED"
        )

        db.add(a)

        p.follow_up_status = (
            PatientStatus.BOOKED.value
        )

        await db.commit()

        return a


    def _action(self, intent):

        return {
            Intent.BOOK_APPOINTMENT:
                "OFFER_SLOTS",

            Intent.RESCHEDULE_APPOINTMENT:
                "OFFER_RESCHEDULE",

            Intent.CONFIRM_APPOINTMENT:
                "CONFIRM_BOOKING",

            Intent.CANCEL_APPOINTMENT:
                "DISCOURAGE_CANCEL",

            Intent.PAIN_OR_SYMPTOM:
                "ESCALATE_CLINICAL",

            Intent.TREATMENT_QUESTION:
                "EXPLAIN_TREATMENT",

            Intent.FEE_QUESTION:
                "ESCALATE_FINANCIAL",

            Intent.PAYMENT_ISSUE:
                "ESCALATE_FINANCIAL",

            Intent.NOT_INTERESTED:
                "MARK_NOT_INTERESTED",

            Intent.REQUEST_HUMAN:
                "ESCALATE_ADMIN",

            Intent.NO_RESPONSE:
                "WAIT",

            Intent.OTHER:
                "GENERAL_REPLY",

        }.get(
            intent,
            "NONE"
        )


    async def _escalate(
        self,
        db,
        patient,
        intent,
        message,
        urgent
    ):

        typ = ESCALATION_INTENTS.get(
            intent,
            EscalationType.ADMINISTRATIVE
        )

        priority = (
            Priority.URGENT.value
            if urgent
            else Priority.HIGH.value
        )

        summary = (
            f"Patient: {patient.name}\n"
            f"Treatment: {patient.treatment}\n"
            f"Status: {patient.treatment_status}\n"
            f"Message: {message}\n"
            f"Intent: {intent.value}\n"
            f"Priority: {priority}\n"
            "Staff review required."
        )

        db.add(
            Escalation(
                patient_id=patient.id,
                type=typ.value,
                priority=priority,
                reason=(
                    "Patient message triggered "
                    f"{intent.value}"
                ),
                patient_message=message,
                detected_intent=
                    intent.value,
                staff_summary=summary,
            )
        )

        patient.follow_up_status = (
            PatientStatus.ESCALATED.value
        )

        patient.priority = priority


agent = PatientFollowUpAgent()
