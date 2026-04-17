from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import base64
import hashlib
import hmac
import json
import smtplib
import os
import random
from email.message import EmailMessage

from database import init_db, insert_feedback, get_all_feedback, get_summary, update_status, insert_user, get_user_by_email
from brain import analyze
from models import Feedback, User, UserSettings, get_db, create_tables, SessionLocal
from schemas import (
    FeedbackCreate, SurveyCreate, StatusUpdate, UserCreate, UserLogin, EmailCodeRequest,
    UserSettingsUpdate, UserSettingsResponse, UserRoleUpdate,
    FeedbackResponse, UserResponse, SummaryResponse, APIResponse
)

VALID_ROLES = {
    "super_admin",
    "survey_admin",
    "survey_manager",
    "analyst",
    "employee",
}

ROLE_PERMISSIONS = {
    "super_admin": {
        "feedback:view",
        "feedback:ingest",
        "feedback:update_status",
        "users:view",
        "users:update_role",
        "users:manage_settings_any",
    },
    "survey_admin": {
        "feedback:view",
        "feedback:ingest",
        "feedback:update_status",
        "users:view",
        "users:update_role",
        "users:manage_settings_any",
    },
    "survey_manager": {
        "feedback:view",
        "feedback:ingest",
        "feedback:update_status",
    },
    "analyst": {
        "feedback:view",
        "feedback:ingest",
        "feedback:update_status",
    },
    "employee": {
        "feedback:view",
    },
}

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "aol.com",
    "protonmail.com",
    "gmx.com",
    "mail.com",
    "live.com",
    "msn.com",
}

EMAIL_CODE_EXPIRY_MINUTES = 10
EMAIL_VERIFICATION_CODES: Dict[str, Dict[str, str]] = {}
ACCESS_TOKEN_EXPIRY_MINUTES = 60 * 12


def get_auth_secret() -> str:
    secret = (os.getenv("SFAO_AUTH_SECRET", "") or "").strip()
    if secret:
        return secret
    return "sfao-dev-secret-change-this"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def create_access_token(user: User) -> str:
    expires_at = int((datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)).timestamp())
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": expires_at,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_json)
    signature = hmac.new(get_auth_secret().encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(signature)}"


def parse_access_token(token: str) -> Dict[str, object]:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    expected_sig = hmac.new(get_auth_secret().encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    given_sig = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected_sig, given_sig):
        raise HTTPException(status_code=401, detail="Invalid access token")

    try:
        payload_raw = _b64url_decode(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid access token payload")

    if int(payload.get("exp", 0)) < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=401, detail="Access token expired")

    return payload


def is_truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def is_production_env() -> bool:
    return (os.getenv("SFAO_ENV", "development") or "development").strip().lower() == "production"


def get_development_org_code() -> Optional[str]:
    enabled_raw = os.getenv("SFAO_ENABLE_DEV_CODE")
    enabled = is_truthy(enabled_raw) if enabled_raw is not None else (not is_production_env())
    if not enabled:
        return None

    code = (os.getenv("SFAO_DEV_ORG_CODE", "DEV-ORG-2026") or "").strip()
    return code or None


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def get_allowed_email_domains() -> Set[str]:
    raw = os.getenv("SFAO_ALLOWED_EMAIL_DOMAINS", "")
    if not raw.strip():
        return set()
    return {domain.strip().lower() for domain in raw.split(",") if domain.strip()}


def validate_work_email(email: str) -> str:
    normalized = normalize_email(email)
    if "@" not in normalized:
        raise HTTPException(status_code=400, detail="Use a valid work email address")

    domain = normalized.rsplit("@", 1)[1]
    if domain in PUBLIC_EMAIL_DOMAINS:
        raise HTTPException(status_code=400, detail="Use your organization email address")

    allowed_domains = get_allowed_email_domains()
    if allowed_domains and domain not in allowed_domains:
        raise HTTPException(status_code=400, detail="Email domain is not allowed for this organization")

    return normalized


