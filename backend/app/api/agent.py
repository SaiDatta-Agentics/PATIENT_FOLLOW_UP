from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from app.database.db import get_db
from app.schemas.schemas import AgentMessageRequest, AgentResponse, SlotRequest
from app.agents.patient_followup_agent import agent
from app.core.auth import get_current_user
from app.services.realtime import manager

router = APIRouter(prefix="/api/agent", tags=["agent"])


def access(user, pid):
    if user["role"] == "PATIENT" and user.get("patient_id") != pid:
        raise HTTPException(403, "Patients can only use their own care assistant")


@router.post("/message", response_model=AgentResponse)
async def message(req: AgentMessageRequest, db=Depends(get_db), user=Depends(get_current_user)):
    access(user, req.patient_id)
    result = await agent.process_message(db, req.patient_id, req.message, req.channel)
    slots = []
    if result["action"] in ("OFFER_SLOTS", "OFFER_RESCHEDULE"):
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
        slots = await agent.check_available_slots(db, tomorrow)
    result["slots"] = slots[:4]
    await manager.broadcast({"type": "CHAT_UPDATED", "patient_id": req.patient_id, "intent": result["intent"], "action": result["action"]}, patient_id=req.patient_id)
    return AgentResponse(**result)


@router.post("/{patient_id}/followup")
async def followup(patient_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    if user["role"] == "PATIENT":
        raise HTTPException(403, "Clinic access required")
    msg = await agent.send_initial_followup(db, patient_id)
    if not msg:
        raise HTTPException(404, "Patient not found")
    await manager.broadcast({"type": "FOLLOWUP_SENT", "patient_id": patient_id}, patient_id=patient_id)
    return {"message": msg, "status": "sent"}


@router.post("/slots")
async def slots(req: SlotRequest, db=Depends(get_db), user=Depends(get_current_user)):
    return {"slots": await agent.check_available_slots(db, req.date, req.time_range)}
