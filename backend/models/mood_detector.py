"""MoodDetector module

Provides the MoodDetector class which handles mood input, inference,
history storage and basic trend calculations using SQLite for persistence.

Usage:
    from models.mood_detector import MoodDetector
    md = MoodDetector()  # uses backend/recommendation.db by default
    md.initialize_db()
    md.detect_mood_from_input(1, 'happy')

"""
from __future__ import annotations

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MoodDetector:
    """Detects, stores and analyses user mood information.

    Persistence: SQLite database (default: recommendation.db in backend).
    """

    ALLOWED_MOODS = {"happy", "sad", "neutral"}

    def __init__(self, db_path: str = "recommendation.db") -> None:
        """Initialize the detector with a path to the SQLite database.

        Args:
            db_path: relative or absolute path to SQLite database file.
        """
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self) -> bool:
        """Ensure required tables exist.

        Returns True on success, False on error.
        """
        try:
            conn = self._connect()
            cur = conn.cursor()

            # user_mood_profile stores current mood summary
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_mood_profile (
                    user_id INTEGER PRIMARY KEY,
                    current_mood TEXT NOT NULL,
                    mood_last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    wellness_score REAL DEFAULT 100.0,
                    addiction_risk_score REAL DEFAULT 0.0
                );
                """
            )

            # mood_history stores all mood events
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mood_history (
                    mood_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mood TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user_mood_profile (user_id)
                );
                """
            )

            # indexes for queries
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mood_history_user ON mood_history(user_id);")
            conn.commit()
            conn.close()
            logger.info("MoodDetector DB initialized.")
            return True
        except sqlite3.Error as e:
            logger.error("Error initializing MoodDetector DB: %s", e)
            return False

    def detect_mood_from_input(self, user_id: int, mood: str) -> Dict:
        """Record a mood selected directly by the user.

        Args:
            user_id: integer user identifier
            mood: one of 'happy', 'sad', 'neutral'

        Returns:
            Dict with stored fields: user_id, mood, confidence, timestamp, status
        """
        mood = (mood or "").strip().lower()
        if mood not in self.ALLOWED_MOODS:
            raise ValueError(f"Invalid mood: {mood}")

        timestamp = datetime.utcnow().isoformat()
        confidence = 0.95
        try:
            conn = self._connect()
            cur = conn.cursor()

            # ensure user profile exists
            cur.execute("SELECT user_id FROM user_mood_profile WHERE user_id = ?", (user_id,))
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO user_mood_profile (user_id, current_mood, mood_last_updated) VALUES (?, ?, ?)",
                    (user_id, mood, timestamp),
                )
            else:
                cur.execute(
                    "UPDATE user_mood_profile SET current_mood = ?, mood_last_updated = ? WHERE user_id = ?",
                    (mood, timestamp, user_id),
                )

            # insert into history
            cur.execute(
                "INSERT INTO mood_history (user_id, mood, confidence, timestamp, source) VALUES (?, ?, ?, ?, ?)",
                (user_id, mood, confidence, timestamp, "user_input"),
            )

            conn.commit()
            conn.close()

            return {
                "user_id": user_id,
                "mood": mood,
                "confidence": confidence,
                "timestamp": timestamp,
                "status": "stored",
            }
        except sqlite3.Error as e:
            logger.error("DB error in detect_mood_from_input: %s", e)
            return {"error": str(e)}

    def infer_mood_from_behavior(self, user_id: int, watch_data: List[Dict]) -> str:
        """Infer mood from watch behaviour.

        Basic heuristic mapping of genres -> mood.

        Args:
            user_id: user id for which to infer
            watch_data: list of dicts, each may contain 'genres' (List[str]) or 'genre' (str)

        Returns:
            mood string
        """
        happy_genres = {"comedy", "musical", "adventure", "animation"}
        sad_genres = {"drama", "thriller", "romance", "melodrama"}

        try:
            genre_counts = {"happy": 0, "sad": 0, "neutral": 0}

            for item in watch_data or []:
                genres = []
                if isinstance(item, dict):
                    if "genres" in item and isinstance(item["genres"], (list, tuple)):
                        genres = [g.lower() for g in item["genres"] if isinstance(g, str)]
                    elif "genre" in item and isinstance(item["genre"], str):
                        genres = [item["genre"].lower()]
                elif isinstance(item, str):
                    genres = [item.lower()]

                for g in genres:
                    if g in happy_genres:
                        genre_counts["happy"] += 1
                    elif g in sad_genres:
                        genre_counts["sad"] += 1
                    else:
                        genre_counts["neutral"] += 1

            # choose mood with highest count
            chosen = max(genre_counts.items(), key=lambda kv: kv[1])[0]

            # store inferred mood with moderate confidence
            confidence = 0.65
            timestamp = datetime.utcnow().isoformat()
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO mood_history (user_id, mood, confidence, timestamp, source) VALUES (?, ?, ?, ?, ?)",
                (user_id, chosen, confidence, timestamp, "inferred"),
            )
            # update current mood as inferred only if there is no recent user input
            cur.execute(
                "SELECT mood_last_updated FROM user_mood_profile WHERE user_id = ?",
                (user_id,)
            )
            row = cur.fetchone()
            update_profile = False
            if row is None:
                # create profile
                cur.execute(
                    "INSERT INTO user_mood_profile (user_id, current_mood, mood_last_updated) VALUES (?, ?, ?)",
                    (user_id, chosen, timestamp),
                )
                update_profile = True
            else:
                try:
                    last = row[0]
                    if last is None:
                        update_profile = True
                    else:
                        # if last update older than 6 hours, allow inferred to set current mood
                        last_dt = datetime.fromisoformat(last) if isinstance(last, str) else datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
                        if datetime.utcnow() - last_dt > timedelta(hours=6):
                            update_profile = True
                except Exception:
                    update_profile = True

            if update_profile:
                cur.execute(
                    "UPDATE user_mood_profile SET current_mood = ?, mood_last_updated = ? WHERE user_id = ?",
                    (chosen, timestamp, user_id),
                )

            conn.commit()
            conn.close()
            return chosen
        except sqlite3.Error as e:
            logger.error("DB error in infer_mood_from_behavior: %s", e)
            return "neutral"

    def get_current_mood(self, user_id: int) -> Dict:
        """Return current mood profile for the user.

        If no profile exists, returns neutral default.
        """
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, current_mood, mood_last_updated, wellness_score, addiction_risk_score FROM user_mood_profile WHERE user_id = ?",
                (user_id,)
            )
            row = cur.fetchone()
            conn.close()
            if row is None:
                return {
                    "user_id": user_id,
                    "current_mood": "neutral",
                    "mood_last_updated": None,
                    "wellness_score": 100.0,
                    "addiction_risk_score": 0.0,
                }

            return {
                "user_id": row["user_id"],
                "current_mood": row["current_mood"],
                "mood_last_updated": (row["mood_last_updated"] if row["mood_last_updated"] is None else str(row["mood_last_updated"])),
                "wellness_score": row["wellness_score"],
                "addiction_risk_score": row["addiction_risk_score"],
            }
        except sqlite3.Error as e:
            logger.error("DB error in get_current_mood: %s", e)
            return {"error": str(e)}

    def get_mood_history(self, user_id: int, hours: int = 24) -> List[Dict]:
        """Return mood history for the past N hours.

        Args:
            user_id: user id
            hours: lookback window in hours

        Returns:
            List of mood event dicts ordered newest first
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT mood_id, mood, confidence, timestamp, source FROM mood_history WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC",
                (user_id, cutoff.isoformat()),
            )
            rows = cur.fetchall()
            conn.close()

            events = []
            for r in rows:
                events.append({
                    "mood_id": r["mood_id"],
                    "mood": r["mood"],
                    "confidence": float(r["confidence"]),
                    "timestamp": (r["timestamp"] if isinstance(r["timestamp"], str) else str(r["timestamp"])),
                    "source": r["source"],
                })
            return events
        except sqlite3.Error as e:
            logger.error("DB error in get_mood_history: %s", e)
            return []

    def get_mood_trend(self, user_id: int, hours: int = 24) -> Dict:
        """Analyze recent moods and return dominant mood and simple trend.

        Returns:
            Dict with keys: dominant_mood, counts, trend_message
        """
        try:
            events = self.get_mood_history(user_id, hours)
            if not events:
                return {"dominant_mood": "neutral", "counts": {}, "trend_message": "No recent data"}

            counts = {m: 0 for m in self.ALLOWED_MOODS}
            for e in events:
                m = e.get("mood")
                if m in counts:
                    counts[m] += 1
                else:
                    counts["neutral"] += 1

            dominant = max(counts.items(), key=lambda kv: kv[1])[0]

            # simple trend analysis: compare first half vs second half of events
            mid = len(events) // 2
            first_half = events[mid:]
            second_half = events[:mid]

            def majority(lst):
                c = {m: 0 for m in self.ALLOWED_MOODS}
                for e in lst:
                    mm = e.get("mood")
                    if mm in c:
                        c[mm] += 1
                return max(c.items(), key=lambda kv: kv[1])[0]

            if not first_half or not second_half:
                trend = "stable"
            else:
                first = majority(first_half)
                second = majority(second_half)
                if first == second:
                    trend = "stable"
                else:
                    trend = f"shifted from {first} to {second}"

            return {"dominant_mood": dominant, "counts": counts, "trend_message": trend}
        except Exception as e:
            logger.error("Error in get_mood_trend: %s", e)
            return {"dominant_mood": "neutral", "counts": {}, "trend_message": "error"}


if __name__ == "__main__":
    md = MoodDetector()
    md.initialize_db()
    print(md.detect_mood_from_input(1, "happy"))
    print(md.get_current_mood(1))
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MoodDetector:
    """
    Handles mood detection, storage, and retrieval for the recommendation system.
    Supports both direct user input and behavioral inference (optional).
    """

    def __init__(self, db_path: str = 'recommendation.db'):
        """
        Initialize the MoodDetector with a database path.
        
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.initialize_db()

    def initialize_db(self):
        """
        Ensures that necessary tables (user_mood_profile, mood_history) exist.
        Although init_db.py handles this, it's good practice for the module to be self-healing.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure tables exist (redundant safety check)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_mood_profile (
                user_id INTEGER PRIMARY KEY,
                current_mood TEXT NOT NULL,
                mood_last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                wellness_score REAL DEFAULT 100.0,
                addiction_risk_score REAL DEFAULT 0.0
            )""")
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS mood_history (
                mood_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mood TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user_mood_profile (user_id)
            )""")
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Error initializing DB in MoodDetector: {e}")

    def detect_mood_from_input(self, user_id: int, mood: str) -> Dict:
        """
        Update mood based on direct user selection.
        
        Args:
            user_id (int): ID of the user.
            mood (str): Selected mood ('happy', 'sad', 'neutral').
            
        Returns:
            Dict: Result of the operation with updated mood info.
        """
        valid_moods = ["happy", "sad", "neutral"]
        mood = mood.lower()
        if mood not in valid_moods:
            logger.warning(f"Invalid mood input: {mood}. Defaulting to neutral.")
            mood = "neutral"

        timestamp = datetime.now()
        confidence = 0.95 # High confidence for direct input

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. Update/Insert current profile
            cursor.execute("""
                INSERT INTO user_mood_profile (user_id, current_mood, mood_last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    current_mood = excluded.current_mood,
                    mood_last_updated = excluded.mood_last_updated
            """, (user_id, mood, timestamp))

            # 2. Log to history
            cursor.execute("""
                INSERT INTO mood_history (user_id, mood, confidence, timestamp, source)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, mood, confidence, timestamp, 'user_input'))

            conn.commit()
            conn.close()

            logger.info(f"Updated mood for user {user_id}: {mood}")
            
            return {
                "user_id": user_id,
                "mood": mood,
                "confidence": confidence,
                "timestamp": timestamp.isoformat(),
                "status": "success"
            }

        except sqlite3.Error as e:
            logger.error(f"Error updating mood from input: {e}")
            return {"status": "error", "message": str(e)}

    def infer_mood_from_behavior(self, user_id: int, watch_data: Dict) -> str:
        """
        Infer user mood based on recent watch behavior.
        
        Args:
            user_id (int): User ID.
            watch_data (Dict): Information about watched content (genre, etc.).
            
        Returns:
            str: Inferred mood ('happy', 'sad', 'neutral').
        """
        # Simplistic inference logic for demonstration
        genre = watch_data.get("genre", "").lower()
        
        if genre in ["comedy", "adventure", "musical"]:
            inferred_mood = "happy"
        elif genre in ["drama", "thriller", "crime"]:
            inferred_mood = "sad" # Or intense/serious
        else:
            inferred_mood = "neutral"
            
        # Note: In a real system, you might not automatically update the DB here 
        # without user confirmation, or you might log it with lower confidence.
        # For this phase, we'll just return the inference.
        return inferred_mood

    def get_current_mood(self, user_id: int) -> Dict:
        """
        Retrieve the current mood for a user.
        
        Args:
            user_id (int): User ID.
            
        Returns:
            Dict: Current mood info or default if not found.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT current_mood, mood_last_updated FROM user_mood_profile WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "mood": row["current_mood"],
                    "last_updated": row["mood_last_updated"],
                    "is_default": False
                }
            else:
                return {
                    "mood": "neutral",
                    "last_updated": None,
                    "is_default": True
                }

        except sqlite3.Error as e:
            logger.error(f"Error retrieval current mood: {e}")
            return {"mood": "neutral", "error": str(e)}

    def get_mood_history(self, user_id: int, hours: int = 24) -> List[Dict]:
        """
        Get mood history for the past N hours.
        
        Args:
            user_id (int): User ID.
            hours (int): Time window in hours.
            
        Returns:
            List[Dict]: List of mood entries.
        """
        try:
            time_threshold = datetime.now() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT mood, confidence, timestamp, source 
                FROM mood_history 
                WHERE user_id = ? AND timestamp >= ? 
                ORDER BY timestamp DESC
            """, (user_id, time_threshold))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error getting mood history: {e}")
            return []

    def get_mood_trend(self, user_id: int, hours: int = 24) -> Dict:
        """
        Analyze recent moods to find the dominant mood and trend.
        
        Args:
            user_id (int): User ID.
            hours (int): Time window.
            
        Returns:
            Dict: Analysis result.
        """
        history = self.get_mood_history(user_id, hours)
        
        if not history:
            return {"dominant_mood": "neutral", "trend": "stable", "entry_count": 0}

        mood_counts = {}
        for entry in history:
            m = entry['mood']
            mood_counts[m] = mood_counts.get(m, 0) + 1
            
        dominant_mood = max(mood_counts, key=mood_counts.get)
        
        # Simple trend analysis: compare first half vs second half of the period if enough data
        # For now, just returning dominant
        
        return {
            "dominant_mood": dominant_mood,
            "trend": "variable", # Placeholder for complex logic
            "entry_count": len(history),
            "breakdown": mood_counts
        }
