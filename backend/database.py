import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Depending on testing vs production
env = os.environ.get("ENV", "development")
if env == "testing":
    SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL") or settings.DATABASE_URL or "sqlite:///./test.db"

# Render provides postgres:// which SQLAlchemy 2.0+ requires as postgresql+psycopg:// or postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
