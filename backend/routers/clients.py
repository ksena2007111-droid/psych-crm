from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=List[schemas.ClientOut])
def get_clients(
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    return db.query(models.Client).filter(
        models.Client.psychologist_id == current.id
    ).all()


@router.post("", response_model=schemas.ClientOut)
def create_client(
    data: schemas.ClientCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    client = models.Client(**data.model_dump(), psychologist_id=current.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(
    client_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    client = db.query(models.Client).filter(
        models.Client.id == client_id,
        models.Client.psychologist_id == current.id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int,
    data: schemas.ClientUpdate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    client = db.query(models.Client).filter(
        models.Client.id == client_id,
        models.Client.psychologist_id == current.id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    client = db.query(models.Client).filter(
        models.Client.id == client_id,
        models.Client.psychologist_id == current.id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Удаляем связанные сессии
    db.query(models.Session).filter(
        models.Session.client_id == client_id
    ).delete()

    # Удаляем связанные бронирования
    db.query(models.Booking).filter(
        models.Booking.client_id == client_id
    ).delete()

    # Удаляем самого клиента
    db.delete(client)
    db.commit()
    return {"ok": True}

@router.get("/{client_id}/sessions", response_model=List[schemas.SessionOut])
def get_client_sessions(
    client_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    client = db.query(models.Client).filter(
        models.Client.id == client_id,
        models.Client.psychologist_id == current.id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return db.query(models.Session).filter(
        models.Session.client_id == client_id
    ).order_by(models.Session.date.desc()).all()


@router.post("/{client_id}/sessions", response_model=schemas.SessionOut)
def create_session(
    client_id: int,
    data: schemas.SessionCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    client = db.query(models.Client).filter(
        models.Client.id == client_id,
        models.Client.psychologist_id == current.id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    session = models.Session(
        **data.model_dump(),
        client_id=client_id,
        psychologist_id=current.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session