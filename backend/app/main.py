from datetime import datetime, timedelta
import os
import random
from typing import Annotated, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func

import requests as http_requests

from fastapi.responses import FileResponse, JSONResponse
import pathlib

from .database import create_db_and_tables, get_session
from .models import (
    ChatMessage,
    ChatSession,
    Feedback,
    FriendRequest,
    GiverProfile,
    MoodRating,
    OtpCode,
    Report,
    Role,
    SeekerProfile,
    SessionStatus,
    User,
)
from .schemas import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatSessionRead,
    FeedbackCreate,
    FriendRequestCreate,
    FriendRequestRespond,
    FriendRequestResponse,
    GiverProfileCreate,
    GiverProfileRead,
    GiverProfileUpdate,
    GiverProfileUpsert,
    LoginRequest,
    MoodRatingCreate,
    MoodRatingRead,
    OtpRequest,
    OtpVerify,
    RegisterRequest,
    ReportCreate,
    SeekerProfileCreate,
    SeekerProfileRead,
    SeekerProfileUpdate,
    SeekerProfileUpsert,
    SessionInfo,
    SessionRequest,
    SubscriptionStatus,
    TokenResponse,
    UserRead,
)
from .security import create_access_token, decode_access_token, get_password_hash, verify_password

app = FastAPI(title="HearU API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        user_id_str = decode_access_token(token)
        user_id = int(user_id_str)
    except (ValueError, Exception):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_user_from_token(token: str, db: Session) -> User | None:
    try:
        user_id_str = decode_access_token(token)
        user_id = int(user_id_str)
        return db.get(User, user_id)
    except Exception:
        return None


def require_role(role: Role):
    def role_checker(user: User = Depends(current_user)) -> User:
        # Compare by value to handle enum aliases (SEEKER == SUPPORT_SEEKER == "support_seeker")
        if user.role.value != role.value:
            raise HTTPException(status_code=403, detail="Forbidden: wrong role")
        return user

    return role_checker


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return user


def require_verified(user: User = Depends(current_user)) -> User:
    if not user.is_email_verified and not user.is_phone_verified:
        raise HTTPException(status_code=403, detail="Verification required")
    return user


def current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_session),
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        user_id_str = decode_access_token(token)
        return db.get(User, int(user_id_str))
    except Exception:
        return None


# ── Frontend & Root ───────────────────────────────────────────────
@app.get("/")
def root():
    backend_frontend = pathlib.Path(__file__).parent / "frontend" / "index.html"
    if backend_frontend.exists():
        return FileResponse(backend_frontend)

    root_frontend = pathlib.Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if root_frontend.exists():
        return FileResponse(root_frontend)

    return {"status": "ok", "service": "HearU API", "docs": "/docs"}


@app.get("/health")
def healthcheck():
    return {"status": "healthy"}


# ── Users & Auth ──────────────────────────────────────────────────
@app.get("/me", response_model=UserRead)
@app.get("/users/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user


@app.delete("/users/me")
def delete_me(user: User = Depends(current_user), db: Session = Depends(get_session)):
    db.delete(user)
    db.commit()
    return {"status": "deleted", "message": "Account successfully deleted"}


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_session)):
    existing = db.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    disp_name = payload.get_display_name()
    if payload.display_name and payload.display_name.strip():
        existing_name = db.exec(select(User).where(User.display_name == disp_name)).first()
        if existing_name:
            raise HTTPException(status_code=400, detail="Display name already taken. Please choose another.")

    pwd = payload.get_password()
    user = User(
        email=payload.email,
        password_hash=get_password_hash(pwd),
        display_name=disp_name,
        role=payload.role,
        is_anonymous=payload.is_anonymous,
        phone_number=payload.phone_number or payload.phoneNumber,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user.role in (Role.SEEKER, Role.SUPPORT_SEEKER):
        db.add(SeekerProfile(user_id=user.id))
    elif user.role in (Role.GIVER, Role.SUPPORT_GIVER):
        db.add(GiverProfile(user_id=user.id, is_available=True, is_verified=True))
    db.commit()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_session)
):
    email = None
    password = None

    # Handle Form URL-Encoded (Android / OAuth2) or JSON (Web)
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")
    else:
        try:
            body = await request.json()
            email = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request format")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = db.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@app.post("/auth/anonymous", response_model=TokenResponse)
