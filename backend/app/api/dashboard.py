from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.database.db import get_db
from app.models.models import Patient, PatientStatus, FollowUpTask, Conversation, Appointment, Escalation
from app.schemas.schemas import DashboardStats
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def aware(dt):
    return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt


@router.get("/stats", response_model=DashboardStats)
async def stats(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "PATIENT":
        raise HTTPException(403, "Clinic dashboard only")
    all_p = (await db.execute(select(Patient))).scalars().all()
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    total = len([p for p in all_p if p.follow_up_status != PatientStatus.COMPLETED.value])
    due = len([p for p in all_p if p.follow_up_date and start <= aware(p.follow_up_date) < end])
    overdue = len([p for p in all_p if p.follow_up_status == PatientStatus.OVERDUE.value])
    responded = len([p for p in all_p if p.follow_up_status == PatientStatus.RESPONDED.value])
    booked = len([p for p in all_p if p.follow_up_status == PatientStatus.BOOKED.value])
    rescheduled = len([p for p in all_p if p.follow_up_status == PatientStatus.RESCHEDULED.value])
    escalated = len([p for p in all_p if p.follow_up_status == PatientStatus.ESCALATED.value])
    noresp = len([p for p in all_p if p.follow_up_status == PatientStatus.NO_RESPONSE.value])
    contacted = len([p for p in all_p if (p.contact_attempts or 0) > 0 or p.follow_up_status not in (PatientStatus.DUE.value,)])
    completed = len([p for p in all_p if p.follow_up_status == PatientStatus.COMPLETED.value])
    return DashboardStats(
        total_followups=total,
        due_today=due,
        overdue=overdue,
        responded=responded,
        booked=booked,
        rescheduled=rescheduled,
        escalations=escalated,
        no_response=noresp,
        completion_rate=round((booked + completed) / max(len(all_p), 1) * 100, 1),
        response_rate=round((responded + booked + rescheduled + escalated) / max(contacted, 1) * 100, 1),
    )


@router.get("/activity")
async def activity(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "PATIENT":
        raise HTTPException(403, "Clinic dashboard only")
    patients = {p.id: p.name for p in (await db.execute(select(Patient))).scalars().all()}
    msgs = (await db.execute(select(Conversation).order_by(Conversation.created_at.desc()).limit(25))).scalars().all()
    tasks = (await db.execute(select(FollowUpTask).order_by(FollowUpTask.created_at.desc()).limit(20))).scalars().all()
    events = [{
        "type": "MESSAGE", "patient_id": m.patient_id, "patient_name": patients.get(m.patient_id, "Patient"),
        "text": m.message, "direction": m.direction, "channel": m.channel, "status": m.delivery_status, "at": m.created_at,
    } for m in msgs]
    events += [{
        "type": "TASK", "patient_id": t.patient_id, "patient_name": patients.get(t.patient_id, "Patient"),
        "text": f"{t.action.replace('_', ' ').title()} via {t.channel}", "direction": "SYSTEM", "channel": t.channel, "status": t.status, "at": t.created_at,
    } for t in tasks]
    return sorted(events, key=lambda x: aware(x["at"]), reverse=True)[:30]


@router.get("/today")
async def today(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "PATIENT":
        raise HTTPException(403, "Clinic dashboard only")
    now = datetime.now(timezone.utc)
    appts = (await db.execute(select(Appointment).order_by(Appointment.date.asc()))).scalars().all()
    escs = (await db.execute(select(Escalation).where(Escalation.status == "OPEN").order_by(Escalation.created_at.desc()))).scalars().all()
    return {
        "appointments_next_7_days": len([a for a in appts if now <= aware(a.date) <= now + timedelta(days=7) and a.status != "CANCELLED"]),
        "open_escalations": len(escs),
        "automation_running": True,
    }
