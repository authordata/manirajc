# HearU - Emotional Support Platform App

This is a runnable starter app for HearU, an emotional support platform connecting:

- Support seekers (with anonymity options)
- Support givers (volunteer profiles + availability)
- AI support chatbot sessions

## Project structure

- `backend/` FastAPI backend and data models
- `frontend/` Web app (HTML/CSS/JS)
- `android/` Native Kotlin starter with API contracts
- `docs/` Product specification and database schema

## Quick start (trial run)

### 1) Start backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2) Start frontend app

```bash
python -m http.server 5173 --directory frontend
```

Open: `http://localhost:5173`

### 3) Run automated backend tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```
