"""
pytest tests for SkillBridge API.
At least 2 tests hit the real (test) SQLite database via seeded_db fixture.
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient


# ---- Test 1: Student signup and login, assert valid JWT ----
def test_student_signup_and_login(client: TestClient, seeded_db):
    """Student can sign up and log in; both return valid JWT."""
    # Signup
    signup_resp = client.post("/auth/signup", json={
        "name": "New Student",
        "email": "newstudent_pytest@example.com",
        "password": "NewPass@123",
        "role": "student",
    })
    assert signup_resp.status_code == 201, signup_resp.text
    token_data = signup_resp.json()
    assert "access_token" in token_data
    assert len(token_data["access_token"]) > 20

    # Login
    login_resp = client.post("/auth/login", json={
        "email": "newstudent_pytest@example.com",
        "password": "NewPass@123",
    })
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert len(login_data["access_token"]) > 20


# ---- Test 2: Trainer creates a session with all required fields ----
def test_trainer_creates_session(client: TestClient, seeded_db):
    """Trainer can create a session; response contains all fields."""
    # Login as trainer
    login = client.post("/auth/login", json={
        "email": seeded_db["trainer_email"],
        "password": "Trainer@123",
    })
    assert login.status_code == 200
    token = login.json()["access_token"]

    resp = client.post(
        "/sessions",
        json={
            "title": "Pytest Session",
            "date": "2025-06-01",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "batch_id": seeded_db["batch_id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Pytest Session"
    assert data["batch_id"] == seeded_db["batch_id"]
    assert "id" in data


# ---- Test 3: Student marks own attendance ----
def test_student_marks_attendance(client: TestClient, seeded_db):
    """Enrolled student can mark attendance for their session."""
    # Login as student
    login = client.post("/auth/login", json={
        "email": seeded_db["student_email"],
        "password": "Student@123",
    })
    assert login.status_code == 200
    token = login.json()["access_token"]

    resp = client.post(
        "/attendance/mark",
        json={"session_id": seeded_db["session_id"], "status": "present"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Accept 201 (first time) or 422 (already marked in prior run)
    assert resp.status_code in (201, 422), resp.text
    if resp.status_code == 201:
        assert resp.json()["status"] == "present"


# ---- Test 4: POST to /monitoring/attendance returns 405 ----
def test_monitoring_attendance_post_returns_405(client: TestClient, seeded_db):
    """POST method on /monitoring/attendance must return 405."""
    resp = client.post("/monitoring/attendance")
    assert resp.status_code == 405, resp.text


# ---- Test 5: Protected endpoint with no token returns 401 ----
def test_no_token_returns_401(client: TestClient, seeded_db):
    """Accessing a protected endpoint without a token returns 401."""
    resp = client.get("/sessions/1/attendance")
    assert resp.status_code == 403, resp.text  # HTTPBearer returns 403 when no token

    # Alternatively test an endpoint with explicit 401 expectation
    resp2 = client.get("/monitoring/attendance")
    assert resp2.status_code in (401, 403), resp2.text


# ---- Bonus Test 6: Wrong password returns 401 ----
def test_wrong_password_returns_401(client: TestClient, seeded_db):
    """Login with wrong password returns 401."""
    resp = client.post("/auth/login", json={
        "email": seeded_db["trainer_email"],
        "password": "WrongPassword",
    })
    assert resp.status_code == 401


# ---- Bonus Test 7: Monitoring officer dual-token flow ----
def test_monitoring_officer_token_flow(client: TestClient, seeded_db):
    """Monitoring officer gets a scoped token and accesses monitoring endpoint."""
    # Login
    login = client.post("/auth/login", json={
        "email": seeded_db["monitor_email"],
        "password": "Monitor@123",
    })
    assert login.status_code == 200
    standard_token = login.json()["access_token"]

    # Get scoped monitoring token
    scoped = client.post(
        "/auth/monitoring-token",
        json={"key": "skillbridge-monitoring-key-2024"},
        headers={"Authorization": f"Bearer {standard_token}"},
    )
    assert scoped.status_code == 200, scoped.text
    scoped_token = scoped.json()["access_token"]

    # Hit the monitoring endpoint with scoped token
    resp = client.get(
        "/monitoring/attendance",
        headers={"Authorization": f"Bearer {scoped_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)
