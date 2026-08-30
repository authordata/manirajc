import os
import random
from datetime import datetime, timedelta
from typing import Annotated, Dict, List

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func

from google import genai

from fastapi.responses import FileResponse
import pathlib

from .database import create_db_and_tables, get_session
from .models import (
    ChatMessage,
    ChatSession,
    Feedback,
    FriendRequest,
    GiverProfile,
    OtpCode,
    Report,
    Role,
    SeekerProfile,
    SessionStatus,
    User,
    MoodRating,
)
from .schemas import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatSessionRead,
    FeedbackCreate,
    FriendRequestCreate,
    GiverProfileCreate,
    GiverProfileRead,
    GiverProfileUpdate,
    LoginRequest,
    OtpRequest,
    OtpVerify,
    RegisterRequest,
    ReportCreate,
    SeekerProfileCreate,
    SeekerProfileRead,
    SeekerProfileUpdate,
    SessionRequest,
    TokenResponse,
    UserRead,
    MoodRatingCreate,
    MoodRatingRead,
)
from .security import create_access_token, decode_access_token, get_password_hash, verify_password

app = FastAPI(title="HearU API", version="0.1.0")

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
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = int(payload["sub"])
    return db.get(User, user_id)


def require_role(role: Role):
    def role_checker(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return role_checker


def require_admin(user: User = Depends(current_user)) -> User:
    # Admin check - currently no admin role, placeholder
    raise HTTPException(status_code=403, detail="Admin required")


def require_verified(user: User = Depends(current_user)) -> User:
    if not (user.is_email_verified or user.is_phone_verified):
        raise HTTPException(status_code=403, detail="Account not verified")
    return user


def current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_session),
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user



@app.get("/")
def root():
    # Serve the web frontend
    frontend_paths = [
        pathlib.Path(__file__).parent / "frontend" / "index.html",
        pathlib.Path(__file__).parent.parent / "frontend" / "index.html",
        pathlib.Path("/app/frontend/index.html"),
    ]
    for p in frontend_paths:
        if p.exists():
            return FileResponse(str(p), media_type="text/html")
    return {"app": "HearU", "docs": "/docs", "status": "running"}


@app.get("/health")
def healthcheck():
    return {"status": "ok", "service": "emotional-support-api"}


@app.get("/me")
@app.get("/users/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_anonymous": user.is_anonymous,
        "is_email_verified": user.is_email_verified,
        "is_phone_verified": user.is_phone_verified,
    }


@app.delete("/users/me")
def delete_me(user: User = Depends(current_user), db: Session = Depends(get_session)):
    db.delete(user)
    db.commit()
    return {"status": "deleted"}


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_session)):
    existing = db.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check display name uniqueness
    if payload.display_name:
        existing_name = db.exec(select(User).where(User.display_name == payload.display_name)).first()
        if existing_name:
            raise HTTPException(status_code=400, detail="Display name already taken. Please choose another.")
    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        display_name=payload.display_name or (f"Anonymous-{random.randint(1000, 9999)}" if payload.is_anonymous else "User"),
        role=payload.role,
        is_anonymous=payload.is_anonymous,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user.role == Role.SEEKER:
        db.add(SeekerProfile(user_id=user.id))
    elif user.role == Role.GIVER:
        db.add(GiverProfile(user_id=user.id))
    db.commit()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@app.post("/auth/anonymous", response_model=TokenResponse)
