from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os

# Database URL
DATABASE_URL = "sqlite:///./sfao.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Database Models
class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source = Column(String, nullable=False)
    text = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    score = Column(Float, default=0.0)
    category = Column(String, nullable=False)
    urgency = Column(String, default="Low")
    status = Column(String, default="New")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    timezone = Column(String, default="Africa/Lagos")
    refresh_interval = Column(Integer, default=10)
    notifications_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
    ensure_user_settings_schema()

def ensure_user_settings_schema():
    """Backfill user_settings columns for existing SQLite databases."""
    with engine.connect() as connection:
        table_exists = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'"
        ).fetchone()

        if not table_exists:
            return

        rows = connection.exec_driver_sql("PRAGMA table_info(user_settings)").fetchall()
        columns = {row[1] for row in rows}

        if "name" not in columns:
            connection.exec_driver_sql("ALTER TABLE user_settings ADD COLUMN name VARCHAR")
        if "timezone" not in columns:
            connection.exec_driver_sql("ALTER TABLE user_settings ADD COLUMN timezone VARCHAR DEFAULT 'Africa/Lagos'")
        if "refresh_interval" not in columns:
            connection.exec_driver_sql("ALTER TABLE user_settings ADD COLUMN refresh_interval INTEGER DEFAULT 10")
        if "notifications_enabled" not in columns:
            connection.exec_driver_sql("ALTER TABLE user_settings ADD COLUMN notifications_enabled BOOLEAN DEFAULT 1")
        if "updated_at" not in columns:
            connection.exec_driver_sql("ALTER TABLE user_settings ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")

        connection.commit()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    print("[DATABASE] Tables created successfully!")