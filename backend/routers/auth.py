from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.PsychologistOut)
def register(data: schemas.PsychologistRegister, db: DBSession = Depends(get_db)):
    existing = db.query(models.Psychologist).filter(
        models.Psychologist.email == data.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Психолог с таким email уже зарегистрирован",
        )
    psychologist = models.Psychologist(
        email=data.email,
        password_hash=auth.hash_password(data.password),
        name=data.name,
    )
    db.add(psychologist)
    db.commit()
    db.refresh(psychologist)
    return psychologist


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DBSession = Depends(get_db)
):
    psychologist = db.query(models.Psychologist).filter(
        models.Psychologist.email == form_data.username
    ).first()
    if not psychologist or not auth.verify_password(form_data.password, psychologist.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    token = auth.create_access_token({"sub": str(psychologist.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.PsychologistOut)
def get_me(current: models.Psychologist = Depends(auth.get_current_psychologist)):
    return current