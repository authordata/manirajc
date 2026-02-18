# Product Specification (V1)

## Vision
Provide a safe emotional support platform where users can choose:
- Human support from a volunteer support giver.
- A private, customizable AI chatbot.

## Goals
- Safe and accessible emotional support.
- Private and anonymous support-seeker experiences.
- Expandable architecture to onboard licensed professionals in later phases.

## User roles
- `support_seeker`
- `support_giver`
- `admin` (future)

## Functional scope

### Onboarding
- Email + password auth (social/phone can be added).
- Role selection at account setup.
- Optional seeker profile fields:
  - gender
  - age range
  - support causes
  - anonymity toggle
- Giver profile fields:
  - about me
  - experience
  - availability status

### Matching and chat
- Seeker can request a session by cause tags.
- System assigns currently available giver (simple queue in V1).
- Real-time is represented by polling API in this starter.
- AI chat route available as fallback.

### Safety
- Post-chat feedback score + optional text.
- Reporting endpoint for abuse/safety concerns.

## Non-functional requirements
- Role-based authorization checks.
- Event timestamps on all records.
- PII minimization + seeker anonymity in peer views.
- Ready for migration from SQLite to PostgreSQL.

## V2 roadmap
- WebSocket real-time chat.
- Content moderation + toxicity scoring.
- Licensed therapist program + paid sessions.
- Push notifications + scheduling.
