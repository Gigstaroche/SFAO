from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Request Models
class FeedbackCreate(BaseModel):
    source: str = Field(..., description="Source of the feedback (Twitter, Facebook, etc.)")
    text: str = Field(..., description="The feedback text content")

class SurveyCreate(BaseModel):
    name: str = Field(..., description="Name of the survey respondent")
    department: str = Field(..., description="Department of the respondent")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    text: str = Field(..., description="Survey feedback text")

class StatusUpdate(BaseModel):
    status: str = Field(..., description="New status (New, In-Progress, Resolved)")

class UserCreate(BaseModel):
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")

class UserLogin(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class UserSettingsUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Display name")
    timezone: Optional[str] = Field(None, description="Preferred timezone")
    refresh_interval: Optional[int] = Field(None, ge=5, le=300, description="Refresh interval in seconds")
    notifications_enabled: Optional[bool] = Field(None, description="Notification preference")

class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="New role for the target user")

# Response Models
class FeedbackResponse(BaseModel):
    id: int
    source: str
    text: str
    sentiment: str
    score: float
    category: str
    urgency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class SummaryResponse(BaseModel):
    total: int
    sentiments: dict
    categories: dict
    sources: dict
    urgencies: dict

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class UserSettingsResponse(BaseModel):
    user_id: int
    name: str
    timezone: str
    refresh_interval: int
    notifications_enabled: bool