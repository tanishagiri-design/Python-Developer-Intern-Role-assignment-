from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas
from src.auth import require_roles

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark", status_code=201)
def mark_attendance(
    payload: schemas.MarkAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.student)),
):
    session = db.query(models.Session).filter(models.Session.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check student is enrolled in the batch
    enrolled = db.query(models.BatchStudent).filter(
        models.BatchStudent.batch_id == session.batch_id,
        models.BatchStudent.student_id == current_user.id,
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this session's batch")

    # Check if already marked
    existing = db.query(models.Attendance).filter(
        models.Attendance.session_id == payload.session_id,
        models.Attendance.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=422, detail="Attendance already marked for this session")

    record = models.Attendance(
        session_id=payload.session_id,
        student_id=current_user.id,
        status=payload.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"message": "Attendance marked successfully", "status": record.status.value}
