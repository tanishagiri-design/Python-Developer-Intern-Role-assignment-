from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound
from src.database import engine, Base
from src.routers import auth_router, batch_router, session_router, attendance_router
from src.routers import institution_router, programme_router, monitoring_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkillBridge Attendance API",
    description="Backend API for the SkillBridge state-level skilling programme attendance system",
    version="1.0.0",
)

# Custom error handlers
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation failed"},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Database integrity error", "message": str(exc.orig)},
    )


# Include routers
app.include_router(auth_router.router)
app.include_router(batch_router.router)
app.include_router(session_router.router)
app.include_router(attendance_router.router)
app.include_router(institution_router.router)
app.include_router(programme_router.router)
app.include_router(monitoring_router.router)


@app.get("/")
def root():
    return {
        "message": "SkillBridge Attendance API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