def create_anonymous_user(db: Session = Depends(get_session)):
    anon_num = random.randint(100000, 999999)
    user = User(
        email=f"anonymous_{anon_num}@hearu.app",
        password_hash=get_password_hash("anonymous"),
        display_name=f"Anonymous-{anon_num}",
        role=Role.SUPPORT_SEEKER,
        is_anonymous=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(SeekerProfile(user_id=user.id))
    db.commit()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


# ── OTP Endpoints ─────────────────────────────────────────────────
@app.post("/auth/otp/send")
@app.post("/auth/send-otp")
def send_otp(
    payload: OtpRequest,
    user: Optional[User] = Depends(current_user_optional),
    db: Session = Depends(get_session)
):
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    target = payload.target or payload.email or payload.phone_number or (user.email if user else None)
    otp = OtpCode(
        user_id=user.id if user else None,
        target=target,
        code=code,
        otp_type=payload.otp_type or payload.method or "email",
        expires_at=expires_at,
    )
    db.add(otp)
    db.commit()
    return {"status": "sent", "code": code, "reference_id": f"ref_{otp.id}", "message": "OTP sent successfully"}


@app.post("/auth/otp/verify")
@app.post("/auth/verify-otp")
def verify_otp(
    payload: OtpVerify,
    user: Optional[User] = Depends(current_user_optional),
    db: Session = Depends(get_session),
):
    query = select(OtpCode).where(
        OtpCode.code == payload.code,
        OtpCode.is_used == False,
        OtpCode.expires_at >= datetime.utcnow(),
    )
    otp = db.exec(query).first()
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp.is_used = True
    db.add(otp)

    if user:
        if otp.otp_type in ("email", "mail"):
            user.is_email_verified = True
        elif otp.otp_type in ("phone", "sms"):
            user.is_phone_verified = True
        db.add(user)

    db.commit()
    return {"status": "verified", "message": "OTP verified successfully"}


# ── Profiles ──────────────────────────────────────────────────────
@app.get("/profiles/seeker/me", response_model=SeekerProfileRead)
def get_seeker_profile(
    user: User = Depends(require_role(Role.SEEKER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(SeekerProfile).where(SeekerProfile.user_id == user.id)).first()
    if not profile:
        profile = SeekerProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@app.post("/profiles/seeker", response_model=SeekerProfileRead)
@app.put("/profiles/seeker", response_model=SeekerProfileRead)
@app.patch("/profiles/seeker", response_model=SeekerProfileRead)
def upsert_seeker_profile(
    payload: SeekerProfileUpsert,
    user: User = Depends(require_role(Role.SEEKER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(SeekerProfile).where(SeekerProfile.user_id == user.id)).first()
    if not profile:
        profile = SeekerProfile(user_id=user.id)

    if payload.gender is not None:
        profile.gender = payload.gender
    if payload.age_range is not None:
        profile.age_range = payload.age_range
    if payload.causes_csv is not None:
        profile.causes_csv = payload.causes_csv
    elif payload.causes is not None:
        profile.causes_csv = ",".join(payload.causes)
    if payload.visibility is not None:
        profile.visibility = payload.visibility
    if payload.alias and payload.alias.strip():
        user.display_name = payload.alias.strip()
        db.add(user)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/profiles/giver/me", response_model=GiverProfileRead)
def get_giver_profile(
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        profile = GiverProfile(user_id=user.id, is_available=True, is_verified=True)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@app.post("/profiles/giver", response_model=GiverProfileRead)
@app.put("/profiles/giver", response_model=GiverProfileRead)
@app.patch("/profiles/giver", response_model=GiverProfileRead)
def upsert_giver_profile(
    payload: GiverProfileUpsert,
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        profile = GiverProfile(user_id=user.id, is_available=True, is_verified=True)

    about_text = payload.about or payload.bio
    if about_text is not None:
        profile.about = about_text

    exp_text = payload.experience or (", ".join(payload.qualifications) if payload.qualifications else None)
    if exp_text is not None:
        profile.experience = exp_text

    if payload.is_available is not None:
        profile.is_available = payload.is_available
    if payload.name and payload.name.strip():
        user.display_name = payload.name.strip()
        db.add(user)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/givers/available", response_model=List[UserRead])
def list_available_givers(db: Session = Depends(get_session)):
    profiles = db.exec(select(GiverProfile).where(GiverProfile.is_available == True)).all()
    givers = []
    for p in profiles:
        user = db.get(User, p.user_id)
        if user:
            givers.append(user)
    return givers


@app.post("/givers/toggle-availability")
def toggle_giver_availability(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if user.role.value not in ("support_giver",):
        raise HTTPException(status_code=403, detail="Only Support Givers can toggle availability")
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        profile = GiverProfile(user_id=user.id, is_available=True, is_verified=True)
        db.add(profile)
    else:
        profile.is_available = not profile.is_available
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return {"status": "updated", "is_available": profile.is_available}


@app.get("/givers/availability")
def get_giver_availability(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if user.role.value not in ("support_giver",):
        return {"is_available": False}
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        profile = GiverProfile(user_id=user.id, is_available=True, is_verified=True)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return {"is_available": profile.is_available}


@app.get("/admin/givers/pending", response_model=List[GiverProfileRead])
def list_pending_givers(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    query = select(GiverProfile).where(GiverProfile.is_verified == False)
    return db.exec(query).all()


@app.post("/admin/givers/{giver_id}/verify")
def verify_giver(
    giver_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    profile = db.get(GiverProfile, giver_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Giver not found")
    profile.is_verified = True
    db.add(profile)
    db.commit()
    return {"status": "verified"}


# ── Matching Algorithm ────────────────────────────────────────────
def auto_match_giver(db: Session, cause: str | None = None, seeker_id: int | None = None) -> User | None:
    available_profiles = db.exec(
        select(GiverProfile).where(GiverProfile.is_available == True)
    ).all()
    if not available_profiles:
        return None

    candidates = []
    for profile in available_profiles:
        user = db.get(User, profile.user_id)
        if not user or user.role not in (Role.GIVER, Role.SUPPORT_GIVER):
            continue
        if seeker_id and user.id == seeker_id:
            continue

        score = 0
        if cause and profile.experience:
            cause_words = set(cause.lower().split())
            exp_words = set(profile.experience.lower().split())
            overlap = cause_words & exp_words
            if overlap:
                score += 30 + len(overlap) * 5
            active_count = db.exec(
            select(func.count(ChatSession.id)).where(
                ChatSession.giver_id == user.id,
                ChatSession.status == SessionStatus.ACTIVE
            )
        ).one()
        if active_count == 0:
            score += 20
        elif active_count == 1:
            score += 10

        avg_rating = db.exec(
            select(func.avg(Feedback.rating)).where(
                Feedback.submitted_by_user_id != user.id,
                Feedback.session_id.in_(
                    select(ChatSession.id).where(ChatSession.giver_id == user.id)
                )
            )
        ).one()
        if avg_rating:
            score += min(int(avg_rating * 3), 15)

        if profile.about and len(profile.about) > 20:
            score += 5

        candidates.append((score, user))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    top_score = candidates[0][0]
    top_givers = [c[1] for c in candidates if c[0] == top_score]
    return random.choice(top_givers)


# ── Sessions ──────────────────────────────────────────────────────
@app.post("/sessions/request", response_model=ChatSessionRead)
def request_session(
    payload: SessionRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if user.role.value not in ("support_seeker",):
        raise HTTPException(status_code=403, detail="Only Support Seekers can request a connection")
    giver = auto_match_giver(db, payload.cause, seeker_id=user.id)
    session = ChatSession(
        seeker_id=user.id,
        giver_id=giver.id if giver else None,
        cause=payload.cause,
        status=SessionStatus.ACTIVE if giver else SessionStatus.OPEN,
        is_ai_session=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.post("/sessions/request-ai", response_model=ChatSessionRead)
def request_ai_session(
    payload: SessionRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    # Any user can chat with AI
    session = ChatSession(
        seeker_id=user.id,
        giver_id=None,
        cause=payload.cause,
        status=SessionStatus.ACTIVE,
        is_ai_session=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.get("/sessions/active", response_model=List[ChatSessionRead])
def get_active_sessions(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if user.role in (Role.SEEKER, Role.SUPPORT_SEEKER):
        # For seekers: show ACTIVE and OPEN (waiting) sessions
        query = select(ChatSession).where(
            ChatSession.seeker_id == user.id,
            (ChatSession.status == SessionStatus.ACTIVE) | (ChatSession.status == SessionStatus.OPEN),
        ).order_by(ChatSession.created_at.desc())
    else:
        # For givers: show ACTIVE sessions
        query = select(ChatSession).where(
            ChatSession.giver_id == user.id,
            ChatSession.status == SessionStatus.ACTIVE,
        ).order_by(ChatSession.created_at.desc())
    return db.exec(query).all()


@app.get("/sessions/pending", response_model=List[ChatSessionRead])
def get_pending_sessions(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    # Givers see ALL open sessions to accept; seekers see their own open ones
    if user.role.value == "support_giver":
        query = select(ChatSession).where(ChatSession.status == SessionStatus.OPEN).order_by(ChatSession.created_at.desc())
    else:
        query = select(ChatSession).where(
            ChatSession.status == SessionStatus.OPEN,
            ChatSession.seeker_id == user.id
        ).order_by(ChatSession.created_at.desc())
    return db.exec(query).all()


@app.post("/sessions/{session_id}/accept", response_model=ChatSessionRead)
def accept_session(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if user.role.value not in ("support_giver",):
        raise HTTPException(status_code=403, detail="Only Support Givers can accept sessions")
    session = db.get(ChatSession, session_id)
    if not session or session.status != SessionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Session not available")
    session.giver_id = user.id
    session.status = SessionStatus.ACTIVE
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.post("/sessions/{session_id}/reject")
def reject_session(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = SessionStatus.CLOSED
    session.ended_at = datetime.utcnow()
    db.add(session)
    db.commit()
    return {"status": "rejected", "message": "Session closed"}


@app.post("/sessions/{session_id}/end", response_model=ChatSessionRead)
def end_session(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.seeker_id != user.id and session.giver_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    session.status = SessionStatus.CLOSED
    session.ended_at = datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.post("/sessions/{session_id}/messages", response_model=ChatMessageRead)
def send_message(
    session_id: int,
    payload: ChatMessageCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session not active")
    if session.seeker_id != user.id and session.giver_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    sender_label = "seeker" if user.id == session.seeker_id else "giver"
    msg = ChatMessage(
        session_id=session_id,
        sender_user_id=user.id,
        sender_label=sender_label,
        content=payload.content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@app.get("/sessions/{session_id}/messages", response_model=List[ChatMessageRead])
def get_messages(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.seeker_id != user.id and session.giver_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    query = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    return db.exec(query).all()


@app.post("/sessions/{session_id}/feedback")
@app.post("/feedback/{session_id}")
def submit_feedback(
    session_id: int,
    payload: FeedbackCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    comment = payload.comment or payload.comments
    feedback = Feedback(
        session_id=session_id,
        submitted_by_user_id=user.id,
        rating=payload.rating,
        comment=comment
    )
    db.add(feedback)
    db.commit()
    return {"status": "received", "message": "Feedback submitted successfully"}


@app.post("/reports")
def submit_report(
    payload: ReportCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    report = Report(
        session_id=payload.session_id,
        reported_by_user_id=user.id,
        reason=payload.reason,
        details=payload.details
    )
    db.add(report)
    db.commit()
    return {"status": "reported", "message": "Report submitted successfully"}


# ── Friends ───────────────────────────────────────────────────────
@app.post("/friends/request")
def create_friend_request(
    payload: FriendRequestCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    target_id = payload.receiver_id or payload.target_user_id
    if not target_id:
        raise HTTPException(status_code=400, detail="Target user ID required")
    if user.id == target_id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    req = FriendRequest(
        sender_id=user.id,
        receiver_id=target_id,
        session_id=payload.session_id
    )
    db.add(req)
    db.commit()
    return {"status": "requested", "message": "Friend request sent"}


@app.post("/friends/accept/{request_id}")
@app.put("/friends/{request_id}/respond")
def accept_friend_request(
    request_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    req = db.get(FriendRequest, request_id)
    if not req or req.receiver_id != user.id:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "accepted"
    db.add(req)
    db.commit()
    return {"status": "accepted", "message": "Friend request accepted"}


@app.get("/friends", response_model=List[UserRead])
def list_friends(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    sent_reqs = db.exec(
        select(FriendRequest).where(FriendRequest.sender_id == user.id, FriendRequest.status == "accepted")
    ).all()
    recv_reqs = db.exec(
        select(FriendRequest).where(FriendRequest.receiver_id == user.id, FriendRequest.status == "accepted")
    ).all()

    friend_ids = set([r.receiver_id for r in sent_reqs] + [r.sender_id for r in recv_reqs])
    friends = []
    for fid in friend_ids:
        f_user = db.get(User, fid)
        if f_user:
            friends.append(f_user)
    return friends


# ── Moods ─────────────────────────────────────────────────────────
@app.post("/moods", response_model=MoodRatingRead)
def submit_mood_rating(
    payload: MoodRatingCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    mood = MoodRating(
        user_id=user.id,
        session_id=payload.session_id,
        mood_before=payload.mood_before,
        mood_after=payload.mood_after
    )
    db.add(mood)
    db.commit()
    db.refresh(mood)
    return mood


@app.get("/moods/history", response_model=List[MoodRatingRead])
def get_mood_history(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    query = select(MoodRating).where(MoodRating.user_id == user.id).order_by(MoodRating.created_at.desc())
    return db.exec(query).all()


@app.get("/moods/average")
def get_average_mood(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    ratings = db.exec(select(MoodRating).where(MoodRating.user_id == user.id)).all()
    if not ratings:
        return {"average_score": 0.0}
    scores = [r.mood_before for r in ratings]
    avg = sum(scores) / len(scores)
    return {"average_score": round(avg, 2)}


@app.get("/crisis/resources")
def get_crisis_resources():
    return [
        {
            "name": "National Suicide Prevention Lifeline",
            "contact": "988",
            "description": "24/7, free and confidential support for people in distress.",
            "type": "phone",
        },
        {
            "name": "Crisis Text Line",
            "contact": "Text HOME to 741741",
            "description": "Free, 24/7 crisis support via text message.",
            "type": "text",
        },
        {
            "name": "The Trevor Project",
            "contact": "1-866-488-7386",
            "description": "Crisis intervention and suicide prevention services to LGBTQ young people.",
            "type": "phone",
        },
        {
            "name": "Veterans Crisis Line",
            "contact": "Dial 988 then press 1",
            "description": "24/7 confidential crisis support for Veterans and their loved ones.",
            "type": "phone",
        }
    ]


@app.get("/subscriptions/status", response_model=SubscriptionStatus)
def get_subscription_status(user: User = Depends(current_user)):
    return SubscriptionStatus(is_premium=user.is_premium, expires_at=None)


@app.post("/subscriptions/upgrade")
def upgrade_subscription(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    user.is_premium = True
    db.add(user)
    db.commit()
    return {"status": "upgraded", "message": "Upgraded to Premium successfully"}


# ── WebSockets ────────────────────────────────────────────────────
active_connections: Dict[int, List[WebSocket]] = {}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str | None = None,
    db: Session = Depends(get_session),
):
    await websocket.accept()
    if not token:
        await websocket.send_json({"type": "error", "message": "Authentication required"})
        await websocket.close(code=1008)
        return
    user = get_user_from_token(token, db)
    if not user:
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close(code=1008)
        return

    session = db.get(ChatSession, session_id)
    if not session or (session.seeker_id != user.id and session.giver_id != user.id):
        await websocket.send_json({"type": "error", "message": "Unauthorized for session"})
        await websocket.close(code=1008)
        return

    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(websocket)

    sender_label = "seeker" if user.id == session.seeker_id else "giver"

    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("{") and data.endswith("}"):
                import json
                try:
                    parsed = json.loads(data)
                    msg_type = parsed.get("type")
                    if msg_type == "typing":
                        for conn in active_connections[session_id]:
                            if conn != websocket:
                                await conn.send_json({"type": "typing", "user_id": user.id})
                        continue
                    elif msg_type == "read":
                        continue
                except Exception:
                    pass

            msg = ChatMessage(
                session_id=session_id,
                sender_user_id=user.id,
                sender_label=sender_label,
                content=data
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            for conn in active_connections[session_id]:
                await conn.send_json({
                    "id": msg.id,
                    "session_id": session_id,
                    "sender_user_id": user.id,
                    "sender_label": sender_label,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                })
    except WebSocketDisconnect:
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]


# ── AI Gemini Generation with Multi-Model Fallback ────────────────
@app.post("/sessions/{session_id}/ai-message", response_model=ChatMessageRead)
def generate_ai_reply(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session or not session.is_ai_session:
        raise HTTPException(status_code=400, detail="Not an active AI session")
    if session.seeker_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    messages = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    ).all()

    conversation_history = "\n".join(
        [f"{'Seeker' if m.sender_user_id == user.id else 'AI'}: {m.content}" for m in messages]
    )

    prompt = (
        f"Conversation so far:\n{conversation_history}\n\nPlease respond with empathy and care:"
    )

    api_key = os.getenv("GEMINI_API_KEY")
    ai_text = None

    system_prompt = (
        "You are a deeply compassionate, emotionally intelligent support companion in HearU — "
        "a safe space for people seeking emotional support. You have a profound understanding of human emotions "
        "and the complexity of the human experience. "
        "Your role is to listen actively, validate feelings without judgment, and respond with warmth and empathy. "
        "You never minimise someone's pain or rush to offer solutions. "
        "You reflect back what you hear, gently ask open-ended questions to help the person explore their feelings, "
        "and remind them they are not alone. "
        "If someone appears to be in crisis or expresses thoughts of self-harm, respond with deep care and "
        "gently guide them toward professional help and crisis resources. "
        "Never offer medical diagnoses or prescriptions. "
        "Speak in a warm, conversational, human tone — never clinical or robotic."
    )

    if api_key:
        try:
            # Try 3.7-flash first, fall back to 3.6-flash only
            for model_name in ["gemini-3.7-flash", "gemini-3.6-flash"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                resp = http_requests.post(
                    url,
                    json={
                        "system_instruction": {
                            "parts": [{"text": system_prompt}]
                        },
                        "contents": [{"parts": [{"text": prompt}]}],
                        "safetySettings": [
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        ],
                        "generationConfig": {
                            "temperature": 0.85,
                            "maxOutputTokens": 300,
                        },
                    },
                    timeout=20,
                )
                resp_data = resp.json()
                if "candidates" in resp_data and resp_data["candidates"]:
                    parts = resp_data["candidates"][0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        ai_text = parts[0]["text"].strip()
                        break
                elif "error" in resp_data:
                    err_msg = resp_data["error"].get("message", "unknown")
                    print(f"[GEMINI] {model_name} error: {err_msg}")
                    if model_name == "gemini-3.6-flash":
                        ai_text = f"I hear you and I care. (AI error: {err_msg})"
        except Exception as e:
            print(f"[GEMINI] Request failed: {e}")
            ai_text = f"I hear you and I care deeply. (AI temporarily unavailable: {type(e).__name__})"
    else:
        ai_text = "I'm here for you. Please set GEMINI_API_KEY in Render environment to enable live AI responses."

    ai_msg = ChatMessage(
        session_id=session_id,
        sender_user_id=None,
        sender_label="ai",
        content=ai_text
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    return ai_msg
