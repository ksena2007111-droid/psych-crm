import json
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/schedule", tags=["schedule"])

DAY_MAP = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def get_active_schedule(psychologist_id: int, db: DBSession):
    return db.query(models.Schedule).filter(
        models.Schedule.psychologist_id == psychologist_id,
        models.Schedule.is_active == True,
    ).first()


def generate_slots(schedule: models.Schedule, target_date: date, booked_times: list):
    from datetime import datetime as dt
    work_days = json.loads(schedule.work_days)
    weekday = target_date.weekday()
    day_names = {v: k for k, v in DAY_MAP.items()}
    if day_names[weekday] not in work_days:
        return []

    slots = []
    start = datetime.strptime(schedule.start_time, "%H:%M")
    end = datetime.strptime(schedule.end_time, "%H:%M")
    break_start = datetime.strptime(schedule.break_start, "%H:%M") if schedule.break_start else None
    break_end = datetime.strptime(schedule.break_end, "%H:%M") if schedule.break_end else None
    duration = timedelta(minutes=schedule.slot_duration_minutes)

    now = dt.now()
    is_today = (target_date == now.date())

    current = start
    while current + duration <= end:
        slot_end = current + duration
        in_break = break_start and break_end and current < break_end and slot_end > break_start
        time_str = current.strftime("%H:%M")

        # Пропускаем слоты в прошлом если это сегодня
        if is_today:
            slot_dt = dt.combine(now.date(), current.time())
            if slot_dt <= now:
                current += duration
                continue

        if not in_break and time_str not in booked_times:
            slots.append(time_str)
        current += duration

    return slots

    slots = []
    start = datetime.strptime(schedule.start_time, "%H:%M")
    end = datetime.strptime(schedule.end_time, "%H:%M")
    break_start = datetime.strptime(schedule.break_start, "%H:%M") if schedule.break_start else None
    break_end = datetime.strptime(schedule.break_end, "%H:%M") if schedule.break_end else None
    duration = timedelta(minutes=schedule.slot_duration_minutes)

    current = start
    while current + duration <= end:
        slot_end = current + duration
        in_break = break_start and break_end and current < break_end and slot_end > break_start
        time_str = current.strftime("%H:%M")
        if not in_break and time_str not in booked_times:
            slots.append(time_str)
        current += duration

    return slots


@router.get("", response_model=List[schemas.ScheduleOut])
def get_schedules(
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    schedules = db.query(models.Schedule).filter(
        models.Schedule.psychologist_id == current.id
    ).all()
    result = []
    for s in schedules:
        d = schemas.ScheduleOut(
            id=s.id,
            name=s.name,
            work_days=json.loads(s.work_days),
            start_time=s.start_time,
            end_time=s.end_time,
            slot_duration_minutes=s.slot_duration_minutes,
            break_start=s.break_start,
            break_end=s.break_end,
            is_active=s.is_active,
        )
        result.append(d)
    return result


@router.post("", response_model=schemas.ScheduleOut)
def create_schedule(
    data: schemas.ScheduleCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    schedule = models.Schedule(
        psychologist_id=current.id,
        name=data.name,
        work_days=json.dumps(data.work_days),
        start_time=data.start_time,
        end_time=data.end_time,
        slot_duration_minutes=data.slot_duration_minutes,
        break_start=data.break_start,
        break_end=data.break_end,
        is_active=False,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    schedule.work_days = json.loads(schedule.work_days)
    return schedule


@router.put("/{schedule_id}", response_model=schemas.ScheduleOut)
def update_schedule(
    schedule_id: int,
    data: schemas.ScheduleCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    schedule = db.query(models.Schedule).filter(
        models.Schedule.id == schedule_id,
        models.Schedule.psychologist_id == current.id,
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    schedule.name = data.name
    schedule.work_days = json.dumps(data.work_days)
    schedule.start_time = data.start_time
    schedule.end_time = data.end_time
    schedule.slot_duration_minutes = data.slot_duration_minutes
    schedule.break_start = data.break_start
    schedule.break_end = data.break_end
    db.commit()
    db.refresh(schedule)
    schedule.work_days = json.loads(schedule.work_days)
    return schedule


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    schedule = db.query(models.Schedule).filter(
        models.Schedule.id == schedule_id,
        models.Schedule.psychologist_id == current.id,
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    db.delete(schedule)
    db.commit()
    return {"ok": True}


@router.patch("/{schedule_id}/activate")
def activate_schedule(
    schedule_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    db.query(models.Schedule).filter(
        models.Schedule.psychologist_id == current.id
    ).update({"is_active": False})
    schedule = db.query(models.Schedule).filter(
        models.Schedule.id == schedule_id,
        models.Schedule.psychologist_id == current.id,
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    schedule.is_active = True
    db.commit()
    return {"ok": True, "active_schedule_id": schedule_id}


@router.post("/{schedule_id}/exceptions")
def add_exception(
    schedule_id: int,
    data: schemas.ScheduleExceptionCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    schedule = db.query(models.Schedule).filter(
        models.Schedule.id == schedule_id,
        models.Schedule.psychologist_id == current.id,
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    exc = models.ScheduleException(
        schedule_id=schedule_id,
        date=data.date,
        reason=data.reason,
    )
    db.add(exc)
    db.commit()
    return {"ok": True}


@router.delete("/exceptions/{exception_id}")
def delete_exception(
    exception_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    exc = db.query(models.ScheduleException).filter(
        models.ScheduleException.id == exception_id
    ).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Исключение не найдено")
    db.delete(exc)
    db.commit()
    return {"ok": True}


@router.get("/slots")
def get_slots(
    date: date,
    psychologist_id: int,
    db: DBSession = Depends(get_db),
):
    schedule = get_active_schedule(psychologist_id, db)
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