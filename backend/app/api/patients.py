from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from app.database.db import get_db
from app.models.models import Patient, Conversation, Escalation, Appointment, FollowUpTask
from app.schemas.schemas import PatientOut, PatientCreate, PatientUpdate, ConversationOut, EscalationOut, AppointmentOut
from app.core.auth import get_current_user
from app.services.followup import create_followup_task
from app.services.realtime import manager

router = APIRouter(prefix="/api/patients", tags=["patients"])


def ensure_access(user, patient_id=None):
    if user["role"] == "PATIENT" and patient_id is not None and user.get("patient_id") != patient_id:
        raise HTTPException(403, "Patients can only access their own record")


@router.get("", response_model=List[PatientOut])
async def list_patients(status: Optional[str] = None, priority: Optional[str] = None, search: Optional[str] = None, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    q = select(Patient)
    if user["role"] == "PATIENT":
        q = q.where(Patient.id == user.get("patient_id"))
    if status:
        q = q.where(Patient.follow_up_status == status)
    if priority:
        q = q.where(Patient.priority == priority)
    if search:
        q = q.where(Patient.name.ilike(f"%{search}%"))
    q = q.order_by(Patient.follow_up_date.asc())
    return (await db.execute(q)).scalars().all()


@router.get("/me/summary")
async def my_summary(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] != "PATIENT" or not user.get("patient_id"):
        raise HTTPException(403, "Patient account required")
    pid = user["patient_id"]
    p = await db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient profile not found")
    conversations = (await db.execute(select(Conversation).where(Conversation.patient_id == pid).order_by(Conversation.created_at.desc()).limit(60))).scalars().all()
    appointments = (await db.execute(select(Appointment).where(Appointment.patient_id == pid).order_by(Appointment.date.asc()))).scalars().all()
    tasks = (await db.execute(select(FollowUpTask).where(FollowUpTask.patient_id == pid).order_by(FollowUpTask.scheduled_at.desc()))).scalars().all()
    escalations = (await db.execute(select(Escalation).where(Escalation.patient_id == pid).order_by(Escalation.created_at.desc()).limit(10))).scalars().all()
    return {
        "patient": PatientOut.model_validate(p).model_dump(mode="json"),
        "conversations": [ConversationOut.model_validate(x).model_dump(mode="json") for x in conversations],
        "appointments": [AppointmentOut.model_validate(x).model_dump(mode="json") for x in appointments],
        "escalations": [EscalationOut.model_validate(x).model_dump(mode="json") for x in escalations],
        "followup_tasks": [{"id": t.id, "scheduled_at": t.scheduled_at, "channel": t.channel, "action": t.action, "status": t.status, "attempt_number": t.attempt_number} for t in tasks],
    }


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    ensure_access(user, patient_id)
    p = await db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    return p


@router.post("", response_model=PatientOut)
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] not in ("DOCTOR", "STAFF"):
        raise HTTPException(403, "Clinic access required")
    values = data.model_dump()
    if values.get("follow_up_date") is None:
        values["follow_up_date"] = datetime.now(timezone.utc) + timedelta(minutes=1)
    p = Patient(**values, source="REAL")
    db.add(p)
    await db.flush()
    await create_followup_task(db, p, p.follow_up_date)
    await db.commit()
    await db.refresh(p)
    await manager.broadcast({"type": "PATIENT_CREATED", "patient_id": p.id, "name": p.name}, patient_id=p.id)
    return p


@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(patient_id: int, data: PatientUpdate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "PATIENT":
        raise HTTPException(403, "Clinic access required")
    p = await db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    old_date = p.follow_up_date
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    if data.follow_up_date and data.follow_up_date != old_date:
        await create_followup_task(db, p, data.follow_up_date, "FOLLOWUP_UPDATED")
    await db.commit()
    await db.refresh(p)
    await manager.broadcast({"type": "PATIENT_UPDATED", "patient_id": p.id}, patient_id=p.id)
    return p


@router.get("/{patient_id}/conversations", response_model=List[ConversationOut])
async def conversations(patient_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    ensure_access(user, patient_id)
    return (await db.execute(select(Conversation).where(Conversation.patient_id == patient_id).order_by(Conversation.created_at.asc()))).scalars().all()


@router.get("/{patient_id}/appointments", response_model=List[AppointmentOut])
async def appointments(patient_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    ensure_access(user, patient_id)
    return (await db.execute(select(Appointment).where(Appointment.patient_id == patient_id).order_by(Appointment.date.asc()))).scalars().all()


@router.get("/{patient_id}/escalations", response_model=List[EscalationOut])
async def escalations(patient_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    ensure_access(user, patient_id)
    return (await db.execute(select(Escalation).where(Escalation.patient_id == patient_id).order_by(Escalation.created_at.desc()))).scalars().all()
