from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database.db import get_db
from app.models.models import User, Patient
from app.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.core.auth import verify_password, create_access_token, get_current_user, hash_password
from app.core.config import settings
from app.services.realtime import manager

router = APIRouter(prefix="/api/auth", tags=["auth"])


def token_for(user: User) -> TokenResponse:
    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "patient_id": user.patient_id,
    })
    return TokenResponse(
        access_token=token,
        role=user.role,
        full_name=user.full_name,
        patient_id=user.patient_id,
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    username = req.username.strip().lower()
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return token_for(user)


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    username = req.username.strip().lower()
    if req.account_type in ("DOCTOR", "STAFF") and req.clinic_access_code != settings.CLINIC_ACCESS_CODE:
        raise HTTPException(status_code=403, detail="Invalid clinic access code")

    existing = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    patient_id = None
    if req.account_type == "PATIENT":
        patient = None
        if req.email:
            patient = (await db.execute(select(Patient).where(Patient.email == req.email.strip().lower()))).scalar_one_or_none()
        if not patient and req.phone:
            patient = (await db.execute(select(Patient).where(Patient.phone == req.phone.strip()))).scalar_one_or_none()
        if patient is None:
            patient = Patient(
                name=req.full_name.strip(),
                email=req.email.strip().lower() if req.email else None,
                phone=req.phone.strip() if req.phone else None,
                preferred_channel="SMS",
                treatment="Treatment plan pending clinic review",
                treatment_status="New patient account",
                follow_up_status="DUE",
                priority="MEDIUM",
                source="SELF_REGISTERED",
            )
            db.add(patient)
            await db.flush()
        patient_id = patient.id

    user = User(
        username=username,
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        role=req.account_type,
        patient_id=patient_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await manager.broadcast({"type": "ACCOUNT_CREATED", "role": user.role, "name": user.full_name}, patient_id=patient_id)
    return token_for(user)


@router.get("/me")
async def me(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db_user = await db.get(User, user["user_id"])
    if not db_user:
        raise HTTPException(404, "User not found")
    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "role": db_user.role,
        "patient_id": db_user.patient_id,
        "full_name": db_user.full_name,
    }
