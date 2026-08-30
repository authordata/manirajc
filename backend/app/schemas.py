from datetime import datetime
from typing import Optional, List, Union

from pydantic import BaseModel, EmailStr, Field

from .models import Role, SessionStatus


# ── Auth ──────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    passwordHash: Optional[str] = None
    display_name: Optional[str] = None
    role: Role = Role.SUPPORT_SEEKER
    is_anonymous: bool = True
    phoneNumber: Optional[str] = None
    phone_number: Optional[str] = None

    def get_password(self) -> str:
        return self.password or self.passwordHash or "Password123!"

    def get_display_name(self) -> str:
        if self.display_name and self.display_name.strip():
            return self.display_name.strip()
        return "Anonymous User" if self.is_anonymous else "User"


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
    is_active: bool = True
    is_verified: bool = True
    created_at: Optional[datetime] = None


# ── OTP ───────────────────────────────────────────────────
class SendOtpRequest(BaseModel):
    otp_type: Optional[str] = "email"
    method: Optional[str] = None
    target: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    otp_type: Optional[str] = "email"
    code: str
    reference_id: Optional[str] = None


# Aliases for main.py compatibility
OtpRequest = SendOtpRequest
OtpVerify = VerifyOtpRequest


# ── Profiles ──────────────────────────────────────────────
class SeekerProfileUpsert(BaseModel):
    gender: Optional[str] = None
    age_range: Optional[str] = None
    causes_csv: Optional[str] = None
    causes: Optional[List[str]] = None
    alias: Optional[str] = None
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
    name: Optional[str] = None
    about: Optional[str] = None
    bio: Optional[str] = None
    experience: Optional[str] = None
    qualifications: Optional[List[str]] = None
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
    is_verified: bool = True


# ── Sessions ──────────────────────────────────────────────
class SessionRequest(BaseModel):
    cause: Optional[str] = None


class ChatSessionRead(BaseModel):
    id: int
    session_id: Optional[int] = None
    seeker_id: int
    giver_id: Optional[int] = None
    is_ai_session: bool = False
    status: SessionStatus
    cause: Optional[str] = None
    created_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if self.session_id is None:
            self.session_id = self.id


class SessionInfo(BaseModel):
    session_id: int
    cause: Optional[str] = None
    status: str
    is_ai_session: bool = False
    created_at: str
    seeker_alias: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[str] = None


# ── Messages ──────────────────────────────────────────────
class MessageCreate(BaseModel):
    content: str


# Alias for main.py compatibility
ChatMessageCreate = MessageCreate


class ChatMessageRead(BaseModel):
    id: int
    session_id: int
    sender_user_id: Optional[int] = None
    sender_id: Optional[int] = None
    sender_label: str
    content: str
    created_at: Optional[datetime] = None
    sender_alias: Optional[str] = None

    def model_post_init(self, __context):
        if self.sender_id is None:
            self.sender_id = self.sender_user_id


# ── Feedback & Reports ────────────────────────────────────
class FeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None
    comments: Optional[str] = None


class ReportCreate(BaseModel):
    session_id: Optional[int] = None
    reported_user_id: Optional[int] = None
    reason: str
    details: Optional[str] = None


# ── Friends ───────────────────────────────────────────────
class FriendRequestCreate(BaseModel):
    receiver_id: Optional[int] = None
    target_user_id: Optional[int] = None
    session_id: Optional[int] = None


class FriendRequestResponse(BaseModel):
    id: int
    requester_id: int
    target_id: int
    status: str
    created_at: Optional[datetime] = None


class FriendRequestRespond(BaseModel):
    status: Optional[str] = "accepted"
    action: Optional[str] = "accept"


# ── Mood ──────────────────────────────────────────────────
class MoodCreate(BaseModel):
    mood_before: int
    mood_after: Optional[int] = None
    session_id: Optional[int] = None


# Aliases for main.py compatibility
MoodRatingCreate = MoodCreate


class MoodRatingRead(BaseModel):
    id: int
    session_id: Optional[int] = None
    user_id: int
    mood_before: int
    mood_after: Optional[int] = None
    created_at: Optional[datetime] = None


class SubscriptionStatus(BaseModel):
    is_premium: bool = False
    expires_at: Optional[str] = None
