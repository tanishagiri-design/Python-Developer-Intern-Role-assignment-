"""
Seed script: creates 2 institutions, 4 trainers, 15 students, 1 PM, 1 MO,
3 batches, 8 sessions, and attendance records.
Run with: python seed.py
"""
import os
import sys
from datetime import date, time, datetime, timedelta, timezone
import secrets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.database import engine, SessionLocal, Base
from src import models
from src.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def run():
    print("Seeding database...")

    # Clear existing data 
    db.query(models.Attendance).delete()
    db.query(models.BatchInvite).delete()
    db.query(models.BatchStudent).delete()
    db.query(models.BatchTrainer).delete()
    db.query(models.Session).delete()
    db.query(models.Batch).delete()
    db.query(models.User).delete()
    db.query(models.Institution).delete()
    db.commit()

    # 2 Institutions
    inst1 = models.Institution(name="Sunrise Vocational Institute")
    inst2 = models.Institution(name="TechSkills Academy")
    db.add_all([inst1, inst2])
    db.commit()
    db.refresh(inst1)
    db.refresh(inst2)

    # 4 Trainers (2 per institution)
    trainers = []
    trainer_data = [
        ("Rajan Mehta", "rajan@example.com", inst1.id),
        ("Priya Nair", "priya@example.com", inst1.id),
        ("Suresh Kumar", "suresh@example.com", inst2.id),
        ("Anita Desai", "anita@example.com", inst2.id),
    ]
    for name, email, inst_id in trainer_data:
        t = models.User(
            name=name, email=email,
            hashed_password=hash_password("Trainer@123"),
            role=models.UserRole.trainer,
            institution_id=inst_id,
        )
        db.add(t)
        trainers.append(t)
    db.commit()
    for t in trainers:
        db.refresh(t)

    # 15 Students
    students = []
    student_names = [
        "Aarav Shah", "Bhoomi Patel", "Chirag Rao", "Divya Singh",
        "Eshan Joshi", "Fatima Khan", "Ganesh Verma", "Hina Malik",
        "Ishaan Gupta", "Jaya Sharma", "Kiran Bose", "Laila Ansari",
        "Manish Tiwari", "Nisha Pandey", "Om Prakash",
    ]
    for i, name in enumerate(student_names):
        email = f"student{i+1}@example.com"
        s = models.User(
            name=name, email=email,
            hashed_password=hash_password("Student@123"),
            role=models.UserRole.student,
        )
        db.add(s)
        students.append(s)
    db.commit()
    for s in students:
        db.refresh(s)

    # Programme Manager
    pm = models.User(
        name="Vijay Kulkarni", email="pm@example.com",
        hashed_password=hash_password("Manager@123"),
        role=models.UserRole.programme_manager,
    )
    db.add(pm)

    # Monitoring Officer
    mo = models.User(
        name="Rekha Iyer", email="monitor@example.com",
        hashed_password=hash_password("Monitor@123"),
        role=models.UserRole.monitoring_officer,
    )
    db.add(mo)

    # Institution users
    inst_user1 = models.User(
        name="Deepak Patil", email="institution1@example.com",
        hashed_password=hash_password("Inst@1234"),
        role=models.UserRole.institution,
        institution_id=inst1.id,
    )
    inst_user2 = models.User(
        name="Sneha Jain", email="institution2@example.com",
        hashed_password=hash_password("Inst@1234"),
        role=models.UserRole.institution,
        institution_id=inst2.id,
    )
    db.add_all([inst_user1, inst_user2])
    db.commit()

    # 3 Batches
    batch1 = models.Batch(name="Web Dev Batch A", institution_id=inst1.id)
    batch2 = models.Batch(name="Data Science Batch B", institution_id=inst1.id)
    batch3 = models.Batch(name="Cloud Computing Batch C", institution_id=inst2.id)
    db.add_all([batch1, batch2, batch3])
    db.commit()
    db.refresh(batch1)
    db.refresh(batch2)
    db.refresh(batch3)

    # Assign trainers to batches
    bt_links = [
        models.BatchTrainer(batch_id=batch1.id, trainer_id=trainers[0].id),
        models.BatchTrainer(batch_id=batch1.id, trainer_id=trainers[1].id),
        models.BatchTrainer(batch_id=batch2.id, trainer_id=trainers[1].id),
        models.BatchTrainer(batch_id=batch3.id, trainer_id=trainers[2].id),
        models.BatchTrainer(batch_id=batch3.id, trainer_id=trainers[3].id),
    ]
    db.add_all(bt_links)
    db.commit()

    # Assign students to batches (5 per batch)
    bs_links = []
    for i, student in enumerate(students[:5]):
        bs_links.append(models.BatchStudent(batch_id=batch1.id, student_id=student.id))
    for i, student in enumerate(students[5:10]):
        bs_links.append(models.BatchStudent(batch_id=batch2.id, student_id=student.id))
    for i, student in enumerate(students[10:15]):
        bs_links.append(models.BatchStudent(batch_id=batch3.id, student_id=student.id))
    db.add_all(bs_links)
    db.commit()

    # 8 Sessions
    base_date = date.today() - timedelta(days=14)
    sessions_data = [
        (batch1.id, trainers[0].id, "HTML & CSS Basics", base_date, time(9, 0), time(11, 0)),
        (batch1.id, trainers[0].id, "JavaScript Intro", base_date + timedelta(days=2), time(9, 0), time(11, 0)),
        (batch1.id, trainers[1].id, "React Fundamentals", base_date + timedelta(days=4), time(9, 0), time(11, 0)),
        (batch2.id, trainers[1].id, "Python for Data Science", base_date, time(14, 0), time(16, 0)),
        (batch2.id, trainers[1].id, "Pandas & NumPy", base_date + timedelta(days=3), time(14, 0), time(16, 0)),
        (batch3.id, trainers[2].id, "AWS Fundamentals", base_date + timedelta(days=1), time(10, 0), time(12, 0)),
        (batch3.id, trainers[2].id, "Docker & Containers", base_date + timedelta(days=3), time(10, 0), time(12, 0)),
        (batch3.id, trainers[3].id, "Kubernetes Basics", base_date + timedelta(days=5), time(10, 0), time(12, 0)),
    ]

    sessions = []
    for batch_id, trainer_id, title, sess_date, start, end in sessions_data:
        s = models.Session(
            batch_id=batch_id, trainer_id=trainer_id,
            title=title, date=sess_date, start_time=start, end_time=end,
        )
        db.add(s)
        sessions.append(s)
    db.commit()
    for s in sessions:
        db.refresh(s)

    # Attendance records
    # batch1 students for sessions 0,1,2
    statuses = [
        models.AttendanceStatus.present,
        models.AttendanceStatus.present,
        models.AttendanceStatus.late,
        models.AttendanceStatus.absent,
        models.AttendanceStatus.present,
    ]
    for i, student in enumerate(students[:5]):
        for sess in sessions[:3]:
            att = models.Attendance(
                session_id=sess.id, student_id=student.id,
                status=statuses[i % len(statuses)],
            )
            db.add(att)

    # batch2 students for sessions 3,4
    for i, student in enumerate(students[5:10]):
        for sess in sessions[3:5]:
            att = models.Attendance(
                session_id=sess.id, student_id=student.id,
                status=statuses[(i + 1) % len(statuses)],
            )
            db.add(att)

    # batch3 students for sessions 5,6,7
    for i, student in enumerate(students[10:15]):
        for sess in sessions[5:8]:
            att = models.Attendance(
                session_id=sess.id, student_id=student.id,
                status=statuses[(i + 2) % len(statuses)],
            )
            db.add(att)

    db.commit()
    print(" Seeding complete!")
    print("\n=== Test Accounts ===")
    print("Role              | Email                   | Password")
    print("-" * 60)
    print("student           | student1@example.com    | Student@123")
    print("trainer           | rajan@example.com       | Trainer@123")
    print("institution       | institution1@example.com| Inst@1234")
    print("programme_manager | pm@example.com          | Manager@123")
    print("monitoring_officer| monitor@example.com     | Monitor@123")


if __name__ == "__main__":
    run()
    db.close()
