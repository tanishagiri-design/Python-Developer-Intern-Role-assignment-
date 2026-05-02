import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use a test SQLite database
TEST_DB_URL = "sqlite:///./test_skillbridge.db"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"
os.environ["MONITORING_API_KEY"] = "skillbridge-monitoring-key-2024"

from src.database import Base, get_db
from src.main import app

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def seeded_db():
    """Seed the test database with baseline data."""
    from src import models
    from src.auth import hash_password

    db = TestingSessionLocal()

    # Clean up
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()

    # Institution
    inst = models.Institution(name="Test Institute")
    db.add(inst)
    db.commit()
    db.refresh(inst)

    # Users
    trainer = models.User(
        name="Test Trainer", email="testtrainer@example.com",
        hashed_password=hash_password("Trainer@123"),
        role=models.UserRole.trainer, institution_id=inst.id,
    )
    student = models.User(
        name="Test Student", email="teststudent@example.com",
        hashed_password=hash_password("Student@123"),
        role=models.UserRole.student,
    )
    mo = models.User(
        name="Test Monitor", email="testmonitor@example.com",
        hashed_password=hash_password("Monitor@123"),
        role=models.UserRole.monitoring_officer,
    )
    db.add_all([trainer, student, mo])
    db.commit()
    db.refresh(trainer)
    db.refresh(student)
    db.refresh(mo)

    # Batch
    batch = models.Batch(name="Test Batch", institution_id=inst.id)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Enroll student
    bs = models.BatchStudent(batch_id=batch.id, student_id=student.id)
    db.add(bs)
    db.commit()

    # Session
    from datetime import date, time, timedelta
    sess = models.Session(
        batch_id=batch.id, trainer_id=trainer.id,
        title="Test Session",
        date=date.today() - timedelta(days=1),
        start_time=time(9, 0), end_time=time(11, 0),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)

    db.close()

    return {
        "institution_id": inst.id,
        "trainer_email": "testtrainer@example.com",
        "student_email": "teststudent@example.com",
        "monitor_email": "testmonitor@example.com",
        "batch_id": batch.id,
        "session_id": sess.id,
    }
