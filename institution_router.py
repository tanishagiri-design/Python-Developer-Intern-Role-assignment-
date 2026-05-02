from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas
from src.auth import require_roles

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/{institution_id}/summary", response_model=schemas.InstitutionSummary)
def institution_summary(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.programme_manager)),
):
    institution = db.query(models.Institution).filter(
        models.Institution.id == institution_id
    ).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batches = db.query(models.Batch).filter(
        models.Batch.institution_id == institution_id
    ).all()

    batch_summaries = []
    for batch in batches:
        sessions = db.query(models.Session).filter(
            models.Session.batch_id == batch.id
        ).all()
        session_ids = [s.id for s in sessions]
        students = db.query(models.BatchStudent).filter(
            models.BatchStudent.batch_id == batch.id
        ).count()
        records = db.query(models.Attendance).filter(
            models.Attendance.session_id.in_(session_ids)
        ).all() if session_ids else []

        batch_summaries.append({
            "batch_id": batch.id,
            "batch_name": batch.name,
            "total_sessions": len(sessions),
            "total_students": students,
            "overall_present": sum(1 for r in records if r.status == models.AttendanceStatus.present),
            "overall_absent": sum(1 for r in records if r.status == models.AttendanceStatus.absent),
            "overall_late": sum(1 for r in records if r.status == models.AttendanceStatus.late),
        })

    return {
        "institution_id": institution_id,
        "institution_name": institution.name,
        "batches": batch_summaries,
    }
