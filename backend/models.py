from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, create_engine
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
    department_tag = Column(String, nullable=True, index=True)
    routing_status = Column(String, default="pending", index=True)
    routing_confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=True, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role = Column(String, nullable=False, index=True)
    permission = Column(String, nullable=False, index=True)
    is_allowed = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class SurveyTemplate(Base):
    __tablename__ = "survey_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(Text, nullable=False)  # JSON string of questions
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    high_urgency_only = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True, unique=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BuyerDepartment(Base):
    __tablename__ = "buyer_departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    custom_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
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
    ensure_governance_schema()
    ensure_feedback_routing_schema()

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


def ensure_governance_schema():
    """Backfill governance tables/columns for existing SQLite databases."""
    with engine.connect() as connection:
        users_table_exists = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()

        if users_table_exists:
            rows = connection.exec_driver_sql("PRAGMA table_info(users)").fetchall()
            columns = {row[1] for row in rows}
            if "organization_id" not in columns:
                connection.exec_driver_sql("ALTER TABLE users ADD COLUMN organization_id INTEGER")
            if "department_id" not in columns:
                connection.exec_driver_sql("ALTER TABLE users ADD COLUMN department_id INTEGER")

        # Create lightweight indexes if they do not exist.
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users(organization_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_users_department_id ON users(department_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_role_permissions_role ON role_permissions(role)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_role_permissions_permission ON role_permissions(permission)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)"
        )

        connection.commit()


def ensure_feedback_routing_schema():
    """Backfill feedback routing columns for existing SQLite databases."""
    with engine.connect() as connection:
        feedback_table_exists = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'"
        ).fetchone()

        if not feedback_table_exists:
            return

        rows = connection.exec_driver_sql("PRAGMA table_info(feedback)").fetchall()
        columns = {row[1] for row in rows}

        if "department_tag" not in columns:
            connection.exec_driver_sql("ALTER TABLE feedback ADD COLUMN department_tag VARCHAR")
        if "routing_status" not in columns:
            connection.exec_driver_sql("ALTER TABLE feedback ADD COLUMN routing_status VARCHAR DEFAULT 'pending'")
        if "routing_confidence" not in columns:
            connection.exec_driver_sql("ALTER TABLE feedback ADD COLUMN routing_confidence REAL DEFAULT 0")

        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_feedback_department_tag ON feedback(department_tag)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_feedback_routing_status ON feedback(routing_status)"
        )

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