def validate_org_code(provided_code: Optional[str], *, required: bool = False) -> None:
    expected_code = (os.getenv("SFAO_ORG_ACCESS_CODE", "") or "").strip()
    if not expected_code:
        expected_code = get_development_org_code() or ""
    submitted_code = (provided_code or "").strip()

    if not expected_code:
        if required and not submitted_code:
            raise HTTPException(status_code=400, detail="Organization code is required")
        return

    if submitted_code != expected_code:
        raise HTTPException(status_code=403, detail="Invalid organization code")


def get_signup_code_delivery_mode() -> str:
    raw_mode = (os.getenv("SFAO_SIGNUP_CODE_MODE", "") or "").strip().lower()
    if raw_mode:
        mode = raw_mode
    elif get_development_org_code():
        mode = "org_code"
    else:
        mode = "email"
    if mode not in {"email", "org_code"}:
        return "email"
    return mode


def requires_login_code() -> bool:
    return is_truthy(os.getenv("SFAO_REQUIRE_LOGIN_CODE", "false"))


def send_org_email_code(email: str, code: str) -> None:
    smtp_host = (os.getenv("SFAO_SMTP_HOST", "") or "").strip()
    smtp_port = int((os.getenv("SFAO_SMTP_PORT", "587") or "587").strip())
    smtp_username = (os.getenv("SFAO_SMTP_USERNAME", "") or "").strip()
    smtp_password = (os.getenv("SFAO_SMTP_PASSWORD", "") or "").strip()
    smtp_from = (os.getenv("SFAO_SMTP_FROM", smtp_username) or "").strip()
    use_tls = (os.getenv("SFAO_SMTP_USE_TLS", "true") or "").strip().lower() in {"1", "true", "yes", "on"}

    if not smtp_host or not smtp_username or not smtp_password or not smtp_from:
        raise HTTPException(
            status_code=500,
            detail="Email verification is not configured. Set SMTP environment variables.",
        )

    msg = EmailMessage()
    msg["Subject"] = "SFAO sign-up verification code"
    msg["From"] = smtp_from
    msg["To"] = email
    msg.set_content(
        f"Your SFAO verification code is: {code}\n\n"
        f"This code expires in {EMAIL_CODE_EXPIRY_MINUTES} minutes."
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
    except Exception:
        raise HTTPException(status_code=502, detail="Could not send verification email")


def store_email_verification_code(email: str, code: str) -> None:
    EMAIL_VERIFICATION_CODES[email] = {
        "code": code,
        "expires_at": (datetime.utcnow() + timedelta(minutes=EMAIL_CODE_EXPIRY_MINUTES)).isoformat(),
    }


def consume_email_verification_code(email: str, provided_code: Optional[str]) -> bool:
    submitted = (provided_code or "").strip()
    record = EMAIL_VERIFICATION_CODES.get(email)
    if not record:
        return False

    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.utcnow() > expires_at:
        EMAIL_VERIFICATION_CODES.pop(email, None)
        raise HTTPException(status_code=400, detail="Verification code expired. Request a new code.")

    if record["code"] != submitted:
        raise HTTPException(status_code=403, detail="Invalid verification code")

    EMAIL_VERIFICATION_CODES.pop(email, None)
    return True


def validate_signup_verification(email: str, provided_code: Optional[str]) -> None:
    mode = get_signup_code_delivery_mode()
    if mode == "org_code":
        validate_org_code(provided_code, required=True)
        return

    if not consume_email_verification_code(email, provided_code):
        raise HTTPException(status_code=400, detail="Request a verification code before signing up")


def normalize_role(role: Optional[str]) -> str:
    """Normalize role naming to stable RBAC identifiers."""
    raw = (role or "employee").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "admin": "survey_admin",
        "manager": "survey_manager",
        "user": "employee",
    }
    return aliases.get(raw, raw)

def has_permission(user_role: Optional[str], permission: str) -> bool:
    role = normalize_role(user_role)
    return permission in ROLE_PERMISSIONS.get(role, set())

