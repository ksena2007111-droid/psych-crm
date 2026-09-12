from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Text
)
from sqlalchemy.orm import relationship
from .database import Base


class Psychologist(Base):
    __tablename__ = "psychologists"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    about = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clients = relationship("Client", back_populates="psychologist")
    services = relationship("Service", back_populates="psychologist")
    schedules = relationship("Schedule", back_populates="psychologist")
    bookings = relationship("Booking", back_populates="psychologist")
    sessions = relationship("Session", back_populates="psychologist")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    psychologist_id = Column(Integer, ForeignKey("psychologists.id"), nullable=False)
    telegram_id = Column(Integer, unique=True, nullable=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    status = Column(String, default="active")
    work_plan = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    psychologist = relationship("Psychologist", back_populates="clients")
    bookings = relationship("Booking", back_populates="client")
    sessions = relationship("Session", back_populates="client")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    psychologist_id = Column(Integer, ForeignKey("psychologists.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    format = Column(String, default="online")
    is_available = Column(Boolean, default=True)

    psychologist = relationship("Psychologist", back_populates="services")
    bookings = relationship("Booking", back_populates="service")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    psychologist_id = Column(Integer, ForeignKey("psychologists.id"), nullable=False)
    name = Column(String, nullable=False)
    work_days = Column(String, nullable=False)  # JSON-строка: '["mon","tue"]'
    start_time = Column(String, nullable=False)  # "09:00"
    end_time = Column(String, nullable=False)    # "18:00"
    slot_duration_minutes = Column(Integer, default=60)
    break_start = Column(String, nullable=True)
    break_end = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)

    psychologist = relationship("Psychologist", back_populates="schedules")
    exceptions = relationship("ScheduleException", back_populates="schedule")


class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)

    schedule = relationship("Schedule", back_populates="exceptions")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    psychologist_id = Column(Integer, ForeignKey("psychologists.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String, nullable=False)  # "10:00"
    status = Column(String, default="pending")  # pending / confirmed / cancelled
    client_comment = Column(Text, nullable=True)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    psychologist = relationship("Psychologist", back_populates="bookings")
    client = relationship("Client", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    session = relationship("Session", back_populates="booking", uselist=False)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    psychologist_id = Column(Integer, ForeignKey("psychologists.id"), nullable=False)
    date = Column(Date, nullable=False)
    request = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    reflection = Column(Text, nullable=True)
    homework = Column(Text, nullable=True)
    status = Column(String, default="planned")  # planned / done / cancelled
    ai_summary = Column(Text, nullable=True)
    ai_recommendations = Column(Text, nullable=True)
    ai_generated_at = Column(DateTime, nullable=True)

    booking = relationship("Booking", back_populates="session")
    client = relationship("Client", back_populates="sessions")
    psychologist = relationship("Psychologist", back_populates="sessions") 