from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.database.db import init_db, async_session
from app.database.seed import seed_data
from app.models.models import User, Patient
from app.api import auth, patients, dashboard, agent, escalations, appointments, realtime
from app.services.followup import process_due_followups
from app.core.config import settings
from app.core.auth import hash_password

scheduler = AsyncIOScheduler()

DEMO_USERS = [
    ("drjones", "doctor123", "Dr. Sarah Jones", "DOCTOR", None),
    ("staff1", "staff123", "Emily Chen", "STAFF", None),
    ("john", "patient123", "John Miller", "PATIENT", "john@example.com"),
    ("maria", "patient123", "Maria Garcia", "PATIENT", "maria@example.com"),
    ("priya", "patient123", "Priya Raman", "PATIENT", "priya@example.com"),
]


async def ensure_demo_data(db):
    patient_result = await db.execute(select(Patient).limit(1))
    if patient_result.scalar_one_or_none() is None:
        users, pts, convos, escs, appts, configs, tasks = seed_data()
        db.add_all(pts)
        await db.flush()
        db.add_all(convos + escs + appts + configs + tasks)
        await db.commit()

    for username, password, full_name, role, patient_email in DEMO_USERS:
        patient_id = None
        if patient_email:
            patient = (await db.execute(select(Patient).where(Patient.email == patient_email))).scalar_one_or_none()
            patient_id = patient.id if patient else None
        user = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if user is None:
            db.add(User(username=username, hashed_password=hash_password(password), full_name=full_name, role=role, patient_id=patient_id))
        else:
            user.hashed_password = hash_password(password)
            user.full_name = full_name
            user.role = role
            user.patient_id = patient_id if role == "PATIENT" else None
    await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as db:
        if settings.DEMO_MODE:
            await ensure_demo_data(db)
    if settings.AUTO_FOLLOWUP_ENABLED:
        scheduler.add_job(process_due_followups, "interval", seconds=max(settings.FOLLOWUP_POLL_SECONDS, 10), id="followup-worker", replace_existing=True)
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, patients.router, dashboard.router, agent.router, escalations.router, appointments.router, realtime.router):
    app.include_router(r)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode": "demo+real",
        "automation": settings.AUTO_FOLLOWUP_ENABLED,
        "poll_seconds": settings.FOLLOWUP_POLL_SECONDS,
        "azure_openai_configured": bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY),
        "azure_communication_configured": bool(settings.AZURE_COMMUNICATION_CONNECTION_STRING),
    }


import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
_static = os.environ.get("STATIC_DIR", "/app/static")
if os.path.isdir(_static):
    assets = os.path.join(_static, "assets")
    if os.path.isdir(assets):
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        candidate = os.path.join(_static, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_static, "index.html"))
