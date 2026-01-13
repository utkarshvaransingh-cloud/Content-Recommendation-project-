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
