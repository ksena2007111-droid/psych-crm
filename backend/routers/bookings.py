from datetime import date
from typing import List, Optional
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession
from dotenv import load_dotenv

from .. import models, schemas, auth
from ..database import get_db

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

router = APIRouter(prefix="/bookings", tags=["bookings"])


class PaidUpdate(BaseModel):
    is_paid: bool


async def notify_client(telegram_id: int, text: str):
    if not telegram_id or not TELEGRAM_TOKEN:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": telegram_id, "text": text}
            )
    except Exception:
        pass  # не блокируем основной запрос если Telegram недоступен


@router.get("", response_model=List[schemas.BookingOut])
def get_bookings(
    date: Optional[date] = None,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    query = db.query(models.Booking).filter(
        models.Booking.psychologist_id == current.id
    )
    if date:
        query = query.filter(models.Booking.date == date)
    return query.order_by(models.Booking.date, models.Booking.time).all()


@router.post("", response_model=schemas.BookingOut)
def create_booking(
    data: schemas.BookingCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    booking = models.Booking(
        **data.model_dump(),
        psychologist_id=current.id,
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/{booking_id}/confirm", response_model=schemas.BookingOut)
async def confirm_booking(
    booking_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.psychologist_id == current.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    booking.status = "confirmed"
    db.commit()
    db.refresh(booking)

    # Уведомляем клиента
    client = db.query(models.Client).filter(
        models.Client.id == booking.client_id
    ).first()
    if client and client.telegram_id:
        await notify_client(
            client.telegram_id,
            f"✅ Ваша запись подтверждена!\n"
            f"📅 Дата: {booking.date}\n"
            f"🕐 Время: {booking.time}\n"
            f"До встречи! 😊"
        )

    return booking


@router.patch("/{booking_id}/cancel", response_model=schemas.BookingOut)
async def cancel_booking(
    booking_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.psychologist_id == current.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)

    # Уведомляем клиента
    client = db.query(models.Client).filter(
        models.Client.id == booking.client_id
    ).first()
    if client and client.telegram_id:
        await notify_client(
            client.telegram_id,
            f"❌ К сожалению, ваша запись на {booking.date} в {booking.time} отменена.\n"
            f"Вы можете записаться на другое время — нажмите 📅 Записаться."
        )

    return booking


@router.patch("/{booking_id}/paid", response_model=schemas.BookingOut)
def update_paid(
    booking_id: int,
    data: PaidUpdate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.psychologist_id == current.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    booking.is_paid = data.is_paid
    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}")
def delete_booking(
    booking_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.psychologist_id == current.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    db.delete(booking)
    db.commit()
    return {"ok": True}