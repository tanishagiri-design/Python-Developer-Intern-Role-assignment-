from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas
from src.auth import (
    hash_password, verify_password, create_access_token,
    create_monitoring_token, get_current_user, MONITORING_API_KEY
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.TokenResponse, status_code=201)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=422, detail="Email already registered")

    if payload.institution_id:
        inst = db.query(models.Institution).filter(
            models.Institution.id == payload.institution_id
        ).first()
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        institution_id=payload.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token}


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token}


@router.post("/monitoring-token", response_model=schemas.TokenResponse)
def get_monitoring_token(
    payload: schemas.MonitoringTokenRequest,
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != models.UserRole.monitoring_officer:
        raise HTTPException(status_code=403, detail="Only monitoring officers can use this endpoint")

    if payload.key != MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = create_monitoring_token(current_user.id)
    return {"access_token": token}
