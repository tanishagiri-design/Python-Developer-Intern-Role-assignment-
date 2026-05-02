import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas
from src.auth import require_roles, get_current_user

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=schemas.BatchResponse, status_code=201)
def create_batch(
    payload: schemas.BatchCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles(models.UserRole.trainer, models.UserRole.institution)
    ),
):
    inst = db.query(models.Institution).filter(
        models.Institution.id == payload.institution_id
    ).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch = models.Batch(name=payload.name, institution_id=payload.institution_id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.post("/{batch_id}/invite", response_model=schemas.InviteResponse)
def create_invite(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.trainer)),
):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invite = models.BatchInvite(
        batch_id=batch_id,
        token=token,
        created_by=current_user.id,
        expires_at=expires_at,
        used=False,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return {"invite_token": token, "expires_at": expires_at}


@router.post("/join", status_code=200)
def join_batch(
    payload: schemas.JoinBatchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.student)),
):
    invite = db.query(models.BatchInvite).filter(
        models.BatchInvite.token == payload.token
    ).first()

    if not invite:
        raise HTTPException(status_code=404, detail="Invite token not found")
    if invite.used:
        raise HTTPException(status_code=422, detail="Invite token already used")
    if invite.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Invite token expired")

    existing = db.query(models.BatchStudent).filter(
        models.BatchStudent.batch_id == invite.batch_id,
        models.BatchStudent.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=422, detail="Already enrolled in this batch")

    link = models.BatchStudent(batch_id=invite.batch_id, student_id=current_user.id)
    db.add(link)
    invite.used = True
    db.commit()
    return {"message": "Successfully joined batch", "batch_id": invite.batch_id}


@router.get("/{batch_id}/summary", response_model=schemas.BatchSummary)
def batch_summary(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.institution)),
):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    sessions = db.query(models.Session).filter(models.Session.batch_id == batch_id).all()
    session_ids = [s.id for s in sessions]

    students = db.query(models.BatchStudent).filter(
        models.BatchStudent.batch_id == batch_id
    ).count()

    records = db.query(models.Attendance).filter(
        models.Attendance.session_id.in_(session_ids)
    ).all() if session_ids else []

    present = sum(1 for r in records if r.status == models.AttendanceStatus.present)
    absent = sum(1 for r in records if r.status == models.AttendanceStatus.absent)
    late = sum(1 for r in records if r.status == models.AttendanceStatus.late)

    return {
        "batch_id": batch_id,
        "batch_name": batch.name,
        "total_sessions": len(sessions),
        "total_students": students,
        "overall_present": present,
        "overall_absent": absent,
        "overall_late": late,
    }
