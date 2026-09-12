from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}", response_model=schemas.SessionOut)
def get_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.psychologist_id == current.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session


@router.put("/{session_id}", response_model=schemas.SessionOut)
def update_session(
    session_id: int,
    data: schemas.SessionUpdate,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.psychologist_id == current.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}")
def delete_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current: models.Psychologist = Depends(auth.get_current_psychologist),
):
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.psychologist_id == current.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    db.delete(session)
    db.commit()
    return {"ok": True}