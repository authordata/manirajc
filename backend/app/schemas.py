from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from .models import Role, SessionStatus


# ── Auth ──────────────────────────────────────────────────
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


# Alias for main.py compatibility
TokenResponse = AuthResponse


# ── User ──────────────────────────────────────────────────
class UserRead(BaseModel):
    id: int
    email: str
    display_name: str
    role: Role
    is_anonymous: bool = True
    phone_number: Optional[str] = None
    is_phone_verified: bool = False
    is_email_verified: bool = False
    is_premium: bool = False
    created_at: Optional[datetime] = None


# ── OTP ───────────────────────────────────────────────────
class SendOtpRequest(BaseModel):
    otp_type: str


class VerifyOtpRequest(BaseModel):
    otp_type: str
    code: str


# Aliases for main.py compatibility
OtpRequest = SendOtpRequest
OtpVerify = VerifyOtpRequest


# ── Profiles ──────────────────────────────────────────────
class SeekerProfileUpsert(BaseModel):
    gender: Optional[str] = None
    age_range: Optional[str] = None
    causes_csv: Optional[str] = None
    visibility: str = "private"


# Aliases for main.py compatibility
SeekerProfileCreate = SeekerProfileUpsert
SeekerProfileUpdate = SeekerProfileUpsert


class SeekerProfileRead(BaseModel):
    id: int
    user_id: int
    gender: Optional[str] = None
    age_range: Optional[str] = None
    causes_csv: Optional[str] = None
    visibility: str = "private"


class GiverProfileUpsert(BaseModel):
    about: Optional[str] = None
    experience: Optional[str] = None
    is_available: bool = True


# Aliases for main.py compatibility
GiverProfileCreate = GiverProfileUpsert
GiverProfileUpdate = GiverProfileUpsert


class GiverProfileRead(BaseModel):
    id: int
    user_id: int
    about: Optional[str] = None
    experience: Optional[str] = None
    is_available: bool = True


# ── Sessions ──────────────────────────────────────────────
class SessionRequest(BaseModel):
    cause: Optional[str] = None


class ChatSessionRead(BaseModel):
    id: int
    seeker_id: int
    giver_id: Optional[int] = None
    is_ai_session: bool = False
    status: SessionStatus
    cause: Optional[str] = None
    created_at: Optional[datetime] = None


class SessionInfo(BaseModel):
    session_id: int
    cause: str | None = None
    status: str
    is_ai_session: bool = False
    created_at: str
    seeker_alias: str | None = None
    last_message: str | None = None
    last_message_time: str | None = None


# ── Messages ──────────────────────────────────────────────
class MessageCreate(BaseModel):
    content: str


# Alias for main.py compatibility
ChatMessageCreate = MessageCreate


class ChatMessageRead(BaseModel):
    id: int
    session_id: int
    sender_user_id: Optional[int] = None
    sender_label: str
    content: str
    created_at: Optional[datetime] = None
    sender_alias: Optional[str] = None


# ── Feedback & Reports ────────────────────────────────────
class FeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


class ReportCreate(BaseModel):
    session_id: Optional[int] = None
    reason: str
    details: Optional[str] = None


# ── Friends ───────────────────────────────────────────────
class FriendRequestCreate(BaseModel):
    receiver_id: int
    session_id: int


class FriendRequestRespond(BaseModel):
    status: str


# ── Mood ──────────────────────────────────────────────────
class MoodCreate(BaseModel):
    mood_before: int
    mood_after: Optional[int] = None


# Aliases for main.py compatibility
MoodRatingCreate = MoodCreate


class MoodRatingRead(BaseModel):
    id: int
    session_id: int
    user_id: int
    mood_before: int
    mood_after: Optional[int] = None
    created_at: Optional[datetime] = None
