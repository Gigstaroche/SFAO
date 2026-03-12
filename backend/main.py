from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import hashlib
import os

from database import init_db, insert_feedback, get_all_feedback, get_summary, update_status, insert_user, get_user_by_email
from brain import analyze

# --- App Setup ---
app = FastAPI(title="SFAO - Smart Feedback Analyzer for Organization", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend at /portal
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')
app.mount("/portal", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")

# --- Initialize DB on startup ---
@app.on_event("startup")
def startup():
    init_db()
    print("[SFAO] System ready.")


# --- Request Models ---
class FeedbackIn(BaseModel):
    source: str
    text: str

class SurveyIn(BaseModel):
    name: str
    department: str
    rating: int
    text: str

class StatusUpdate(BaseModel):
    status: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str


# --- Helpers ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# --- Routes ---
@app.get("/")
def root():
    return {"message": "SFAO API is running.", "docs": "/docs"}


@app.post("/ingest")
def ingest(data: FeedbackIn):
    """Ingest feedback from external sources (social media, chatbots)."""
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    result = analyze(data.text, data.source)
    row_id = insert_feedback(**result)
    return {"id": row_id, "status": "ingested", **result}


@app.post("/survey")
def survey(data: SurveyIn):
    """Ingest feedback from internal employee/customer surveys."""
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    full_text = f"[{data.department}] Rating {data.rating}/5: {data.text}"
    result = analyze(full_text, "Survey")
    row_id = insert_feedback(**result)
    return {"id": row_id, "status": "submitted", **result}


@app.get("/feed")
def feed(limit: int = 50):
    """Get the latest feedback entries."""
    return get_all_feedback(limit)


@app.get("/summary")
def summary():
    """Get aggregated stats for the dashboard."""
    return get_summary()


@app.patch("/feedback/{feedback_id}/status")
def set_status(feedback_id: int, body: StatusUpdate):
    """Update action status: New → In-Progress → Resolved."""
    valid = ["New", "In-Progress", "Resolved"]
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid}")
    update_status(feedback_id, body.status)
    return {"id": feedback_id, "status": body.status}


@app.post("/auth/register")
def register(data: UserRegister):
    """Register a new portal user."""
    hashed = hash_password(data.password)
    user_id = insert_user(data.name, data.email, hashed)
    if user_id is None:
        raise HTTPException(status_code=409, detail="Email already registered.")
    return {"id": user_id, "message": "Registered successfully."}


@app.post("/auth/login")
def login(data: UserLogin):
    """Login and return basic user info."""
    user = get_user_by_email(data.email)
    if not user or user["password"] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "id":    user["id"],
        "name":  user["name"],
        "email": user["email"],
        "role":  user["role"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
