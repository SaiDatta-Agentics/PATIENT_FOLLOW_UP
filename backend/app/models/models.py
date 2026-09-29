from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.db import Base
import enum


def utcnow():
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    DOCTOR = "DOCTOR"
    STAFF = "STAFF"
    PATIENT = "PATIENT"


class PatientStatus(str, enum.Enum):
    DUE = "DUE"
    CONTACTED = "CONTACTED"
    RESPONDED = "RESPONDED"
    BOOKED = "BOOKED"
    RESCHEDULED = "RESCHEDULED"
    OVERDUE = "OVERDUE"
    ESCALATED = "ESCALATED"
    NO_RESPONSE = "NO_RESPONSE"
    COMPLETED = "COMPLETED"


class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Intent(str, enum.Enum):
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    RESCHEDULE_APPOINTMENT = "RESCHEDULE_APPOINTMENT"
    CONFIRM_APPOINTMENT = "CONFIRM_APPOINTMENT"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    PAIN_OR_SYMPTOM = "PAIN_OR_SYMPTOM"
    TREATMENT_QUESTION = "TREATMENT_QUESTION"
    FEE_QUESTION = "FEE_QUESTION"
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    NOT_INTERESTED = "NOT_INTERESTED"
    REQUEST_HUMAN = "REQUEST_HUMAN"
    NO_RESPONSE = "NO_RESPONSE"
    OTHER = "OTHER"


class EscalationType(str, enum.Enum):
    CLINICAL = "CLINICAL"
    FINANCIAL = "FINANCIAL"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(20), default=Role.STAFF.value)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(30))
    email = Column(String(200))
    preferred_channel = Column(String(20), default="SMS")
    preferred_language = Column(String(10), default="en")
    last_visit = Column(DateTime)
    treatment = Column(String(300))
    treatment_status = Column(String(100))
    follow_up_date = Column(DateTime)
    follow_up_status = Column(String(30), default=PatientStatus.DUE.value)
    priority = Column(String(20), default=Priority.MEDIUM.value)
    contact_attempts = Column(Integer, default=0)
    last_contact = Column(DateTime)
    opted_out = Column(Boolean, default=False)
    notes = Column(Text)
    source = Column(String(30), default="REAL")
    created_at = Column(DateTime, default=utcnow)
    conversations = relationship("Conversation", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="patient", cascade="all, delete-orphan")
    followup_tasks = relationship("FollowUpTask", back_populates="patient", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    treatment_type = Column(String(200))
    status = Column(String(30), default="SCHEDULED")
    notes = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    patient = relationship("Patient", back_populates="appointments")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    channel = Column(String(20), default="SMS")
    direction = Column(String(10))
    message = Column(Text)
    intent = Column(String(50))
    agent_action = Column(String(100))
    delivery_status = Column(String(30), default="RECORDED")
    provider_message_id = Column(String(200), nullable=True)
    escalation_status = Column(String(30))
    created_at = Column(DateTime, default=utcnow)
    patient = relationship("Patient", back_populates="conversations")


class Escalation(Base):
    __tablename__ = "escalations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    type = Column(String(30))
    priority = Column(String(20))
    reason = Column(Text)
    patient_message = Column(Text)
    detected_intent = Column(String(50))
    staff_summary = Column(Text)
    status = Column(String(30), default="OPEN")
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    patient = relationship("Patient", back_populates="escalations")


class FollowUpTask(Base):
    __tablename__ = "followup_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    channel = Column(String(20), default="SMS")
    action = Column(String(50), default="INITIAL_FOLLOWUP")
    status = Column(String(30), default="SCHEDULED")
    attempt_number = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_attempt_at = Column(DateTime, nullable=True)
    next_attempt_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    patient = relationship("Patient", back_populates="followup_tasks")


class FollowUpConfig(Base):
    __tablename__ = "followup_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    day_offset = Column(Integer, nullable=False)
    action = Column(String(100))
    message_template = Column(Text)
    is_active = Column(Boolean, default=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(200))
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime, default=utcnow)
