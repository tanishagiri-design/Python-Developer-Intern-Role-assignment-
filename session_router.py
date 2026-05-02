from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from src.database import get_db
from src import models, schemas
from src.auth import require_roles

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=schemas.SessionResponse, status_code=201)
def create_session(
    payload: schemas.SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.trainer)),
):
    batch = db.query(models.Batch).filter(models.Batch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    session = models.Session(
        batch_id=payload.batch_id,
        trainer_id=current_user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/attendance", response_model=schemas.AttendanceSummary)
def session_attendance(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.trainer)),
):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = (
        db.query(models.Attendance, models.User)
        .join(models.User, models.Attendance.student_id == models.User.id)
        .filter(models.Attendance.session_id == session_id)
        .all()
    )

    attendance_list = []
    present = absent = late = 0
    for att, user in records:
        attendance_list.append({
            "student_id": user.id,
            "student_name": user.name,
            "status": att.status.value,
            "marked_at": att.marked_at,
        })
        if att.status == models.AttendanceStatus.present:
            present += 1
        elif att.status == models.AttendanceStatus.absent:
            absent += 1
        else:
            late += 1

    return {
        "session_id": session_id,
        "session_title": session.title,
        "total_students": len(records),
        "present": present,
        "absent": absent,
        "late": late,
        "records": attendance_list,
    }
