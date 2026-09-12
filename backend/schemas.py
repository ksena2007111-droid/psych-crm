from datetime import datetime, date as date_type
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ===== Psychologist / Auth =====

class PsychologistRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class PsychologistLogin(BaseModel):
    email: EmailStr
    password: str


class PsychologistOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    about: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ===== Client =====

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date_type] = None
    work_plan: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    status: Optional[str] = None
    work_plan: Optional[str] = None
    notes: Optional[str] = None


class ClientOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    status: str
    work_plan: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    telegram_id: Optional[int] = None

    class Config:
        from_attributes = True


# ===== Service =====

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int
    price: float
    format: str = "online"


class ServiceOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    duration_minutes: int
    price: float
    format: str
    is_available: bool

    class Config:
        from_attributes = True


# ===== Schedule =====

class ScheduleCreate(BaseModel):
    name: str
    work_days: List[str]  # ["mon", "tue", ...]
    start_time: str
    end_time: str
    slot_duration_minutes: int = 60
    break_start: Optional[str] = None
    break_end: Optional[str] = None


class ScheduleOut(BaseModel):
    id: int
    name: str
    work_days: List[str]
    start_time: str
    end_time: str
    slot_duration_minutes: int
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class ScheduleExceptionCreate(BaseModel):
    date: date_type
    reason: Optional[str] = None


# ===== Booking =====

class BookingCreate(BaseModel):
    client_id: int
    service_id: int
    date: date_type
    time: str
    client_comment: Optional[str] = None


class BookingOut(BaseModel):
    id: int
    client_id: int
    service_id: int
    date: date_type
    time: str
    status: str
    client_comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Session =====

class SessionCreate(BaseModel):
    date: date_type
    request: Optional[str] = None
    description: Optional[str] = None
    reflection: Optional[str] = None
    homework: Optional[str] = None
    status: str = "planned"


class SessionUpdate(BaseModel):
    date: Optional[date_type] = None
    request: Optional[str] = None
    description: Optional[str] = None
    reflection: Optional[str] = None
    homework: Optional[str] = None
    status: Optional[str] = None


class SessionOut(BaseModel):
    id: int
    client_id: int
    date: date_type
    request: Optional[str] = None
    description: Optional[str] = None
    reflection: Optional[str] = None
    homework: Optional[str] = None
    status: str
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[str] = None

    class Config:
        from_attributes = True


# ===== Public (для бота) =====

class PublicClientRegister(BaseModel):
    telegram_id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class PublicBookingCreate(BaseModel):
    telegram_id: int
    psychologist_id: int
    service_id: int
    date: date_type
    time: str
    client_comment: Optional[str] = None