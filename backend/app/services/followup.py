from datetime import datetime, timezone
from sqlalchemy import select
from app.database.db import async_session
from app.models.models import Patient, FollowUpTask, Conversation, PatientStatus
from app.agents.response_generator import generate_initial_followup
from app.services.communication import communication_service
from app.services.realtime import manager
from app.core.config import settings


def aware(dt):
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def create_followup_task(db, patient: Patient, scheduled_at=None, action="INITIAL_FOLLOWUP"):
    when = scheduled_at or patient.follow_up_date or datetime.now(timezone.utc)
    task = FollowUpTask(patient_id=patient.id, scheduled_at=when, channel=patient.preferred_channel or "SMS", action=action)
    db.add(task)
    await db.flush()
    return task


async def process_due_followups():
    if not settings.AUTO_FOLLOWUP_ENABLED:
        return
    changed = []
    async with async_session() as db:
        now = datetime.now(timezone.utc)
        tasks = (await db.execute(select(FollowUpTask).where(FollowUpTask.status == "SCHEDULED"))).scalars().all()
        for task in tasks:
            if aware(task.scheduled_at) > now:
                continue
            patient = await db.get(Patient, task.patient_id)
            if not patient or patient.opted_out or patient.follow_up_status == PatientStatus.COMPLETED.value:
                task.status = "SKIPPED"
                continue
            ctx = {"name": patient.name, "treatment": patient.treatment, "treatment_status": patient.treatment_status, "clinic_name": settings.CLINIC_NAME}
            message = generate_initial_followup(ctx)
            if (task.channel or "").upper() == "VOICE":
                delivery = await communication_service.start_voice_call(patient.phone)
                logged_message = f"Voice follow-up initiated. Script: {message}"
            else:
                delivery = await communication_service.send_sms(patient.phone, message)
                logged_message = message
            db.add(Conversation(
                patient_id=patient.id,
                channel=task.channel,
                direction="OUTBOUND",
                message=logged_message,
                intent="INITIAL_FOLLOWUP",
                agent_action="AUTO_FOLLOWUP",
                delivery_status=delivery["status"],
                provider_message_id=delivery.get("message_id"),
            ))
            task.status = "SENT" if delivery["status"] != "FAILED" else "FAILED"
            task.attempt_number += 1
            task.last_attempt_at = now
            patient.last_contact = now
            patient.contact_attempts = (patient.contact_attempts or 0) + 1
            if patient.follow_up_status in (PatientStatus.DUE.value, PatientStatus.OVERDUE.value):
                patient.follow_up_status = PatientStatus.CONTACTED.value
            changed.append(patient.id)
        await db.commit()
    for patient_id in changed:
        await manager.broadcast({"type": "AUTO_FOLLOWUP_SENT", "patient_id": patient_id}, patient_id=patient_id)
