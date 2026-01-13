-- SQLite schema for mood-aware recommendation system

-- User mood profile for current state tracking
CREATE TABLE IF NOT EXISTS user_mood_profile (
    user_id INTEGER PRIMARY KEY,
    current_mood TEXT NOT NULL,
    mood_last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wellness_score REAL DEFAULT 100.0,
    addiction_risk_score REAL DEFAULT 0.0
);

-- Historical log of all detected moods
CREATE TABLE IF NOT EXISTS mood_history (
    mood_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mood TEXT NOT NULL,
    confidence REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL, -- 'user_input' or 'inferred'
    FOREIGN KEY (user_id) REFERENCES user_mood_profile (user_id)
);

-- Track individual content watch sessions
CREATE TABLE IF NOT EXISTS watch_sessions (
    session_id TEXT PRIMARY KEY, -- f"sess_{user_id}_{content_id}_{timestamp}"
    user_id INTEGER NOT NULL,
    content_id INTEGER NOT NULL,
    mood_at_start TEXT NOT NULL,
    time_period TEXT NOT NULL, -- 'morning', 'afternoon', etc.
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT 0,
    user_satisfied BOOLEAN,
    FOREIGN KEY (user_id) REFERENCES user_mood_profile (user_id)
);

-- Daily aggregation of addiction and wellness metrics
CREATE TABLE IF NOT EXISTS addiction_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_watch_minutes INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    max_session_duration INTEGER DEFAULT 0,
    addiction_risk_score REAL DEFAULT 0.0,
    wellness_score REAL DEFAULT 100.0,
    break_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user_mood_profile (user_id),
    UNIQUE(user_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_mood_history_user ON mood_history(user_id);
CREATE INDEX IF NOT EXISTS idx_watch_sessions_user ON watch_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_addiction_metrics_user_date ON addiction_metrics(user_id, date);
