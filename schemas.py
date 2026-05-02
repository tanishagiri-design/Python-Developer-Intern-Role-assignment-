from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, time, datetime
from src.models import UserRole, AttendanceStatus


# ---- Auth ----
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    institution_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonitoringTokenRequest(BaseModel):
    key: str


# ---- Batch ----
class BatchCreate(BaseModel):
    name: str
    institution_id: int


class BatchResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InviteResponse(BaseModel):
    invite_token: str
    expires_at: datetime


class JoinBatchRequest(BaseModel):
    token: str


# ---- Session ----
class SessionCreate(BaseModel):
    title: str
    date: date
    start_time: time
    end_time: time
    batch_id: int


class SessionResponse(BaseModel):
    id: int
    batch_id: int
    trainer_id: int
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Attendance ----
class MarkAttendanceRequest(BaseModel):
    session_id: int
    status: AttendanceStatus


class AttendanceRecord(BaseModel):
    student_id: int
    student_name: str
    status: str
    marked_at: Optional[datetime]


class AttendanceSummary(BaseModel):
    session_id: int
    session_title: str
    total_students: int
    present: int
    absent: int
    late: int
    records: List[AttendanceRecord]


class BatchSummary(BaseModel):
    batch_id: int
    batch_name: str
    total_sessions: int
    total_students: int
    overall_present: int
    overall_absent: int
    overall_late: int


class InstitutionSummary(BaseModel):
    institution_id: int
    institution_name: str
    batches: List[BatchSummary]


class ProgrammeSummary(BaseModel):
    total_institutions: int
    total_batches: int
    total_sessions: int
    total_attendance_records: int
    present: int
    absent: int
    late: int


class MonitoringAttendanceRecord(BaseModel):
    attendance_id: int
    session_id: int
    session_title: str
    student_id: int
    student_name: str
    institution_id: Optional[int]
    batch_id: int
    status: str
    marked_at: Optional[datetime]