def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """Resolve authenticated user from bearer token only."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    payload = parse_access_token(token)
    resolved_user_id = int(payload.get("sub", 0))

    if not resolved_user_id:
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    user = db.query(User).filter(User.id == resolved_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user for provided authentication")

    return user

def require_permission(permission: str):
    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
        return current_user

    return _guard

# --- Database Functions ---
def create_feedback_orm(db: Session, feedback_data: FeedbackCreate, analysis_result: dict) -> Feedback:
    """Create feedback using SQLAlchemy ORM"""
    db_feedback = Feedback(
        source=feedback_data.source,
        text=feedback_data.text,
        sentiment=analysis_result["sentiment"],
        score=analysis_result["score"],
        category=analysis_result["category"],
        urgency=analysis_result["urgency"],
        status="New",
        created_at=datetime.now()
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def get_all_feedback_orm(db: Session) -> List[Feedback]:
    """Get all feedback using SQLAlchemy ORM"""
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()

def get_feedback_summary_orm(db: Session) -> dict:
    """Get summary statistics using SQLAlchemy ORM"""
    feedbacks = db.query(Feedback).all()
    total = len(feedbacks)
    
    sentiments = {}
    categories = {}
    sources = {}
    urgencies = {}
    
    for feedback in feedbacks:
        # Count sentiments
        sentiments[feedback.sentiment] = sentiments.get(feedback.sentiment, 0) + 1
        
        # Count categories
        categories[feedback.category] = categories.get(feedback.category, 0) + 1
        
        # Count sources
        sources[feedback.source] = sources.get(feedback.source, 0) + 1
        
        # Count urgencies
        urgencies[feedback.urgency] = urgencies.get(feedback.urgency, 0) + 1
    
    return {
        "total": total,
        "sentiments": sentiments,
        "categories": categories,
        "sources": sources,
        "urgencies": urgencies
    }

def update_feedback_status_orm(db: Session, feedback_id: int, status: str) -> Optional[Feedback]:
    """Update feedback status using SQLAlchemy ORM"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if feedback:
        feedback.status = status
        db.commit()
        db.refresh(feedback)
    return feedback

