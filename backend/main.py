from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Set
import hashlib
import os

from database import init_db, insert_feedback, get_all_feedback, get_summary, update_status, insert_user, get_user_by_email
from brain import analyze
from models import Feedback, User, UserSettings, get_db, create_tables, SessionLocal
from schemas import (
    FeedbackCreate, SurveyCreate, StatusUpdate, UserCreate, UserLogin,
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
        "feedback:ingest",
        "feedback:update_status",
        "users:view",
        "users:update_role",
        "users:manage_settings_any",
    },
    "survey_admin": {
        "feedback:ingest",
        "feedback:update_status",
        "users:view",
        "users:update_role",
        "users:manage_settings_any",
    },
    "survey_manager": {
        "feedback:ingest",
        "feedback:update_status",
    },
    "analyst": {
        "feedback:ingest",
        "feedback:update_status",
    },
    "employee": set(),
}

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
    x_user_id: Optional[int] = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    """Resolve authenticated user from request header."""
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing authentication header X-User-Id")

    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user for provided X-User-Id")

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
        email=user_data.email,
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
    return db.query(User).filter(User.email == email, User.password == hashed_password).first()

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

# Canonical portal entry point.
@app.get("/portal")
@app.get("/portal/")
def portal_entry():
    return FileResponse(os.path.join(FRONTEND_PATH, "portal.html"))


@app.get("/portal/dashboard")
@app.get("/portal/dashboard/")
@app.get("/portal/index.html")
def dashboard_entry():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

# Backward compatibility for old direct portal file links.
@app.get("/portal/portal.html")
def legacy_portal_file_redirect():
    return RedirectResponse(url="/portal/", status_code=307)

@app.get("/portal/survey.html")
def legacy_portal_survey_redirect():
    return RedirectResponse(url="/portal/", status_code=307)

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
                "sentiment": analysis["sentiment"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit survey: {str(e)}")


@app.get("/feed", response_model=List[FeedbackResponse])
def get_feedback_feed(db: Session = Depends(get_db)):
    """Get all feedback for the live feed"""
    try:
        feedbacks = get_all_feedback_orm(db)
        return [FeedbackResponse.from_orm(feedback) for feedback in feedbacks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feedback: {str(e)}")


@app.get("/summary", response_model=SummaryResponse)
def get_feedback_summary(db: Session = Depends(get_db)):
    """Get summary statistics for the dashboard"""
    try:
        summary_data = get_feedback_summary_orm(db)
        return SummaryResponse(**summary_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")


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
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
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
        authenticated_user = authenticate_user_orm(db, user_login.email, user_login.password)
        
        if not authenticated_user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return APIResponse(
            success=True,
            message="Login successful",
            data={
                "id": authenticated_user.id,
                "name": authenticated_user.name,
                "email": authenticated_user.email,
                "role": authenticated_user.role
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate user: {str(e)}")


@app.post("/auth/register", response_model=APIResponse)
def register_auth(user: UserCreate, db: Session = Depends(get_db)):
    """Auth alias for register route used by frontend portal."""
    return register_user(user, db)


@app.post("/auth/login", response_model=APIResponse)
def login_auth(user_login: UserLogin, db: Session = Depends(get_db)):
    """Auth alias for login route used by frontend portal."""
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
