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


class FeedbackRouteUpdate(BaseModel):
    department_tag: str = Field(..., min_length=2, description="Target department for this feedback")
    routing_status: str = Field("assigned", description="Routing state: assigned or needs-triage")
    routing_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score from 0 to 1")

class UserCreate(BaseModel):
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")
    org_code: Optional[str] = Field(None, description="Organization access code")

class UserLogin(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    org_code: Optional[str] = Field(None, description="Organization sign-in code")


class EmailCodeRequest(BaseModel):
    email: str = Field(..., description="Organization email used for verification")

class UserSettingsUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Display name")
    timezone: Optional[str] = Field(None, description="Preferred timezone")
    refresh_interval: Optional[int] = Field(None, ge=5, le=300, description="Refresh interval in seconds")
    notifications_enabled: Optional[bool] = Field(None, description="Notification preference")

class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="New role for the target user")


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Organization display name")
    code: Optional[str] = Field(None, description="Optional short organization code")


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Department name")
    organization_id: Optional[int] = Field(None, ge=1, description="Parent organization id")


class BuyerCreate(BaseModel):
    name: str = Field(..., min_length=2, description="Buyer name")
    code: Optional[str] = Field(None, description="Optional buyer code")
    organization_id: Optional[int] = Field(None, ge=1, description="Parent organization id")


class BuyerDepartmentCreate(BaseModel):
    buyer_id: int = Field(..., ge=1, description="Buyer ID")
    department_id: int = Field(..., ge=1, description="Department ID")
    custom_name: Optional[str] = Field(None, description="Custom department name for this buyer")


class RolePermissionsUpdate(BaseModel):
    permissions: List[str] = Field(default_factory=list, description="Allowed permissions for role")

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
    department_tag: Optional[str] = None
    routing_status: Optional[str] = None
    routing_confidence: Optional[float] = None
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


class BuyerResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    organization_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BuyerDepartmentResponse(BaseModel):
    id: int
    buyer_id: int
    department_id: int
    custom_name: Optional[str] = None
    is_active: bool
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