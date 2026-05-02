from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas
from src.auth import get_monitoring_user
from typing import List

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/attendance", response_model=List[schemas.MonitoringAttendanceRecord])
def monitoring_attendance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_monitoring_user),
):
    records = (
        db.query(models.Attendance, models.User, models.Session)
        .join(models.User, models.Attendance.student_id == models.User.id)
        .join(models.Session, models.Attendance.session_id == models.Session.id)
        .all()
    )

    result = []
    for att, user, session in records:
        result.append({
            "attendance_id": att.id,
            "session_id": session.id,
            "session_title": session.title,
            "student_id": user.id,
            "student_name": user.name,
            "institution_id": user.institution_id,
            "batch_id": session.batch_id,
            "status": att.status.value,
            "marked_at": att.marked_at,
        })
    return result


# Return 405 for any non-GET method on /monitoring/attendance
@router.post("/attendance")
@router.put("/attendance")
@router.delete("/attendance")
@router.patch("/attendance")
async def monitoring_attendance_method_not_allowed(request: Request):
    return JSONResponse(
        status_code=405,
        content={"detail": "Method Not Allowed. This endpoint is read-only."},
    )
