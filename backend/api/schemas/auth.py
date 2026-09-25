from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for authenticating a user via email/username and password."""
    email: str = Field(..., description="User login email address or username alias")
    password: str = Field(..., description="Plaintext password")


class TokenResponse(BaseModel):
    """RFC 6749 compliant OAuth2 access token response."""
    access_token: str = Field(..., description="Signed JSON Web Token (HS256)")
    token_type: str = Field(default="bearer", description="Token type (bearer)")
    expires_in: int = Field(..., description="Token validity in seconds")
    role: str = Field(..., description="Stakeholder role (MINISTRY, STATE_OFFICER, DISTRICT_OFFICER, MP)")
    email: str = Field(..., description="Authenticated user email")
    full_name: str = Field(..., description="Stakeholder full name")
    assigned_state: Optional[str] = Field(None, description="Assigned state jurisdiction")
    assigned_district: Optional[str] = Field(None, description="Assigned district jurisdiction")
    assigned_mp_name: Optional[str] = Field(None, description="Assigned MP scrutiny name")


class UserRead(BaseModel):
    """User profile response reflecting active database record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    assigned_state: Optional[str] = None
    assigned_district: Optional[str] = None
    assigned_mp_name: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """Administrator schema for creating a new user account."""
    email: EmailStr = Field(..., description="Unique email address for user")
    password: str = Field(..., min_length=8, description="Initial plaintext password (min 8 characters)")
    full_name: str = Field(..., min_length=2, description="Stakeholder full name")
    role: str = Field(..., pattern="^(MINISTRY|STATE_OFFICER|DISTRICT_OFFICER|MP)$", description="User role")
    assigned_state: Optional[str] = Field(None, description="Required for STATE_OFFICER and DISTRICT_OFFICER")
    assigned_district: Optional[str] = Field(None, description="Required for DISTRICT_OFFICER")
    assigned_mp_name: Optional[str] = Field(None, description="Required for MP")