def create_anonymous_user(db: Session = Depends(get_session)):
    anon_id = random.randint(10000, 99999)
    user = User(
        email=f"anon_{anon_id}@hearu.local",
        password_hash=get_password_hash("anonymous"),
        display_name=f"Anonymous-{anon_id}",
        role=Role.SEEKER,
        is_anonymous=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(SeekerProfile(user_id=user.id))
    db.commit()
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@app.post("/auth/otp/send")
def send_otp(payload: OtpRequest, db: Session = Depends(get_session)):
    if not payload.otp_type:
        raise HTTPException(status_code=400, detail="Provide otp_type (email or phone)")
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    otp = OtpCode(
        user_id=user.id if "user" in dir() else 0,
        code=code,
        otp_type=payload.otp_type,
        expires_at=expires_at,
    )
    db.add(otp)
    db.commit()
    # In production, send via email/SMS. Return code here for MVP/testing.
    return {"status": "sent", "code": code}


@app.post("/auth/otp/verify")
def verify_otp(
    payload: OtpVerify,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    query = select(OtpCode).where(
        OtpCode.code == payload.code,
        OtpCode.is_used == False,
        OtpCode.expires_at >= datetime.utcnow(),
    )
    if payload.otp_type:
        query = query.where(OtpCode.otp_type == payload.otp_type)
    if False:
        query = query.where(OtpCode.user_id == user.id)
    otp = db.exec(query).first()
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    otp.is_used = True
    if payload.otp_type == "email":
        user.is_email_verified = True
    elif payload.otp_type == "phone":
        user.is_phone_verified = True
    db.add(otp)
    db.add(user)
    db.commit()
    return {"status": "verified"}


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
def create_seeker_profile(
    payload: SeekerProfileCreate,
    user: User = Depends(require_role(Role.SEEKER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(SeekerProfile).where(SeekerProfile.user_id == user.id)).first()
    if profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    profile = SeekerProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.patch("/profiles/seeker", response_model=SeekerProfileRead)
def update_seeker_profile(
    payload: SeekerProfileUpdate,
    user: User = Depends(require_role(Role.SEEKER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(SeekerProfile).where(SeekerProfile.user_id == user.id)).first()
    if not profile:
        profile = SeekerProfile(user_id=user.id)
        db.add(profile)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
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
        profile = GiverProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@app.post("/profiles/giver", response_model=GiverProfileRead)
def create_giver_profile(
    payload: GiverProfileCreate,
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    profile = GiverProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.patch("/profiles/giver", response_model=GiverProfileRead)
def update_giver_profile(
    payload: GiverProfileUpdate,
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        profile = GiverProfile(user_id=user.id)
        db.add(profile)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
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
            givers.append({"id": user.id, "display_name": user.display_name, "about": p.about})
    return givers


@app.post("/givers/toggle-availability")
def toggle_giver_availability(
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        profile = GiverProfile(user_id=user.id, is_available=True)
        db.add(profile)
    else:
        profile.is_available = not profile.is_available
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return {"status": "updated", "is_available": profile.is_available}


@app.get("/givers/availability")
def get_giver_availability(
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        return {"is_available": False}
    return {"is_available": profile.is_available}


@app.get("/admin/givers/pending", response_model=List[GiverProfileRead])
def list_pending_givers(
    user: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    query = select(GiverProfile).where(GiverProfile.is_verified == False)
    return db.exec(query).all()


@app.post("/admin/givers/{giver_id}/verify")
def verify_giver(
    giver_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    profile = db.get(GiverProfile, giver_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Giver not found")
    profile.is_verified = True
    db.add(profile)
    db.commit()
    return {"status": "verified"}


def auto_match_giver(db: Session, cause: str | None = None, seeker_id: int | None = None) -> User | None:
    """Smart matching algorithm for connecting seekers with the best giver.
    
    Priority:
    1. Experience match - giver whose experience matches the cause
    2. Least busy - giver with fewest active sessions
    3. Highest rated - giver with best average feedback rating
    4. Random fallback - any available giver
    """
    available_profiles = db.exec(
        select(GiverProfile).where(GiverProfile.is_available == True)
    ).all()
    if not available_profiles:
        return None

    # Build scored list of (score, user, profile)
    candidates = []
    for profile in available_profiles:
        user = db.get(User, profile.user_id)
        if not user or user.role not in (Role.GIVER, Role.SUPPORT_GIVER):
            continue
        # Don't match seeker with themselves
        if seeker_id and user.id == seeker_id:
            continue

        score = 0

        # Score 1: Experience keyword match (+30 points)
        if cause and profile.experience:
            cause_words = set(cause.lower().split())
            exp_words = set(profile.experience.lower().split())
            overlap = cause_words & exp_words
            if overlap:
                score += 30 + len(overlap) * 5

        # Score 2: Fewer active sessions = more available (+20 max)
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
        # More than 1 active session = no bonus

        # Score 3: Higher average rating (+15 max)
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

        # Score 4: About section filled out (+5 points)
        if profile.about and len(profile.about) > 20:
            score += 5

        candidates.append((score, user))

    if not candidates:
        return None

    # whisper
    # Sort by score descending, pick top candidate
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    # If top candidates have same score, pick randomly among them
    top_score = candidates[0][0]
    top_givers = [c[1] for c in candidates if c[0] == top_score]
    return random.choice(top_givers)


@app.post("/sessions/request", response_model=ChatSessionRead)
def request_session(
    payload: SessionRequest,
    user: User = Depends(require_role(Role.SEEKER)),
    db: Session = Depends(get_session),
):
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
    query = select(ChatSession).where(
        ChatSession.status == SessionStatus.ACTIVE,
        (ChatSession.seeker_id == user.id) | (ChatSession.giver_id == user.id),
    )
    return db.exec(query).all()


@app.get("/sessions/pending", response_model=List[ChatSessionRead])
def get_pending_sessions(
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    query = select(ChatSession).where(ChatSession.status == SessionStatus.OPEN)
    return db.exec(query).all()


@app.post("/sessions/{session_id}/accept", response_model=ChatSessionRead)
def accept_session(
    session_id: int,
    user: User = Depends(require_role(Role.GIVER)),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session or session.status != SessionStatus.OPEN:
        raise HTTPException(status_code=404, detail="Session not available")
    session.giver_id = user.id
    session.status = SessionStatus.ACTIVE
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


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

    msg = ChatMessage(session_id=session_id, sender_user_id=user.id, sender_label="seeker", content=payload.content)
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
def submit_feedback(
    session_id: int,
    payload: FeedbackCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.seeker_id != user.id and session.giver_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    feedback = Feedback(session_id=session_id, submitted_by_user_id=user.id, **payload.model_dump())
    db.add(feedback)
    db.commit()
    return {"status": "received"}


@app.post("/reports")
def submit_report(
    payload: ReportCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    report = Report(reported_by_user_id=user.id, **payload.model_dump())
    db.add(report)
    db.commit()
    return {"status": "reported"}


@app.post("/friends/request")
def create_friend_request(
    payload: FriendRequestCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if user.id == payload.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    req = FriendRequest(sender_id=user.id, receiver_id=payload.receiver_id)
    db.add(req)
    db.commit()
    return {"status": "requested"}


@app.post("/friends/accept/{request_id}")
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
    return {"status": "accepted"}


@app.get("/friends", response_model=List[UserRead])
def list_friends(
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    sent = db.exec(
        select(User)
        .join(FriendRequest, FriendRequest.receiver_id == User.id)
        .where(FriendRequest.sender_id == user.id, FriendRequest.status == "accepted")
    ).all()
    received = db.exec(
        select(User)
        .join(FriendRequest, FriendRequest.sender_id == User.id)
        .where(FriendRequest.receiver_id == user.id, FriendRequest.status == "accepted")
    ).all()
    return list(set(sent + received))


@app.post("/moods", response_model=MoodRatingRead)
def submit_mood_rating(
    payload: MoodRatingCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    mood = MoodRating(user_id=user.id, **payload.model_dump())
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
    query = select(func.avg(MoodRating.rating)).where(MoodRating.user_id == user.id)
    avg_score = db.exec(query).first()
    return {"average_score": avg_score or 0.0}


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

            msg = ChatMessage(session_id=session_id, sender_user_id=user.id, sender_label="seeker", content=data)
            db.add(msg)
            db.commit()
            db.refresh(msg)

            for conn in active_connections[session_id]:
                await conn.send_json({
                    "id": msg.id,
                    "session_id": session_id,
                    "sender_user_id": user.id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                })
    except WebSocketDisconnect:
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]


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
        "You are an empathetic, compassionate, and supportive emotional listener in an app called HearU. "
        "Your goal is to validate the user's feelings, offer comfort, and provide non-judgmental support. "
        "Do not offer medical advice. If the user appears in crisis, kindly remind them of professional help.\n\n"
        f"Conversation so far:\n{conversation_history}\n\nAI Response:"
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-05-20",
                contents=prompt,
            )
            ai_text = response.text
        except Exception as e:
            import traceback
            print(f"[GEMINI ERROR] {type(e).__name__}: {e}")
            traceback.print_exc()
            ai_text = f"I hear you and I want to help. (AI temporarily unavailable: {type(e).__name__})"
    else:
        print("[GEMINI] No GEMINI_API_KEY found in environment!")
        ai_text = "I'm here for you. Please set GEMINI_API_KEY in environment for AI responses."

    ai_msg = ChatMessage(session_id=session_id, sender_user_id=None, sender_label="ai", content=ai_text)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    return ai_msg
