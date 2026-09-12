from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List
import json
from datetime import date, datetime, timedelta

from .. import models, schemas
from ..database import get_db
from .schedule import generate_slots

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/psychologist/{psychologist_id}/services")
def public_get_services(psychologist_id: int, db: DBSession = Depends(get_db)):
    return db.query(models.Service).filter(
        models.Service.psychologist_id == psychologist_id,
        models.Service.is_available == True,
    ).all()


@router.get("/psychologist/{psychologist_id}/slots")
def public_get_slots(psychologist_id: int, date: date, db: DBSession = Depends(get_db)):
    schedule = db.query(models.Schedule).filter(
        models.Schedule.psychologist_id == psychologist_id,
        models.Schedule.is_active == True,
    ).first()
    if not schedule:
        return {"slots": []}

    exception = db.query(models.ScheduleException).filter(
        models.ScheduleException.schedule_id == schedule.id,
        models.ScheduleException.date == date,
    ).first()
    if exception:
        return {"slots": [], "reason": exception.reason}

    booked = db.query(models.Booking).filter(
        models.Booking.psychologist_id == psychologist_id,
        models.Booking.date == date,
        models.Booking.status != "cancelled",
    ).all()
    booked_times = [b.time for b in booked]
    slots = generate_slots(schedule, date, booked_times)
    return {"slots": slots}


@router.post("/clients/register")
def public_register_client(data: schemas.PublicClientRegister, db: DBSession = Depends(get_db)):
    existing = db.query(models.Client).filter(
        models.Client.telegram_id == data.telegram_id
    ).first()
    if existing:
        return existing

    psychologist = db.query(models.Psychologist).first()
    if not psychologist:
        raise HTTPException(status_code=404, detail="Психолог не найден")

    client = models.Client(
        psychologist_id=psychologist.id,
        telegram_id=data.telegram_id,
        name=data.name,
        phone=data.phone,
        email=data.email,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/clients/{telegram_id}")
def public_get_client(telegram_id: int, db: DBSession = Depends(get_db)):
    client = db.query(models.Client).filter(
        models.Client.telegram_id == telegram_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.get("/clients/{telegram_id}/bookings")
def public_get_bookings(telegram_id: int, db: DBSession = Depends(get_db)):
    client = db.query(models.Client).filter(
        models.Client.telegram_id == telegram_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return db.query(models.Booking).filter(
        models.Booking.client_id == client.id
    ).order_by(models.Booking.date.desc()).all()


@router.post("/bookings")
def public_create_booking(data: schemas.PublicBookingCreate, db: DBSession = Depends(get_db)):
    client = db.query(models.Client).filter(
        models.Client.telegram_id == data.telegram_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    booking = models.Booking(
        psychologist_id=data.psychologist_id,
        client_id=client.id,
        service_id=data.service_id,
        date=data.date,
        time=data.time,
        client_comment=data.client_comment,
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/bookings/{booking_id}/cancel")
def public_cancel_booking(booking_id: int, db: DBSession = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    booking.status = "cancelled"
    db.commit()
    return {"ok": True}