def create_user_orm(db: Session, user_data: UserCreate) -> User:
    """Create user using SQLAlchemy ORM"""
    hashed_password = hashlib.sha256(user_data.password.encode()).hexdigest()
    is_first_user = db.query(User).count() == 0
    db_user = User(
        name=user_data.name,
        email=normalize_email(user_data.email),
        password=hashed_password,
        role="super_admin" if is_first_user else "employee",
        created_at=datetime.now()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user_orm(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user using SQLAlchemy ORM"""
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return db.query(User).filter(User.email == normalize_email(email), User.password == hashed_password).first()

def get_or_create_user_settings(db: Session, user: User) -> UserSettings:
    """Get existing settings or create defaults for a user."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if settings:
        return settings

    settings = UserSettings(
        user_id=user.id,
        name=user.name,
        timezone="Africa/Lagos",
        refresh_interval=10,
        notifications_enabled=True,
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings

def ensure_super_admin_exists() -> None:
    """Promote earliest user to super_admin if none exists."""
    db = SessionLocal()
    try:
        all_users = db.query(User).order_by(User.created_at.asc()).all()
        has_super_admin = any(normalize_role(user.role) == "super_admin" for user in all_users)
        if has_super_admin:
            return

        fallback_admin = all_users[0] if all_users else None
        if fallback_admin:
            fallback_admin.role = "super_admin"
            db.commit()
    finally:
        db.close()

# --- App Setup ---
app = FastAPI(title="SFAO - Smart Feedback Analyzer for Organization", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()
create_tables()  # Create SQLAlchemy tables
ensure_super_admin_exists()

FRONTEND_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

# Canonical dashboard entry point.
@app.get("/portal")
@app.get("/portal/")
def portal_entry():
    return RedirectResponse(url="/portal/dashboard", status_code=307)


@app.get("/portal/dashboard")
@app.get("/portal/dashboard/")
@app.get("/portal/index.html")
def dashboard_entry():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

# Serve frontend assets and other pages under /portal
app.mount("/portal", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")

# --- Initialize DB on startup ---
@app.on_event("startup")
def startup():
    init_db()
    ensure_super_admin_exists()
    print("[SFAO] System ready.")


# --- Routes ---
@app.get("/")
def root():
    return {"message": "SFAO API is running.", "docs": "/docs"}


@app.post("/ingest", response_model=APIResponse)
def ingest_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feedback:ingest")),
):
    """Ingest feedback from external sources"""
    try:
        # Analyze the feedback
        analysis = analyze(feedback.text)
        
        # Create feedback using SQLAlchemy ORM
        db_feedback = create_feedback_orm(db, feedback, analysis)
        
        return APIResponse(
            success=True,
            message="Feedback ingested successfully",
            data={
                "id": db_feedback.id,
                "sentiment": analysis["sentiment"],
                "category": analysis["category"],
                "urgency": analysis["urgency"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest feedback: {str(e)}")


@app.post("/survey", response_model=APIResponse)
def submit_survey(survey: SurveyCreate, db: Session = Depends(get_db)):
    """Submit internal survey feedback"""
    try:
        # Create feedback object for analysis
        feedback_data = FeedbackCreate(
            source=f"Survey - {survey.department}",
            text=f"{survey.name} (Rating: {survey.rating}/5): {survey.text}"
        )
        
        # Analyze the feedback
        analysis = analyze(feedback_data.text)
        
        # Adjust sentiment based on rating
        if survey.rating <= 2:
            analysis["sentiment"] = "Negative"
            analysis["urgency"] = "High"
        elif survey.rating >= 4:
            analysis["sentiment"] = "Positive"
        
        # Create feedback using SQLAlchemy ORM
        db_feedback = create_feedback_orm(db, feedback_data, analysis)
        
        return APIResponse(
            success=True,
            message="Survey submitted successfully",
            data={
                "id": db_feedback.id,
                "rating": survey.rating,
                "sentiment": analysis["sentiment"],
                "category": analysis["category"],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit survey: {str(e)}")


@app.get("/feed", response_model=List[FeedbackResponse])
def get_feedback_feed(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    urgency: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feedback:view")),
):
    """Get all feedback for the live feed"""
    try:
        query = db.query(Feedback)

        if urgency:
            query = query.filter(Feedback.urgency == urgency)
        if category:
            query = query.filter(Feedback.category.ilike(category))
        if source:
            query = query.filter(Feedback.source.ilike(source))
        if status:
            query = query.filter(Feedback.status == status)
        if q:
            pattern = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    Feedback.text.ilike(pattern),
                    Feedback.source.ilike(pattern),
                    Feedback.category.ilike(pattern),
                )
            )

        feedbacks = (
            query.order_by(Feedback.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [FeedbackResponse.from_orm(feedback) for feedback in feedbacks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feedback: {str(e)}")


@app.get("/summary", response_model=SummaryResponse)
def get_feedback_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feedback:view")),
):
    """Get summary statistics for the dashboard"""
    try:
        summary_data = get_feedback_summary_orm(db)
        return SummaryResponse(**summary_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")


@app.get("/auth/config", response_model=APIResponse)
def auth_config():
    """Expose non-sensitive auth mode metadata for frontend behavior."""
    signup_mode = get_signup_code_delivery_mode()
    dev_code = get_development_org_code()

    return APIResponse(
        success=True,
        message="Auth config",
        data={
            "signup_mode": signup_mode,
            "require_login_code": requires_login_code(),
            "dev_code_hint": dev_code if signup_mode == "org_code" and dev_code else None,
        },
    )


@app.post("/auth/send-code", response_model=APIResponse)
def send_signup_email_code(payload: EmailCodeRequest, db: Session = Depends(get_db)):
    """Send one-time verification code to a user's organization email."""
    if get_signup_code_delivery_mode() != "email":
        raise HTTPException(status_code=400, detail="Email verification code is not enabled in this environment")

    normalized_email = validate_work_email(payload.email)

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    code = f"{random.randint(0, 999999):06d}"
    send_org_email_code(normalized_email, code)
    store_email_verification_code(normalized_email, code)

    return APIResponse(success=True, message="Verification code sent", data={"email": normalized_email})


@app.put("/feedback/{feedback_id}/status", response_model=APIResponse)
def update_feedback_status(
    feedback_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feedback:update_status")),
):
    """Update feedback status"""
    try:
        valid_statuses = ["New", "In-Progress", "Resolved"]
        if status_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")
            
        updated_feedback = update_feedback_status_orm(db, feedback_id, status_update.status)
        
        if not updated_feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        return APIResponse(
            success=True,
            message="Status updated successfully",
            data={"id": feedback_id, "status": status_update.status}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@app.post("/users/register", response_model=APIResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        normalized_email = validate_work_email(user.email)
        validate_signup_verification(normalized_email, user.org_code)

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        user.email = normalized_email
        
        # Create new user
        db_user = create_user_orm(db, user)
        
        return APIResponse(
            success=True,
            message="User registered successfully",
            data={
                "id": db_user.id,
                "name": db_user.name,
                "email": db_user.email,
                "role": db_user.role
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")


@app.post("/users/login", response_model=APIResponse)
def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user login"""
    try:
        normalized_email = validate_work_email(user_login.email)

        require_login_code = requires_login_code()
        validate_org_code(user_login.org_code, required=require_login_code)

        authenticated_user = authenticate_user_orm(db, normalized_email, user_login.password)
        
        if not authenticated_user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return APIResponse(
            success=True,
            message="Login successful",
            data={
                "id": authenticated_user.id,
                "name": authenticated_user.name,
                "email": authenticated_user.email,
                "role": authenticated_user.role,
                "access_token": create_access_token(authenticated_user),
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRY_MINUTES * 60,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate user: {str(e)}")


@app.post("/auth/register", response_model=APIResponse)
def register_auth(user: UserCreate, db: Session = Depends(get_db)):
    """Auth alias for register route used by the dashboard login overlay."""
    return register_user(user, db)


@app.post("/auth/login", response_model=APIResponse)
def login_auth(user_login: UserLogin, db: Session = Depends(get_db)):
    """Auth alias for login route used by the dashboard login overlay."""
    return login_user(user_login, db)


@app.get("/users/{user_id}/settings", response_model=UserSettingsResponse)
def get_user_settings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get persisted settings for a user profile."""
    can_read_any_settings = has_permission(current_user.role, "users:manage_settings_any")
    if current_user.id != user_id and not can_read_any_settings:
        raise HTTPException(status_code=403, detail="You can only view your own settings")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = get_or_create_user_settings(db, user)
    return UserSettingsResponse(
        user_id=user.id,
        name=settings.name or user.name,
        timezone=settings.timezone or "Africa/Lagos",
        refresh_interval=settings.refresh_interval or 10,
        notifications_enabled=bool(settings.notifications_enabled),
    )


@app.put("/users/{user_id}/settings", response_model=APIResponse)
def update_user_settings(
    user_id: int,
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update persisted settings for a user profile."""
    can_update_any_settings = has_permission(current_user.role, "users:manage_settings_any")
    if current_user.id != user_id and not can_update_any_settings:
        raise HTTPException(status_code=403, detail="You can only update your own settings")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    settings = get_or_create_user_settings(db, user)

    if payload.name is not None:
        settings.name = payload.name.strip() or user.name
        user.name = settings.name
    if payload.timezone is not None:
        settings.timezone = payload.timezone
    if payload.refresh_interval is not None:
        settings.refresh_interval = payload.refresh_interval
    if payload.notifications_enabled is not None:
        settings.notifications_enabled = payload.notifications_enabled

    db.commit()
    db.refresh(settings)
    db.refresh(user)

    return APIResponse(
        success=True,
        message="User settings updated",
        data={
            "user_id": user.id,
            "name": settings.name or user.name,
            "timezone": settings.timezone,
            "refresh_interval": settings.refresh_interval,
            "notifications_enabled": bool(settings.notifications_enabled),
        },
    )

@app.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("users:view")),
):
    """Get all registered users"""
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [UserResponse.from_orm(user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@app.put("/admin/users/{user_id}/role", response_model=APIResponse)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("users:update_role")),
):
    """Update a user's role (survey admin / super admin only)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")

    new_role = normalize_role(payload.role)
    if new_role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {payload.role}")

    actor_role = normalize_role(actor.role)
    target_role = normalize_role(target.role)

    if target_role == "super_admin" and actor_role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can modify another super admin")

    if new_role == "super_admin" and actor_role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can assign super_admin role")

    target.role = new_role
    db.commit()
    db.refresh(target)

    return APIResponse(
        success=True,
        message="User role updated",
        data={
            "id": target.id,
            "name": target.name,
            "email": target.email,
            "role": target.role,
        },
    )

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SFAO API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
