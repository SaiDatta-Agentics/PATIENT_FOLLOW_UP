from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone
from app.database.db import get_db
from app.models.models import Escalation, Patient
from app.schemas.schemas import EscalationOut, EscalationUpdate
from app.core.auth import get_current_user
from app.services.realtime import manager

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


@router.get("", response_model=List[EscalationOut])
async def list_all(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    q = select(Escalation).order_by(Escalation.created_at.desc())
    if user["role"] == "PATIENT":
        q = q.where(Escalation.patient_id == user.get("patient_id"))
    return (await db.execute(q)).scalars().all()


@router.put("/{escalation_id}", response_model=EscalationOut)
async def update(escalation_id: int, data: EscalationUpdate, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "PATIENT":
        raise HTTPException(403, "Clinic access required")
    e = await db.get(Escalation, escalation_id)
    if not e:
        raise HTTPException(404, "Escalation not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    if data.status == "RESOLVED":
        e.resolved_at = datetime.now(timezone.utc)
        p = await db.get(Patient, e.patient_id)
        if p and p.follow_up_status == "ESCALATED":
            p.follow_up_status = "RESPONDED"
    await db.commit()
    await db.refresh(e)
    await manager.broadcast({"type": "ESCALATION_UPDATED", "patient_id": e.patient_id, "status": e.status}, patient_id=e.patient_id)
    return e
