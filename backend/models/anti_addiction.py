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
