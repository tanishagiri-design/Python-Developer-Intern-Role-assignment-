# SkillBridge Attendance API

A REST API backend for the SkillBridge state-level skilling programme attendance management system. Built with FastAPI, PostgreSQL (Neon), and deployed on Railway.

---
# Option 1: Run with existing server
cd /Users/avinashgiri/Desktop/submission
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Option 2: Run with DATABASE_URL for local SQLite
cd /Users/avinashgiri/Desktop/submission
DATABASE_URL="sqlite:///./skillbridge.db" python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
 
 
## Live API

> **Base URL:** `https://YOUR-APP-NAME.railway.app`
> *(Replace this with your actual Railway/Render URL after deployment)*

**Interactive Docs:** `https://YOUR-APP-NAME.railway.app/docs`

---

## Local Setup (from scratch)

Assumes Python 3.10+ and pip are installed.

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/skillbridge-api.git
cd skillbridge-api

# 2. Create and activate virtualenv
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set your DATABASE_URL (Neon PostgreSQL or leave as SQLite for local dev)

# 5. Seed the database
python seed.py

# 6. Run the server
uvicorn src.main:app --reload

# API is now available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

For local development without PostgreSQL, the app defaults to SQLite (`skillbridge_test.db`) automatically.

---

## Test Accounts (all seeded by seed.py)

| Role               | Email                    | Password      |
|--------------------|--------------------------|---------------|
| student            | student1@example.com     | Student@123   |
| trainer            | rajan@example.com        | Trainer@123   |
| institution        | institution1@example.com | Inst@1234     |
| programme_manager  | pm@example.com           | Manager@123   |
| monitoring_officer | monitor@example.com      | Monitor@123   |

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use a separate SQLite test database and are self-contained. At least two tests (student attendance marking and monitoring token flow) hit a real test database.

---

## Sample curl Commands

Replace `BASE` with your live URL or `http://localhost:8000` for local.

### Auth

```bash
# Signup
curl -X POST $BASE/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"Pass@123","role":"student"}'

# Login (returns JWT)
curl -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student1@example.com","password":"Student@123"}'

# Save the token
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"rajan@example.com","password":"Trainer@123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Get monitoring-scoped token (monitoring officer only)
STANDARD_TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"monitor@example.com","password":"Monitor@123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

MONITORING_TOKEN=$(curl -s -X POST $BASE/auth/monitoring-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $STANDARD_TOKEN" \
  -d '{"key":"skillbridge-monitoring-key-2024"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

### Batches

```bash
# Create batch (trainer or institution)
TRAINER_TOKEN=<trainer_token>
curl -X POST $BASE/batches \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"New Batch","institution_id":1}'

# Generate invite link (trainer)
curl -X POST $BASE/batches/1/invite \
  -H "Authorization: Bearer $TRAINER_TOKEN"

# Student joins batch with token
STUDENT_TOKEN=<student_token>
curl -X POST $BASE/batches/join \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"<invite_token>"}'

# Batch summary (institution)
INST_TOKEN=<institution_token>
curl $BASE/batches/1/summary \
  -H "Authorization: Bearer $INST_TOKEN"
```

### Sessions

```bash
# Create session (trainer)
curl -X POST $BASE/sessions \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"HTML Basics","date":"2025-07-01","start_time":"09:00:00","end_time":"11:00:00","batch_id":1}'

# View session attendance (trainer)
curl $BASE/sessions/1/attendance \
  -H "Authorization: Bearer $TRAINER_TOKEN"
```

### Attendance

```bash
# Mark attendance (student)
curl -X POST $BASE/attendance/mark \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":1,"status":"present"}'
```

### Programme & Institution Summary

```bash
PM_TOKEN=<pm_token>

# Institution summary
curl $BASE/institutions/1/summary \
  -H "Authorization: Bearer $PM_TOKEN"

# Programme-wide summary
curl $BASE/programme/summary \
  -H "Authorization: Bearer $PM_TOKEN"
```

### Monitoring Officer

```bash
# Read-only monitoring attendance (requires scoped token)
curl $BASE/monitoring/attendance \
  -H "Authorization: Bearer $MONITORING_TOKEN"
