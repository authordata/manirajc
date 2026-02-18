from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import (
    ChatMessage,
    ChatSession,
    Feedback,
    GiverProfile,
    Report,
    Role,
    SeekerProfile,
    SessionStatus,
    User,
)
from .schemas import (
    AuthResponse,
    FeedbackCreate,
    GiverProfileUpsert,
    LoginRequest,
    MessageCreate,
    RegisterRequest,
    ReportCreate,
    SeekerProfileUpsert,
    SessionRequest,
)
from .security import create_access_token, decode_access_token, hash_password, verify_password

app = FastAPI(title="Emotional Support Platform API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    create_db_and_tables()


def current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", maxsplit=1)[1]
    try:
        user_id = int(decode_access_token(token))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/health")
def healthcheck():
    return {"status": "ok", "service": "emotional-support-api"}


@app.get("/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_anonymous": user.is_anonymous,
    }


@app.post("/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        display_name=payload.display_name,
        is_anonymous=payload.is_anonymous,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    if user.role == Role.SUPPORT_SEEKER:
        session.add(SeekerProfile(user_id=user.id))
    else:
        session.add(GiverProfile(user_id=user.id))
    session.commit()

    return AuthResponse(access_token=create_access_token(str(user.id)))


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(access_token=create_access_token(str(user.id)))


@app.put("/profiles/seeker")
def upsert_seeker_profile(
    payload: SeekerProfileUpsert,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if user.role != Role.SUPPORT_SEEKER:
        raise HTTPException(status_code=403, detail="Role not allowed")

    profile = session.exec(select(SeekerProfile).where(SeekerProfile.user_id == user.id)).first()
    if not profile:
        profile = SeekerProfile(user_id=user.id)

    profile.gender = payload.gender
    profile.age_range = payload.age_range
    profile.causes_csv = payload.causes_csv
    profile.visibility = payload.visibility

    session.add(profile)
    session.commit()
    return {"success": True}


@app.put("/profiles/giver")
def upsert_giver_profile(
    payload: GiverProfileUpsert,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if user.role != Role.SUPPORT_GIVER:
        raise HTTPException(status_code=403, detail="Role not allowed")

    profile = session.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        profile = GiverProfile(user_id=user.id)

    profile.about = payload.about
    profile.experience = payload.experience
    profile.is_available = payload.is_available

    session.add(profile)
    session.commit()
    return {"success": True}


@app.post("/sessions/request")
def request_human_session(
    payload: SessionRequest,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if user.role != Role.SUPPORT_SEEKER:
        raise HTTPException(status_code=403, detail="Only seekers can request support")

    available_giver = session.exec(
        select(GiverProfile).where(GiverProfile.is_available.is_(True))
    ).first()

    chat_session = ChatSession(
        seeker_id=user.id,
        giver_id=available_giver.user_id if available_giver else None,
        status=SessionStatus.ACTIVE if available_giver else SessionStatus.OPEN,
        cause=payload.cause,
    )
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    return {
        "session_id": chat_session.id,
        "status": chat_session.status,
        "giver_assigned": chat_session.giver_id,
        "is_ai_session": False,
    }


@app.post("/sessions/request-ai")
def request_ai_session(
    payload: SessionRequest,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if user.role != Role.SUPPORT_SEEKER:
        raise HTTPException(status_code=403, detail="Only seekers can request AI support")

    chat_session = ChatSession(
        seeker_id=user.id,
        giver_id=None,
        is_ai_session=True,
        status=SessionStatus.ACTIVE,
        cause=payload.cause,
    )
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return {
        "session_id": chat_session.id,
        "status": chat_session.status,
        "giver_assigned": None,
        "is_ai_session": True,
    }


@app.get("/sessions")
def list_sessions(user: User = Depends(current_user), db: Session = Depends(get_session)):
    if user.role == Role.SUPPORT_SEEKER:
        query = select(ChatSession).where(ChatSession.seeker_id == user.id)
    else:
        query = select(ChatSession).where(ChatSession.giver_id == user.id)

    return db.exec(query.order_by(ChatSession.created_at.desc())).all()


@app.post("/sessions/{session_id}/messages")
def send_message(
    session_id: int,
    payload: MessageCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if user.id not in [chat_session.seeker_id, chat_session.giver_id]:
        raise HTTPException(status_code=403, detail="Not part of this session")

    sender_label = "seeker" if user.id == chat_session.seeker_id else "giver"
    message = ChatMessage(
        session_id=session_id,
        sender_user_id=user.id,
        sender_label=sender_label,
        content=payload.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {"id": message.id, "created_at": message.created_at}


@app.post("/sessions/{session_id}/ai-message")
def ai_message(
    session_id: int,
    payload: MessageCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    chat_session = db.get(ChatSession, session_id)
    if not chat_session or not chat_session.is_ai_session:
        raise HTTPException(status_code=404, detail="AI session not found")

    if user.id != chat_session.seeker_id:
        raise HTTPException(status_code=403, detail="Only seeker can use this AI session")

    user_message = ChatMessage(
        session_id=session_id,
        sender_user_id=user.id,
        sender_label="seeker",
        content=payload.content,
    )
    db.add(user_message)

    reply = (
        "I hear you. Thank you for sharing this. "
        "Would you like grounding tips, reflective questions, or to continue venting?"
    )
    ai_response = ChatMessage(
        session_id=session_id,
        sender_user_id=None,
        sender_label="ai_bot",
        content=reply,
    )
    db.add(ai_response)
    db.commit()

    return {"reply": reply}


@app.get("/sessions/{session_id}/messages")
def list_messages(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if user.id not in [chat_session.seeker_id, chat_session.giver_id]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if chat_session.is_ai_session and user.id == chat_session.seeker_id:
        pass

    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()

    return messages


@app.post("/sessions/{session_id}/end")
def end_session(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if user.id not in [chat_session.seeker_id, chat_session.giver_id]:
        raise HTTPException(status_code=403, detail="Not authorized")

    chat_session.status = SessionStatus.CLOSED
    chat_session.ended_at = datetime.utcnow()
    db.add(chat_session)
    db.commit()
    return {"success": True}


@app.post("/feedback/{session_id}")
def submit_feedback(
    session_id: int,
    payload: FeedbackCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    feedback = Feedback(
        session_id=session_id,
        submitted_by_user_id=user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    return {"success": True}


@app.post("/reports")
def create_report(
    payload: ReportCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    report = Report(
        session_id=payload.session_id,
        reported_by_user_id=user.id,
        reason=payload.reason,
        details=payload.details,
    )
    db.add(report)
    db.commit()
    return {"success": True}
