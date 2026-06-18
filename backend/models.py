from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os
import uuid

# Database URL
DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sfao.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

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
    share_token = Column(String, nullable=True, unique=True, index=True)
    share_mode = Column(String, default="employee", index=True)
    allow_anonymous = Column(Boolean, default=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
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

class SurveyAssignment(Base):
    __tablename__ = "survey_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    survey_template_id = Column(Integer, ForeignKey("survey_templates.id"), nullable=False, index=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assigned_to_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    assigned_to_organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assignment_status = Column(String, default="pending", index=True)  # pending, in-progress, submitted, expired
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    survey_template_id = Column(Integer, ForeignKey("survey_templates.id"), nullable=False, index=True)
    respondent_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    survey_assignment_id = Column(Integer, ForeignKey("survey_assignments.id"), nullable=True, index=True)
    respondent_name = Column(String, nullable=True)
    respondent_email = Column(String, nullable=True)
    response_source = Column(String, default="employee", index=True)
    is_anonymous = Column(Boolean, default=False)
    responses = Column(Text, nullable=False)  # JSON string of {question_id: answer}
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(String, default="in-progress", index=True)  # in-progress, submitted, draft
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
    ensure_user_settings_schema()
    ensure_governance_schema()
    ensure_feedback_routing_schema()
    ensure_survey_schema()

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


def ensure_survey_schema():
    """Backfill survey template/share columns for existing SQLite databases."""
    with engine.connect() as connection:
        template_exists = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='survey_templates'"
        ).fetchone()
        response_exists = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='survey_responses'"
        ).fetchone()

        if template_exists:
            rows = connection.exec_driver_sql("PRAGMA table_info(survey_templates)").fetchall()
            columns = {row[1] for row in rows}
            if "share_token" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_templates ADD COLUMN share_token VARCHAR")
            if "share_mode" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_templates ADD COLUMN share_mode VARCHAR DEFAULT 'employee'")
            if "allow_anonymous" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_templates ADD COLUMN allow_anonymous BOOLEAN DEFAULT 1")
            if "published_at" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_templates ADD COLUMN published_at DATETIME")

            # Backfill tokens for already-published templates.
            published_rows = connection.exec_driver_sql(
                "SELECT id FROM survey_templates WHERE is_published = 1 AND (share_token IS NULL OR share_token = '')"
            ).fetchall()
            for row in published_rows:
                connection.exec_driver_sql(
                    "UPDATE survey_templates SET share_token = ?, share_mode = COALESCE(share_mode, 'employee'), allow_anonymous = COALESCE(allow_anonymous, 1), published_at = COALESCE(published_at, CURRENT_TIMESTAMP) WHERE id = ?",
                    (uuid.uuid4().hex, row[0]),
                )

            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_survey_templates_share_token ON survey_templates(share_token)"
            )
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_survey_templates_share_mode ON survey_templates(share_mode)"
            )
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_survey_templates_published_at ON survey_templates(published_at)"
            )

        if response_exists:
            rows = connection.exec_driver_sql("PRAGMA table_info(survey_responses)").fetchall()
            columns = {row[1] for row in rows}
            if "respondent_name" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_responses ADD COLUMN respondent_name VARCHAR")
            if "respondent_email" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_responses ADD COLUMN respondent_email VARCHAR")
            if "response_source" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_responses ADD COLUMN response_source VARCHAR DEFAULT 'employee'")
            if "is_anonymous" not in columns:
                connection.exec_driver_sql("ALTER TABLE survey_responses ADD COLUMN is_anonymous BOOLEAN DEFAULT 0")

            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_survey_responses_response_source ON survey_responses(response_source)"
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