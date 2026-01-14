"""AntiAddictionModule

Tracks watch sessions, computes addiction risk, and provides break
recommendations and throttling guidance.
"""
from __future__ import annotations

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import math

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AntiAddictionModule:
    """Module for tracking watch behavior and computing addiction metrics.

    Stores sessions and daily aggregates in SQLite. Methods are defensive
    and return informative dicts for API usage.
    """

    DAILY_WATCH_GOAL = 120  # minutes
    BREAK_INTERVAL = 30     # minutes
    BINGE_THRESHOLD = 180   # minutes
    CRITICAL_THRESHOLD = 300

    def __init__(self, db_path: str = "recommendation.db") -> None:
        self.db_path = db_path
        self.initialize_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self) -> None:
        """Create required tables if they don't exist."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS watch_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    content_id INTEGER NOT NULL,
                    mood_at_start TEXT,
                    time_period TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_minutes INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0,
                    user_satisfied INTEGER DEFAULT 0
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS addiction_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    total_watch_minutes INTEGER DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    max_session_duration INTEGER DEFAULT 0,
                    addiction_risk_score REAL DEFAULT 0.0,
                    wellness_score REAL DEFAULT 100.0,
                    break_count INTEGER DEFAULT 0,
                    UNIQUE(user_id, date)
                )
                """
            )

            cur.execute("CREATE INDEX IF NOT EXISTS idx_ws_user ON watch_sessions(user_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_am_user_date ON addiction_metrics(user_id, date);")
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error("Error initializing AntiAddiction DB: %s", e)

    def _today_str(self, date: Optional[str] = None) -> str:
        if date:
            return date
        return datetime.utcnow().date().isoformat()

    def start_watch_session(self, user_id: int, content_id: int, mood: str, time_period: str) -> str:
        """Start a new watch session and return its session_id."""
        try:
            ts = int(datetime.utcnow().timestamp())
            session_id = f"sess_{user_id}_{content_id}_{ts}"
            start_time = datetime.utcnow().isoformat()
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO watch_sessions (session_id, user_id, content_id, mood_at_start, time_period, start_time) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, user_id, content_id, mood, time_period, start_time),
            )
            conn.commit()
            conn.close()
            return session_id
        except sqlite3.Error as e:
            logger.error("Error starting session: %s", e)
            raise

    def update_watch_progress(self, session_id: str, duration_minutes: int) -> Dict[str, Any]:
        """Update session progress and check for break recommendation.

        Returns dict with should_break, addiction_score, message, break_recommendation
        """
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT user_id, duration_minutes FROM watch_sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            if row is None:
                conn.close()
                return {"error": "session_not_found"}

            user_id = int(row["user_id"])
            cur.execute("UPDATE watch_sessions SET duration_minutes = ? WHERE session_id = ?", (int(duration_minutes), session_id))
            conn.commit()

            # compute addiction score for user today
            today = self._today_str()
            score = self.get_addiction_risk_score(user_id, today)

            should_break = (duration_minutes > 0 and duration_minutes % self.BREAK_INTERVAL == 0)
            message = "Keep watching" if not should_break else "Time for a break"
            rec = None
            if should_break:
                rec = {
                    "duration": duration_minutes,
                    "message": "You should take a short break.",
                    "addiction_score": score,
                    "activity_suggestion": "Stand up, stretch, grab water"
                }

            conn.close()
            return {"should_break": should_break, "addiction_score": score, "message": message, "break_recommendation": rec}
        except sqlite3.Error as e:
            logger.error("Error updating session: %s", e)
            return {"error": str(e)}

    def end_watch_session(self, session_id: str, user_id: int, user_satisfied: bool) -> Dict[str, Any]:
        """End a session and update daily aggregates.

        Returns session stats and updated addiction score.
        """
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT duration_minutes, start_time FROM watch_sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id))
            row = cur.fetchone()
            if row is None:
                conn.close()
                return {"error": "session_not_found"}

            duration = int(row["duration_minutes"] or 0)
            end_time = datetime.utcnow().isoformat()
            cur.execute("UPDATE watch_sessions SET end_time = ?, completed = 1, user_satisfied = ? WHERE session_id = ?", (end_time, int(bool(user_satisfied)), session_id))

            # update addiction_metrics for today
            today = self._today_str()
            cur.execute("SELECT metric_id, total_watch_minutes, session_count, max_session_duration, break_count FROM addiction_metrics WHERE user_id = ? AND date = ?", (user_id, today))
            mrow = cur.fetchone()
            if mrow is None:
                cur.execute("INSERT INTO addiction_metrics (user_id, date, total_watch_minutes, session_count, max_session_duration, break_count) VALUES (?, ?, ?, ?, ?, ?)", (user_id, today, duration, 1, duration, 0))
            else:
                total = int(mrow["total_watch_minutes"] or 0) + duration
                scnt = int(mrow["session_count"] or 0) + 1
                maxd = max(int(mrow["max_session_duration"] or 0), duration)
                bcount = int(mrow["break_count"] or 0)
                cur.execute("UPDATE addiction_metrics SET total_watch_minutes = ?, session_count = ?, max_session_duration = ? WHERE metric_id = ?", (total, scnt, maxd, int(mrow["metric_id"])))

            conn.commit()

            # recompute addiction score and store
            score = self.get_addiction_risk_score(user_id, today)
            wellness = 100.0 - score
            # update stored score
            cur.execute("UPDATE addiction_metrics SET addiction_risk_score = ?, wellness_score = ? WHERE user_id = ? AND date = ?", (score, wellness, user_id, today))
            conn.commit()

            conn.close()
            return {"session_id": session_id, "duration": duration, "addiction_score": score, "wellness_score": wellness}
        except sqlite3.Error as e:
            logger.error("Error ending session: %s", e)
            return {"error": str(e)}

    def _compute_binge_factor(self, max_session_duration: int) -> float:
        """Return binge factor (0-100) based on max session duration."""
        if max_session_duration < 60:
            return 0.0
        if max_session_duration < 180:
            return 50.0
        if max_session_duration < 300:
            return 80.0
        return 100.0

    def _unhealthy_hours_factor(self, user_id: int, date: Optional[str] = None) -> float:
        """Return 50 if any watch took place after 23:00 on the date, else 0."""
        try:
            d = self._today_str(date)
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT start_time, end_time FROM watch_sessions WHERE user_id = ? AND date(start_time) = ?", (user_id, d))
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                st = r["start_time"]
                if not st:
                    continue
                try:
                    hr = datetime.fromisoformat(st).hour
                except Exception:
                    continue
                if hr >= 23 or hr < 6:
                    return 50.0
            return 0.0
        except sqlite3.Error as e:
            logger.error("Error computing unhealthy hours: %s", e)
            return 0.0

    def get_addiction_risk_score(self, user_id: int, date: Optional[str] = None) -> float:
        """Compute addiction risk score (0-100) for user on given date."""
        try:
            d = self._today_str(date)
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT total_watch_minutes, session_count, max_session_duration FROM addiction_metrics WHERE user_id = ? AND date = ?", (user_id, d))
            row = cur.fetchone()
            conn.close()

            total_minutes = int(row["total_watch_minutes"] or 0) if row else 0
            session_count = int(row["session_count"] or 0) if row else 0
            max_session = int(row["max_session_duration"] or 0) if row else 0

            # Factor 1: Time vs Goal (40%)
            f1 = min(100.0, (total_minutes / float(self.DAILY_WATCH_GOAL)) * 100.0) if self.DAILY_WATCH_GOAL > 0 else 0.0

            # Factor 2: Session Frequency (30%): (session_count / 5) * 100
            f2 = min(100.0, (session_count / 5.0) * 100.0)

            # Factor 3: Binge Patterns (20%)
            f3 = self._compute_binge_factor(max_session)

            # Factor 4: Unhealthy Hours (10%)
            f4 = self._unhealthy_hours_factor(user_id, d)

            total = (f1 * 0.4) + (f2 * 0.3) + (f3 * 0.2) + (f4 * 0.1)
            total = max(0.0, min(100.0, total))
            return round(float(total), 2)
        except Exception as e:
            logger.error("Error computing addiction risk score: %s", e)
            return 0.0

    def get_wellness_score(self, user_id: int, date: Optional[str] = None) -> float:
        score = self.get_addiction_risk_score(user_id, date)
        return round(max(0.0, min(100.0, 100.0 - score)), 2)

    def _addiction_level(self, score: float) -> str:
        if score < 20:
            return "Healthy"
        if score < 40:
            return "Moderate"
        if score < 60:
            return "High"
        if score < 80:
            return "Very High"
        return "Critical"

    def should_throttle_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Return throttle percentage and message based on addiction score."""
        score = self.get_addiction_risk_score(user_id)
        if score < 60:
            pct = 100
            msg = "No throttling"
        elif score <= 75:
            pct = 50
            msg = "Partial throttling due to moderate addiction risk"
        else:
            pct = 20
            msg = "Strong throttling due to high addiction risk"
        return {"throttle_percent": pct, "throttled": pct < 100, "message": msg, "score": score}

    def get_daily_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Return a wellness dashboard for today including week trend."""
        try:
            today = self._today_str()
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT total_watch_minutes, session_count, max_session_duration, break_count, addiction_risk_score, wellness_score FROM addiction_metrics WHERE user_id = ? AND date = ?", (user_id, today))
            row = cur.fetchone()

            total = int(row["total_watch_minutes"] or 0) if row else 0
            session_count = int(row["session_count"] or 0) if row else 0
            max_session = int(row["max_session_duration"] or 0) if row else 0
            break_count = int(row["break_count"] or 0) if row else 0

            addiction_score = float(row["addiction_risk_score"]) if row and row["addiction_risk_score"] is not None else self.get_addiction_risk_score(user_id, today)
            wellness = float(row["wellness_score"]) if row and row["wellness_score"] is not None else (100.0 - addiction_score)

            remaining = max(0, self.DAILY_WATCH_GOAL - total)
            exceeded = total > self.DAILY_WATCH_GOAL

            # week trend
            trend = []
            for i in range(7):
                d = (datetime.utcnow().date() - timedelta(days=i)).isoformat()
                cur.execute("SELECT addiction_risk_score FROM addiction_metrics WHERE user_id = ? AND date = ?", (user_id, d))
                r = cur.fetchone()
                score = float(r["addiction_risk_score"]) if r and r["addiction_risk_score"] is not None else self.get_addiction_risk_score(user_id, d)
                trend.append({"date": d, "score": score})

            conn.close()

            level = self._addiction_level(addiction_score)
            status_message = "All good" if addiction_score < 60 else ("Consider taking breaks" if addiction_score < 80 else "Critical: seek moderation")

            throttle = self.should_throttle_recommendations(user_id)

            return {
                "today_watch_time": total,
                "daily_goal": self.DAILY_WATCH_GOAL,
                "remaining_goal": remaining,
                "exceeded_goal": exceeded,
                "session_count": session_count,
                "max_session_duration": max_session,
                "break_count": break_count,
                "addiction_risk_score": addiction_score,
                "addiction_level": level,
                "wellness_score": wellness,
                "week_trend": trend,
                "status_message": status_message,
                "throttle": throttle,
                "recommendations": ["Take a 5 minute break every 30 minutes", "Prefer shorter content"]
            }
        except sqlite3.Error as e:
            logger.error("Error generating dashboard: %s", e)
            return {"error": str(e)}


