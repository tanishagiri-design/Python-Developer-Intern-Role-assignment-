import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Default to SQLite for local development
# Check if DATABASE_URL is set and valid
raw_db_url = os.getenv("DATABASE_URL", "").strip()

# Use SQLite if no valid DATABASE_URL is set or if it contains invalid "host" placeholder
if not raw_db_url or "host" in raw_db_url.lower() or "localhost" not in raw_db_url:
    DATABASE_URL = "sqlite:///./skillbridge.db"
    print(f"Using SQLite database: {DATABASE_URL}")
else:
    DATABASE_URL = raw_db_url
    # Handle Neon/Railway postgres:// vs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print(f"Using PostgreSQL database: {DATABASE_URL}")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
