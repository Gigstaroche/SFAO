from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional, List

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


class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="Email to send password reset code to")


class PasswordResetConfirm(BaseModel):
    email: str = Field(..., description="Email address for the account")
    code: str = Field(..., description="Verification code sent to email")
    new_password: str = Field(..., min_length=6, description="New password to set for the account")

class UserSettingsUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Display name")
    timezone: Optional[str] = Field(None, description="Preferred timezone")
    refresh_interval: Optional[int] = Field(None, ge=5, le=300, description="Refresh interval in seconds")
    notifications_enabled: Optional[bool] = Field(None, description="Notification preference")

class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="New role for the target user")


class SurveyTemplateCreate(BaseModel):
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    questions: str = Field(..., description="JSON string of questions")


class SurveyTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    questions: Optional[str] = Field(None, description="JSON string of questions")
    is_published: Optional[bool] = Field(None, description="Publish status")


class SurveyTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    questions: str
    created_by: Optional[int]
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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

class SurveyAssignmentCreate(BaseModel):
    survey_template_id: int = Field(..., ge=1, description="Survey template ID")
    assigned_to_user_id: Optional[int] = Field(None, ge=1, description="Assign to specific user")
    assigned_to_department_id: Optional[int] = Field(None, ge=1, description="Assign to all users in department")
    assigned_to_organization_id: Optional[int] = Field(None, ge=1, description="Assign to all users in organization")
    due_date: Optional[datetime] = Field(None, description="Survey deadline")


class SurveyAssignmentResponse(BaseModel):
    id: int
    survey_template_id: int
    assigned_to_user_id: Optional[int]
    assigned_to_department_id: Optional[int]
    assigned_to_organization_id: Optional[int]
    assigned_by: int
    assignment_status: str
    assigned_at: datetime
    due_date: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class SurveyResponseCreate(BaseModel):
    survey_template_id: int = Field(..., ge=1, description="Survey template ID")
    responses: str = Field(..., description="JSON string of {question_id: answer}")


class SurveyResponseUpdate(BaseModel):
    responses: Optional[str] = Field(None, description="JSON string of {question_id: answer}")
    status: Optional[str] = Field(None, description="Response status: draft, in-progress, submitted")


class SurveyResponseData(BaseModel):
    id: int
    survey_template_id: int
    respondent_user_id: int
    survey_assignment_id: Optional[int]
    responses: str
    start_time: datetime
    submitted_at: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

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
    sentiments: Dict[str, int]
    categories: Dict[str, int]
    sources: Dict[str, int]
    urgencies: Dict[str, int]

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class UserSettingsResponse(BaseModel):
    user_id: int
    name: str
    timezone: str
    refresh_interval: int
    notifications_enabled: bool