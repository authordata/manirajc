import os
import random
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func

import google.generativeai as genai

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
    AuthResponse,
    FeedbackCreate,
    FriendRequestCreate,
    FriendRequestRespond,
    GiverProfileUpsert,
    LoginRequest,
    MessageCreate,
    RegisterRequest,
    ReportCreate,
    SeekerProfileUpsert,
    SendOtpRequest,
    SessionRequest,
    VerifyOtpRequest,
    MoodCreate,
)
from .security import create_access_token, decode_access_token, hash_password, verify_password

app = FastAPI(title="Emotional Support Platform API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://hearu.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

CRISIS_KEYWORDS = ['suicide', 'kill myself', 'end my life', 'self-harm', 'want to die', 'hurt myself']

def check_crisis(content: str) -> bool:
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in CRISIS_KEYWORDS)

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
    return {"success": True}


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


@app.post("/auth/send-otp")
def send_otp(payload: SendOtpRequest, user: User = Depends(current_user), db: Session = Depends(get_session)):
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    otp = OtpCode(user_id=user.id, code=code, otp_type=payload.otp_type, expires_at=expires_at)
    db.add(otp)
    db.commit()
    print(f"OTP for user {user.id} ({payload.otp_type}): {code}")
    return {"success": True}


@app.post("/auth/verify-otp")
def verify_otp(payload: VerifyOtpRequest, user: User = Depends(current_user), db: Session = Depends(get_session)):
    otp = db.exec(
        select(OtpCode)
        .where(OtpCode.user_id == user.id)
        .where(OtpCode.otp_type == payload.otp_type)
        .where(OtpCode.code == payload.code)
        .where(OtpCode.is_used == False)
        .where(OtpCode.expires_at > datetime.utcnow())
        .order_by(OtpCode.id.desc())
    ).first()
    
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    otp.is_used = True
    db.add(otp)
    
    if payload.otp_type == 'phone':
        user.is_phone_verified = True
    else:
        user.is_email_verified = True
    db.add(user)
    db.commit()
    return {"success": True}


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

    chat_session = ChatSession(
        seeker_id=user.id,
        giver_id=None,  # No auto-assignment
        status=SessionStatus.OPEN,  # Always OPEN until giver accepts
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


@app.get("/sessions/pending")
def get_pending_sessions(user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Get all OPEN sessions waiting for a giver (giver dashboard)"""
    if user.role != Role.SUPPORT_GIVER:
        raise HTTPException(status_code=403, detail="Only givers can view pending sessions")
    sessions = db.exec(
        select(ChatSession).where(ChatSession.status == SessionStatus.OPEN)
        .order_by(ChatSession.created_at.desc())
    ).all()
    # Return session info with cause and seeker alias (not real name)
    result = []
    for s in sessions:
        result.append({
            "session_id": s.id,
            "cause": s.cause,
            "status": s.status,
            "created_at": str(s.created_at),
            "seeker_alias": f"Seeker #{s.seeker_id % 1000}",  # Anonymous alias
        })
    return result


@app.post("/sessions/{session_id}/accept")
def accept_session(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Giver accepts an open session"""
    if user.role != Role.SUPPORT_GIVER:
        raise HTTPException(status_code=403, detail="Only givers can accept sessions")
    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if chat_session.status != SessionStatus.OPEN:
        raise HTTPException(status_code=400, detail="Session is no longer open")
    if chat_session.giver_id is not None:
        raise HTTPException(status_code=400, detail="Session already has a giver")
    
    chat_session.giver_id = user.id
    chat_session.status = SessionStatus.ACTIVE
    db.add(chat_session)
    db.commit()
    
    # Add a system message
    system_msg = ChatMessage(
        session_id=session_id,
        sender_user_id=None,
        sender_label="system",
        content="A support giver has joined the session. You can now chat.",
    )
    db.add(system_msg)
    db.commit()
    
    return {"success": True, "session_id": session_id, "status": "active"}


@app.post("/sessions/{session_id}/reject")
def reject_session(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Giver rejects/passes on an open session"""
    # Just return success - session stays open for other givers
    return {"success": True, "message": "Session passed"}


@app.post("/givers/toggle-availability")
def toggle_availability(user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Toggle giver's availability status"""
    if user.role != Role.SUPPORT_GIVER:
        raise HTTPException(status_code=403, detail="Only givers can toggle availability")
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Giver profile not found")
    profile.is_available = not profile.is_available
    db.add(profile)
    db.commit()
    return {"success": True, "is_available": profile.is_available}


@app.get("/givers/availability")
def get_availability(user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Get giver's current availability"""
    if user.role != Role.SUPPORT_GIVER:
        raise HTTPException(status_code=403, detail="Only givers")
    profile = db.exec(select(GiverProfile).where(GiverProfile.user_id == user.id)).first()
    return {"is_available": profile.is_available if profile else False}


@app.get("/sessions/active")
def get_active_sessions(user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Get all active sessions for the current user (both seekers and givers)"""
    if user.role == Role.SUPPORT_SEEKER:
        sessions = db.exec(
            select(ChatSession).where(
                ChatSession.seeker_id == user.id,
                ChatSession.status.in_([SessionStatus.ACTIVE, SessionStatus.OPEN])
            ).order_by(ChatSession.created_at.desc())
        ).all()
    else:
        sessions = db.exec(
            select(ChatSession).where(
                ChatSession.giver_id == user.id,
                ChatSession.status == SessionStatus.ACTIVE
            ).order_by(ChatSession.created_at.desc())
        ).all()
    
    result = []
    for s in sessions:
        # Get last message preview
        last_msg = db.exec(
            select(ChatMessage).where(ChatMessage.session_id == s.id)
            .order_by(ChatMessage.created_at.desc())
        ).first()
        result.append({
            "session_id": s.id,
            "cause": s.cause,
            "status": s.status,
            "is_ai_session": s.is_ai_session,
            "created_at": str(s.created_at),
            "last_message": last_msg.content[:50] if last_msg else None,
            "last_message_time": str(last_msg.created_at) if last_msg else None,
        })
    return result


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
    
    crisis_detected = check_crisis(payload.content)
    if crisis_detected:
        crisis_message = ChatMessage(
            session_id=session_id,
            sender_user_id=None,
            sender_label="system",
            content="Crisis detected. Please reach out to an emergency hotline: 988 (US) or your local emergency services."
        )
        db.add(crisis_message)

    db.commit()
    db.refresh(message)

    return {"id": message.id, "created_at": message.created_at, "crisis_detected": crisis_detected}


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
    
    crisis_detected = check_crisis(payload.content)
    if crisis_detected:
        reply = "Crisis detected. Please reach out to an emergency hotline: 988 (US) or your local emergency services."
    else:
        reply = (
            "I hear you. Thank you for sharing this. "
            "Would you like grounding tips, reflective questions, or to continue venting?"
        )
        
        if GEMINI_API_KEY:
            try:
                # Get last 10 messages before the current one to build history
                past_messages = db.exec(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(10)
                ).all()
                
                past_messages.reverse()
                
                history = []
                for msg in past_messages:
                    role = "user" if msg.sender_label == "seeker" else "model"
                    # skip system messages if any, or map them to model
                    if msg.sender_label == "system":
                        continue
                    history.append({"role": role, "parts": [msg.content]})
                    
                sys_instruct = (
                    "You are HearU, a compassionate AI emotional support companion created to help people through difficult moments. \n\n"
                    "Guidelines:\n"
                    "- Listen with deep empathy and validate feelings\n"
                    "- Offer gentle coping strategies (breathing exercises, grounding techniques, journaling prompts)\n"
                    "- Keep responses warm, concise (2-3 sentences), and supportive\n"
                    "- You are NOT a therapist or medical professional - remind users to seek professional help for serious issues\n"
                    "- Never diagnose conditions, prescribe medication, or provide medical advice\n"
                    "- If someone mentions self-harm or suicide, immediately provide crisis resources (988 Lifeline)\n"
                    "- Remember context from the conversation to provide continuity\n"
                    "- Use the person's emotional state to guide your response tone\n"
                    "- Suggest professional resources when appropriate"
                )
                
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash-preview-05-20",
                    system_instruction=sys_instruct
                )
                
                chat = model.start_chat(history=history)
                response = chat.send_message(payload.content)
                reply = response.text
            except Exception as e:
                print(f"Gemini API error: {e}")

    ai_response = ChatMessage(
        session_id=session_id,
        sender_user_id=None,
        sender_label="ai_bot" if not crisis_detected else "system",
        content=reply,
    )
    db.add(ai_response)
    db.commit()

    return {"reply": reply, "crisis_detected": crisis_detected}


@app.post("/sessions/{session_id}/mood")
def add_mood(
    session_id: int,
    payload: MoodCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if payload.mood_before < 1 or payload.mood_before > 5:
        raise HTTPException(status_code=400, detail="Mood rating must be 1-5")
    if payload.mood_after is not None and (payload.mood_after < 1 or payload.mood_after > 5):
        raise HTTPException(status_code=400, detail="Mood rating must be 1-5")

    mood = db.exec(
        select(MoodRating)
        .where(MoodRating.session_id == session_id)
        .where(MoodRating.user_id == user.id)
    ).first()
    
    if mood:
        mood.mood_before = payload.mood_before
        mood.mood_after = payload.mood_after
    else:
        mood = MoodRating(
            session_id=session_id,
            user_id=user.id,
            mood_before=payload.mood_before,
            mood_after=payload.mood_after
        )
    db.add(mood)
    db.commit()
    db.refresh(mood)
    return mood


@app.get("/sessions/{session_id}/mood")
def get_mood(
    session_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    moods = db.exec(
        select(MoodRating)
        .where(MoodRating.session_id == session_id)
    ).all()
    return moods


@app.get("/analytics/sessions")
def get_sessions_analytics(db: Session = Depends(get_session)):
    total_sessions = db.exec(select(func.count(ChatSession.id))).one()
    avg_rating = db.exec(select(func.avg(Feedback.rating))).one() or 0.0
    
    moods = db.exec(
        select(MoodRating)
        .where(MoodRating.mood_after != None)
    ).all()
    
    mood_improvement = 0.0
    if moods:
        total_diff = sum(m.mood_after - m.mood_before for m in moods if m.mood_after is not None)
        mood_improvement = total_diff / len(moods)
        
    return {
        "total_sessions": total_sessions,
        "avg_rating": float(avg_rating),
        "avg_mood_improvement": float(mood_improvement)
    }

@app.get("/analytics/givers/leaderboard")
def get_givers_leaderboard(db: Session = Depends(get_session)):
    sessions = db.exec(select(ChatSession).where(ChatSession.giver_id != None)).all()
    feedbacks = db.exec(select(Feedback)).all()
    
    giver_stats = {}
    for s in sessions:
        if s.giver_id not in giver_stats:
            giver_stats[s.giver_id] = {"session_count": 0, "ratings": []}
        giver_stats[s.giver_id]["session_count"] += 1
        
    for f in feedbacks:
        s = db.get(ChatSession, f.session_id)
        if s and s.giver_id:
            if s.giver_id not in giver_stats:
                giver_stats[s.giver_id] = {"session_count": 0, "ratings": []}
            giver_stats[s.giver_id]["ratings"].append(f.rating)
            
    leaderboard = []
    for g_id, stats in giver_stats.items():
        avg_rating = sum(stats["ratings"]) / len(stats["ratings"]) if stats["ratings"] else 0.0
        leaderboard.append({
            "giver_id": g_id,
            "session_count": stats["session_count"],
            "avg_rating": avg_rating
        })
        
    leaderboard.sort(key=lambda x: (x["avg_rating"], x["session_count"]), reverse=True)
    return leaderboard


@app.get("/sessions/{session_id}/messages")
def list_messages(
    session_id: int,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if user.id not in [chat_session.seeker_id, chat_session.giver_id]:
        raise HTTPException(status_code=403, detail="Not authorized")

    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .offset(offset)
        .limit(limit)
    ).all()
    
    aliases = ["Blue Penguin", "Gentle Cloud", "Happy Tiger", "Silver Fox", "Golden Eagle"]
    def get_alias(u_id: int):
        return aliases[u_id % len(aliases)]
        
    are_friends = False
    if not chat_session.is_ai_session and chat_session.giver_id:
        other_id = chat_session.giver_id if user.id == chat_session.seeker_id else chat_session.seeker_id
        fr = db.exec(
            select(FriendRequest).where(
                (((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == other_id)) | \
                 ((FriendRequest.sender_id == other_id) & (FriendRequest.receiver_id == user.id))) & \
                (FriendRequest.status == "accepted")
            )
        ).first()
        if fr:
            are_friends = True

    response_messages = []
    for msg in messages:
        msg_dict = msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict()
        if msg.sender_user_id is not None:
            if msg.sender_user_id == user.id or are_friends:
                msg_dict["sender_alias"] = None
            else:
                msg_dict["sender_user_id"] = None
                msg_dict["sender_alias"] = get_alias(msg.sender_user_id)
        else:
            msg_dict["sender_alias"] = "AI"
        response_messages.append(msg_dict)
    
    return response_messages


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


@app.post("/friends/request")
def send_friend_request(
    payload: FriendRequestCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    chat_session = db.get(ChatSession, payload.session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if user.id not in [chat_session.seeker_id, chat_session.giver_id]:
        raise HTTPException(status_code=403, detail="Not part of this session")
        
    if payload.receiver_id not in [chat_session.seeker_id, chat_session.giver_id] or payload.receiver_id == user.id:
        raise HTTPException(status_code=400, detail="Invalid receiver")

    existing = db.exec(
        select(FriendRequest).where(
            (FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == payload.receiver_id)
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Request already sent")
        
    fr = FriendRequest(sender_id=user.id, receiver_id=payload.receiver_id, session_id=payload.session_id)
    db.add(fr)
    db.commit()
    return {"success": True, "request_id": fr.id}


@app.put("/friends/{request_id}/respond")
def respond_friend_request(
    request_id: int,
    payload: FriendRequestRespond,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
):
    if payload.status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    fr = db.get(FriendRequest, request_id)
    if not fr or fr.receiver_id != user.id:
        raise HTTPException(status_code=404, detail="Request not found")
        
    fr.status = payload.status
    db.add(fr)
    db.commit()
    return {"success": True}


@app.get("/friends")
def list_friends(user: User = Depends(current_user), db: Session = Depends(get_session)):
    requests = db.exec(
        select(FriendRequest).where(
            ((FriendRequest.sender_id == user.id) | (FriendRequest.receiver_id == user.id)) & \
            (FriendRequest.status == "accepted")
        )
    ).all()
    
    friends = []
    for r in requests:
        friend_id = r.receiver_id if r.sender_id == user.id else r.sender_id
        friends.append({"friend_id": friend_id, "session_id": r.session_id})
        
    return friends


@app.post("/subscriptions/upgrade")
def upgrade_to_premium(user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Upgrade user to premium tier (verified listeners, priority matching)"""
    user.is_premium = True
    db.add(user)
    db.commit()
    return {"success": True, "tier": "premium", "message": "Welcome to HearU Premium!"}

@app.get("/subscriptions/status")
def subscription_status(user: User = Depends(current_user)):
    """Check user's subscription status"""
    return {
        "is_premium": getattr(user, 'is_premium', False),
        "tier": "premium" if getattr(user, 'is_premium', False) else "free",
        "features": {
            "verified_listeners": getattr(user, 'is_premium', False),
            "priority_matching": getattr(user, 'is_premium', False),
            "session_history": True,
            "ai_support": True,
            "crisis_support": True
        }
    }
