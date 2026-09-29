from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    account_type: Literal["PATIENT", "DOCTOR", "STAFF"]
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)
    full_name: str = Field(min_length=2, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    clinic_access_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    patient_id: Optional[int] = None


class PatientBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_channel: str = "SMS"
    preferred_language: str = "en"
    treatment: Optional[str] = None
    treatment_status: Optional[str] = None
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    last_visit: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_channel: Optional[str] = None
    treatment: Optional[str] = None
    treatment_status: Optional[str] = None
    follow_up_status: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class PatientOut(PatientBase):
    id: int
    last_visit: Optional[datetime]
    follow_up_date: Optional[datetime]
    follow_up_status: str
    priority: str
    contact_attempts: int
    last_contact: Optional[datetime]
    opted_out: bool
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    patient_id: int
    date: datetime
    duration_minutes: int = 30
    treatment_type: Optional[str] = None
    notes: Optional[str] = None


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    date: datetime
    duration_minutes: int
    treatment_type: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    patient_id: int
    channel: Optional[str]
    direction: Optional[str]
    message: Optional[str]
    intent: Optional[str]
    agent_action: Optional[str]
    delivery_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EscalationOut(BaseModel):
    id: int
    patient_id: int
    type: Optional[str]
    priority: Optional[str]
    reason: Optional[str]
    patient_message: Optional[str]
    detected_intent: Optional[str]
    staff_summary: Optional[str]
    status: str
    assigned_to: Optional[int]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EscalationUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[int] = None


class AgentMessageRequest(BaseModel):
    patient_id: int
    message: str = Field(min_length=1, max_length=3000)
    channel: str = "WEB"


class AgentResponse(BaseModel):
    reply: str
    intent: str
    action: str
    escalated: bool = False
    slots: List[str] = Field(default_factory=list)


class DashboardStats(BaseModel):
    total_followups: int
    due_today: int
    overdue: int
    responded: int
    booked: int
    rescheduled: int
    escalations: int
    no_response: int
    completion_rate: float
    response_rate: float


class SlotRequest(BaseModel):
    date: str
    time_range: Optional[str] = None
