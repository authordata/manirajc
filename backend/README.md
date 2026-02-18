# Backend API (FastAPI)

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Trial run (API)

```bash
# register seeker
curl -s -X POST http://localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"trial@example.com","password":"Password123!","display_name":"Trial","role":"support_seeker","is_anonymous":true}'

# create AI session + send AI message (with token from previous output)
```

## Key endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /me`
- `PUT /profiles/seeker`
- `PUT /profiles/giver`
- `POST /sessions/request`
- `POST /sessions/request-ai`
- `GET /sessions`
- `POST /sessions/{id}/messages`
- `POST /sessions/{id}/ai-message`
- `GET /sessions/{id}/messages`
- `POST /sessions/{id}/end`
- `POST /feedback/{session_id}`
- `POST /reports`

## Notes
- Uses SQLite by default; replace database URL for PostgreSQL in production.
- Token auth is bearer JWT and should be replaced with secure secrets + refresh flow.
