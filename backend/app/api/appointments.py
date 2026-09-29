from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database.db import get_db
from app.models.models import Appointment, Patient
from app.schemas.schemas import AppointmentCreate, AppointmentOut
from app.core.auth import get_current_user
from app.services.realtime import manager

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.get("", response_model=List[AppointmentOut])
async def list_all(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    q = select(Appointment).order_by(Appointment.date.asc())
    if user["role"] == "PATIENT":
        q = q.where(Appointment.patient_id == user.get("patient_id"))
    return (await db.execute(q)).scalars().all()


@router.post("", response_model=AppointmentOut)
async def create(data: AppointmentCreate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "PATIENT" and data.patient_id != user.get("patient_id"):
        raise HTTPException(403, "Patients can only book their own appointment")
    a = Appointment(**data.model_dump(), status="CONFIRMED")
    db.add(a)
    p = await db.get(Patient, data.patient_id)
    if p:
        p.follow_up_status = "BOOKED"
    await db.commit()
    await db.refresh(a)
    await manager.broadcast({"type": "APPOINTMENT_BOOKED", "patient_id": data.patient_id, "appointment_id": a.id}, patient_id=data.patient_id)
    return a


@router.put("/{appt_id}/cancel", response_model=AppointmentOut)
async def cancel(appt_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    a = await db.get(Appointment, appt_id)
    if not a:
        raise HTTPException(404, "Appointment not found")
    if user["role"] == "PATIENT" and a.patient_id != user.get("patient_id"):
        raise HTTPException(403)
    a.status = "CANCELLED"
    await db.commit()
    await db.refresh(a)
    await manager.broadcast({"type": "APPOINTMENT_CANCELLED", "patient_id": a.patient_id, "appointment_id": a.id}, patient_id=a.patient_id)
    return a