if __name__ == "__main__":
    aa = AntiAddictionModule()
    sid = aa.start_watch_session(1, 127, 'happy', 'afternoon')
    print('started', sid)
    print(aa.update_watch_progress(sid, 30))
    print(aa.end_watch_session(sid, 1, True))
    print(aa.get_daily_dashboard(1))
import sqlite3
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Union, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AntiAddictionModule:
    """
    Tracks user watch patterns and provides anti-addiction interventions.
    Calculates addiction risk scores and manages healthy viewing habits.
    """
    
    # Constants
    DAILY_WATCH_GOAL = 120 # minutes
    BREAK_INTERVAL = 30 # minutes
    BINGE_THRESHOLD = 180 # minutes
    CRITICAL_THRESHOLD = 300 # minutes

    def __init__(self, db_path: str = 'recommendation.db'):
        self.db_path = db_path
        self.initialize_db()

    def initialize_db(self):
        """Ensures persistence tables exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Watch sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watch_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    content_id INTEGER NOT NULL,
                    mood_at_start TEXT NOT NULL,
                    time_period TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_minutes INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    user_satisfied BOOLEAN
                )
            """)
            
            # Daily metrics
            cursor.execute("""
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
                    UNIQUE(user_id, date)
                )
            """)
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Error initializing AntiAddiction DB: {e}")

    def start_watch_session(self, user_id: int, content_id: int, mood: str, time_period: str) -> str:
        """
        Start a new watch session.
        Returns: session_id
        """
        timestamp = datetime.now()
        session_id = f"sess_{user_id}_{content_id}_{int(timestamp.timestamp())}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO watch_sessions (session_id, user_id, content_id, mood_at_start, time_period, start_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, content_id, mood, time_period, timestamp))
            
            # Initialize daily metric if needed
            today = timestamp.date()
            cursor.execute("""
                INSERT OR IGNORE INTO addiction_metrics (user_id, date)
                VALUES (?, ?)
            """, (user_id, today))
            
            conn.commit()
            conn.close()
            logger.info(f"Started session {session_id} for user {user_id}")
            return session_id
        except sqlite3.Error as e:
            logger.error(f"Error starting session: {e}")
            return ""

    def update_watch_progress(self, session_id: str, duration_minutes: int) -> Dict:
        """
        Update progress of an active session.
        Checks if a break is needed.
        """
        # Logic: If duration hits a multiple of BREAK_INTERVAL, recommend break
        should_break = (duration_minutes > 0) and (duration_minutes % self.BREAK_INTERVAL == 0)
        
        # In a real app, we'd update DB here too if we want granular tracking
        # For prototype, we assume final duration is sent at end_watch_session
        
        return {
            "session_id": session_id,
            "current_duration": duration_minutes,
            "should_break": should_break,
            "message": "Take a break! You've been watching for a while." if should_break else "",
            "break_recommendation": "Stretch, drink water, or walk around." if should_break else None
        }

    def end_watch_session(self, session_id: str, user_id: int, user_satisfied: bool = True) -> Dict:
        """
        End a session and update daily metrics.
        """
        end_time = datetime.now()
        today = end_time.date()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Get start time to calc true duration (or use supplied duration if tracking via update)
            # For simplicity, we'll calculate from start_time in DB vs now
            cursor.execute("SELECT start_time FROM watch_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": "Session not found"}
                
            start_time = datetime.fromisoformat(row[0])
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # 2. Update session
            cursor.execute("""
                UPDATE watch_sessions 
                SET end_time = ?, duration_minutes = ?, completed = 1, user_satisfied = ?
                WHERE session_id = ?
            """, (end_time, duration_minutes, user_satisfied, session_id))
            
            # 3. Update daily metrics
            # Increment total Minutes, Increment session count
            cursor.execute("""
                UPDATE addiction_metrics 
                SET total_watch_minutes = total_watch_minutes + ?,
                    session_count = session_count + 1,
                    max_session_duration = MAX(max_session_duration, ?)
                WHERE user_id = ? AND date = ?
            """, (duration_minutes, duration_minutes, user_id, today))
            
            conn.commit()
            conn.close()
            
            # 4. Recalculate risk score
            self._update_addiction_score(user_id, today)
            
            dashboard = self.get_daily_dashboard(user_id)
            return {"status": "success", "session_duration": duration_minutes, "dashboard": dashboard}
            
        except sqlite3.Error as e:
            logger.error(f"Error ending session: {e}")
            return {"error": str(e)}

    def _update_addiction_score(self, user_id: int, date_obj: date):
        """Internal method to recalculate and save addiction score."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM addiction_metrics WHERE user_id = ? AND date = ?
            """, (user_id, date_obj))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return

            total_minutes = row['total_watch_minutes']
            session_count = row['session_count']
            max_duration = row['max_session_duration']
            
            # --- Calculation Logic ---
            # Factor 1: Time vs Goal (40%)
            f1 = min(total_minutes / self.DAILY_WATCH_GOAL * 100, 100) * 0.40
            
            # Factor 2: Session Frequency (30%) - approx 5 sessions is "high"
            f2 = min((session_count / 5) * 100, 100) * 0.30
             
            # Factor 3: Binge Patterns (20%)
            f3 = 0
            if total_minutes > self.CRITICAL_THRESHOLD: f3 = 100
            elif total_minutes > self.BINGE_THRESHOLD: f3 = 80
            elif total_minutes > self.DAILY_WATCH_GOAL * 1.5: f3 = 50
            f3 = f3 * 0.20
            
            # Factor 4: Unhealthy Hours (10%) - Check if latest session ended late
            # Simplified: if current time is late night (e.g. 11PM - 4AM). 
            # Ideally checks specific session timestamps.
            # We'll just check if now() is in unhealthy window
            current_hour = datetime.now().hour
            f4 = 0
            if 23 <= current_hour or current_hour <= 4:
                f4 = 50 * 0.10 # Max 5 points
            
            risk_score = min(f1 + f2 + f3 + f4, 100)
            wellness_score = 100 - risk_score
            
            # Update DB
            cursor.execute("""
                UPDATE addiction_metrics
                SET addiction_risk_score = ?, wellness_score = ?
                WHERE metric_id = ?
            """, (risk_score, wellness_score, row['metric_id']))
            
            # Also update user profile
            cursor.execute("""
                UPDATE user_mood_profile
                SET addiction_risk_score = ?, wellness_score = ?
                WHERE user_id = ?
            """, (risk_score, wellness_score, user_id))
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"Error calculating score: {e}")

    def get_addiction_risk_score(self, user_id: int, date_obj: date = None) -> float:
        """Get current risk score."""
        if date_obj is None:
            date_obj = date.today()
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT addiction_risk_score FROM addiction_metrics WHERE user_id = ? AND date = ?", (user_id, date_obj))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else 0.0
        except sqlite3.Error:
            return 0.0

    def get_daily_dashboard(self, user_id: int) -> Dict:
        """Return comprehensive wellness data."""
        today = date.today()
        score = self.get_addiction_risk_score(user_id, today)
        
        # Get metrics
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM addiction_metrics WHERE user_id = ? AND date = ?", (user_id, today))
            row = cursor.fetchone()
            conn.close()
            
            total_time = row['total_watch_minutes'] if row else 0
        except:
            total_time = 0
            
        remaining = max(0, self.DAILY_WATCH_GOAL - total_time)
        exceeded = max(0, total_time - self.DAILY_WATCH_GOAL)
        
        # Risk level text
        if score < 20: level = "Healthy"
        elif score < 40: level = "Moderate"
        elif score < 60: level = "High"
        elif score < 80: level = "Very High"
        else: level = "Critical"
        
        return {
            "user_id": user_id,
            "date": today.isoformat(),
            "today_watch_time": total_time,
            "daily_goal": self.DAILY_WATCH_GOAL,
            "remaining_goal": remaining,
            "exceeded_goal": exceeded,
            "addiction_risk_score": round(score, 1),
            "wellness_score": round(100 - score, 1),
            "addiction_level": level,
            "status_message": self._get_status_message(level, remaining)
        }
        
    def _get_status_message(self, level, remaining):
        if level == "Healthy":
            if remaining > 0: return f"Great habits! You have {remaining} min left in your daily goal."
            return "Goal reached. Good job pacing yourself!"
        elif level == "Moderate":
            return "You're watching a bit more than usual. Take breaks!"
        else:
            return "Warning: High screen time detected. Consider stopping for today."

    def should_throttle_recommendations(self, user_id: int) -> Dict:
        """
        Check if we should limit recommendations based on risk.
        """
        score = self.get_addiction_risk_score(user_id)
        
        throttle_percentage = 0.0 # 0% throttled (show 100%)
        if score > 75:
            throttle_percentage = 0.8 # Show only 20%
        elif score > 60:
            throttle_percentage = 0.5 # Show 50%
            
        return {
            "should_throttle": score > 60,
            "throttle_percentage": throttle_percentage,
            "risk_score": score
        }
