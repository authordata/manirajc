from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class Role(str, Enum):
    SUPPORT_SEEKER = "support_seeker"
    SUPPORT_GIVER = "support_giver"
    # Aliases for backward compatibility
    SEEKER = "support_seeker"
    GIVER = "support_giver"


class SessionStatus(str, Enum):
    OPEN = "open"
    ACTIVE = "active"
    CLOSED = "closed"
    # Aliases for compatibility
    REQUESTED = "open"
    ENDED = "closed"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: Role
    display_name: str
    is_anonymous: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    phone_number: Optional[str] = None
    is_phone_verified: bool = False
    is_email_verified: bool = False
    is_premium: bool = False
    is_admin: bool = False


class OtpCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    target: Optional[str] = None
    code: str
    otp_type: str = "email"  # 'email' or 'phone'
    expires_at: datetime
    is_used: bool = False


class FriendRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(index=True)
    receiver_id: int = Field(index=True)
    session_id: Optional[int] = Field(default=None, index=True)
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SeekerProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True)
    gender: Optional[str] = None
    age_range: Optional[str] = None
    causes_csv: Optional[str] = None
    visibility: str = "private"


class GiverProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True)
    about: Optional[str] = None
    experience: Optional[str] = None
    is_available: bool = True
    is_verified: bool = True


class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    seeker_id: int = Field(index=True)
    giver_id: Optional[int] = Field(default=None, index=True)
    is_ai_session: bool = False
    status: SessionStatus = SessionStatus.OPEN
    cause: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    sender_user_id: Optional[int] = Field(default=None, index=True)
    sender_label: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    submitted_by_user_id: int = Field(index=True)
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, index=True)
    reported_by_user_id: int = Field(index=True)
    reason: str
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MoodRating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, index=True)
    user_id: int = Field(index=True)
    mood_before: int
    mood_after: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
