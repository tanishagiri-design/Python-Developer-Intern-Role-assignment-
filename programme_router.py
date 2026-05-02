from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas
from src.auth import require_roles

router = APIRouter(prefix="/programme", tags=["programme"])


@router.get("/summary", response_model=schemas.ProgrammeSummary)
def programme_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.programme_manager)),
):
    total_institutions = db.query(models.Institution).count()
    total_batches = db.query(models.Batch).count()
    total_sessions = db.query(models.Session).count()

    all_records = db.query(models.Attendance).all()
    present = sum(1 for r in all_records if r.status == models.AttendanceStatus.present)
    absent = sum(1 for r in all_records if r.status == models.AttendanceStatus.absent)
    late = sum(1 for r in all_records if r.status == models.AttendanceStatus.late)

    return {
        "total_institutions": total_institutions,
        "total_batches": total_batches,
        "total_sessions": total_sessions,
        "total_attendance_records": len(all_records),
        "present": present,
        "absent": absent,
        "late": late,
    }