```

---

## JWT Payload Structure

### Standard Token (all roles except monitoring scoped)
```json
{
  "sub": "42",
  "role": "trainer",
  "iat": 1718000000,
  "exp": 1718086400
}
```
Expiry: 24 hours (1440 minutes).

### Monitoring Scoped Token
```json
{
  "sub": "7",
  "role": "monitoring_officer",
  "token_type": "monitoring_scoped",
  "iat": 1718000000,
  "exp": 1718003600
}
```
Expiry: 1 hour. Only accepted by `GET /monitoring/attendance`. All other endpoints reject it with 401.

---

## Token Rotation / Revocation Strategy

In a real deployment:
- Store a `token_version` or `jti` (JWT ID) column on the users table.
- On logout or key rotation, increment `token_version`. Any token with an older version is rejected.
- For the monitoring API key, store it hashed in the database so it can be rotated by updating the record without redeploying.
- Use short-lived access tokens (15 min) + refresh tokens stored server-side for standard roles.

---

## One Known Security Issue

**Issue:** The `MONITORING_API_KEY` is hardcoded in `.env` and compared using a plain string equality check. This is vulnerable to timing attacks.

**Fix:** Use `hmac.compare_digest(provided_key, expected_key)` instead of `==`, and hash the stored key with bcrypt so even if the .env is leaked the raw key isn't exposed.

---

## Schema Design Decisions

### `batch_trainers` (many-to-many)
A batch can have multiple trainers (e.g., one lead, one assistant). A trainer can also teach multiple batches. The junction table `batch_trainers` avoids data duplication and supports this flexibility cleanly.

### `batch_invites`
Invite tokens are one-time-use (`used` boolean) with an expiry (`expires_at`). This prevents link sharing abuse. The token is a cryptographically random URL-safe string generated by `secrets.token_urlsafe(32)`. Each invite is tied to a specific batch, so a student can't use an invite for the wrong batch.

### Dual-token for Monitoring Officer
The Monitoring Officer gets two tokens:
1. A **standard login token** (24h) — cannot access `/monitoring/*`.
2. A **scoped monitoring token** (1h) — obtained by presenting the standard token + a secret API key. Only this scoped token works on monitoring endpoints.

This design means even if a monitoring officer's login token is stolen, it gives no access to monitoring data without the API key. The 1-hour expiry limits the blast radius if the scoped token is leaked.

### `attendance` uniqueness
A student can only mark attendance once per session. This is enforced in application logic (returning 422 if duplicate), with a future improvement being a DB-level unique constraint on `(session_id, student_id)`.

---

## Deployment Notes

### Railway (recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set DATABASE_URL=postgresql://...
railway variables set SECRET_KEY=your-secret
railway variables set MONITORING_API_KEY=skillbridge-monitoring-key-2024

# Run seed on the deployed instance
railway run python seed.py
```

### Render (alternative)
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- Add environment variables in the Render dashboard.

### Neon (PostgreSQL)
Sign up at neon.tech, create a project, copy the connection string and set it as `DATABASE_URL`.

---

## What's Working / Partial / Skipped

### Fully Working ✅
- All 5 user roles with JWT-based RBAC on every endpoint
- `POST /auth/signup`, `POST /auth/login`, `POST /auth/monitoring-token`
- `POST /batches`, `POST /batches/{id}/invite`, `POST /batches/join`
- `POST /sessions`, `POST /attendance/mark`
- `GET /sessions/{id}/attendance`
- `GET /batches/{id}/summary`
- `GET /institutions/{id}/summary`
- `GET /programme/summary`
- `GET /monitoring/attendance` (scoped token only)
- 405 on non-GET `/monitoring/attendance`
- 422 with descriptive errors for all invalid POST bodies
- 404 for missing foreign keys (batch_id, session_id, institution_id)
- 403 for student marking attendance in unenrolled session
- Seed script with 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions
- 7 pytest tests (5 required + 2 bonus), 2+ hitting real test DB
- Password hashing with bcrypt via passlib

### Partially Done ⚠️
- Deployment instructions are complete but the live URL requires you to deploy (see above). The app is fully ready to deploy with one `railway up` command.

### Skipped / Future Improvements ❌
- Refresh token rotation (currently single-token, 24h expiry)
- DB-level unique constraint on `attendance(session_id, student_id)`
- Pagination on list endpoints (monitoring/attendance could be large)
- Rate limiting on auth endpoints

---

## One Thing I'd Do Differently

I would add a DB-level unique constraint on `(session_id, student_id)` in the `attendance` table from the start. Currently, duplicate attendance is caught in application code, but a race condition (two simultaneous requests) could bypass it. A DB constraint is the only safe guarantee.

---

## Project Structure

```
/submission
├── CONTACT.txt
├── Procfile
├── railway.json
├── requirements.txt
├── runtime.txt
├── .env.example
├── seed.py
├── README.md
├── /src
│   ├── __init__.py
│   ├── main.py          # FastAPI app, router registration, error handlers
│   ├── database.py      # SQLAlchemy engine, session, Base
│   ├── models.py        # ORM models (User, Batch, Session, Attendance, etc.)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── auth.py          # JWT creation/validation, password hashing, dependencies
│   └── /routers
│       ├── auth_router.py
│       ├── batch_router.py
│       ├── session_router.py
│       ├── attendance_router.py
│       ├── institution_router.py
│       ├── programme_router.py
│       └── monitoring_router.py
└── /tests
    ├── __init__.py
    ├── conftest.py      # TestClient, test DB setup, seeded_db fixture
    └── test_api.py      # 7 pytest tests
```
