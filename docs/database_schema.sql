CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('support_seeker','support_giver')),
  display_name TEXT NOT NULL,
  is_anonymous BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL
);

CREATE TABLE seeker_profiles (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  gender TEXT,
  age_range TEXT,
  causes_csv TEXT,
  visibility TEXT NOT NULL DEFAULT 'private'
);

CREATE TABLE giver_profiles (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  about TEXT,
  experience TEXT,
  is_available BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE chat_sessions (
  id INTEGER PRIMARY KEY,
  seeker_id INTEGER NOT NULL REFERENCES users(id),
  giver_id INTEGER REFERENCES users(id),
  is_ai_session BOOLEAN NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('open','active','closed')),
  cause TEXT,
  created_at DATETIME NOT NULL,
  ended_at DATETIME
);

CREATE TABLE chat_messages (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES chat_sessions(id),
  sender_user_id INTEGER REFERENCES users(id),
  sender_label TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME NOT NULL
);

CREATE TABLE feedback (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES chat_sessions(id),
  submitted_by_user_id INTEGER NOT NULL REFERENCES users(id),
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  created_at DATETIME NOT NULL
);

CREATE TABLE reports (
  id INTEGER PRIMARY KEY,
  session_id INTEGER REFERENCES chat_sessions(id),
  reported_by_user_id INTEGER NOT NULL REFERENCES users(id),
  reason TEXT NOT NULL,
  details TEXT,
  created_at DATETIME NOT NULL
);
