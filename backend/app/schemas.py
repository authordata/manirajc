from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from .models import Role, SessionStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str
    role: Role
    is_anonymous: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SeekerProfileUpsert(BaseModel):
    gender: Optional[str] = None
    age_range: Optional[str] = None
    causes_csv: Optional[str] = None
    visibility: str = "private"


class GiverProfileUpsert(BaseModel):
    about: Optional[str] = None
    experience: Optional[str] = None
    is_available: bool = True


class SessionRequest(BaseModel):
    cause: Optional[str] = None


class MessageCreate(BaseModel):
    content: str


class FeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


class ReportCreate(BaseModel):
    session_id: Optional[int] = None
    reason: str
    details: Optional[str] = None


class ChatSessionRead(BaseModel):
    id: int
    seeker_id: int
    giver_id: Optional[int]
    is_ai_session: bool
    status: SessionStatus
    cause: Optional[str]
    created_at: datetime


class ChatMessageRead(BaseModel):
    id: int
    session_id: int
    sender_user_id: Optional[int]
    sender_label: str
    content: str
    created_at: datetime
    sender_alias: Optional[str] = None


class SendOtpRequest(BaseModel):
    otp_type: str


class VerifyOtpRequest(BaseModel):
    otp_type: str
    code: str


class FriendRequestCreate(BaseModel):
    receiver_id: int
    session_id: int


class FriendRequestRespond(BaseModel):
    status: str
