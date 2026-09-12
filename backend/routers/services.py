from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=List[schemas.ServiceOut])
def get_services(
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    return db.query(models.Service).filter(
        models.Service.psychologist_id == current.id
    ).all()


@router.post("", response_model=schemas.ServiceOut)
def create_service(
    data: schemas.ServiceCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    service = models.Service(**data.model_dump(), psychologist_id=current.id)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/{service_id}", response_model=schemas.ServiceOut)
def update_service(
    service_id: int,
    data: schemas.ServiceCreate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    service = db.query(models.Service).filter(
        models.Service.id == service_id,
        models.Service.psychologist_id == current.id,
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    for field, value in data.model_dump().items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    service = db.query(models.Service).filter(
        models.Service.id == service_id,
        models.Service.psychologist_id == current.id,
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    db.delete(service)
    db.commit()
    return {"ok": True}


@router.patch("/{service_id}/toggle", response_model=schemas.ServiceOut)
def toggle_service(
    service_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    service = db.query(models.Service).filter(
        models.Service.id == service_id,
        models.Service.psychologist_id == current.id,
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    service.is_available = not service.is_available
    db.commit()
    db.refresh(service)
    return service