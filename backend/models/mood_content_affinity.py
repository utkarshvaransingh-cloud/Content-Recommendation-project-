"""Mood-Content Affinity module

Provides `MoodContentAffinity` class which stores a mood-genre affinity
matrix in-memory and persists it to SQLite for lookup and updates.
"""
from __future__ import annotations

import sqlite3
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MoodContentAffinity:
    """Affinity model mapping moods to genre affinity scores.

    Stores a default matrix as a Python dict and persists entries to a
    SQLite table `mood_affinity` for durability and simple queries.
    """

    DEFAULT_MATRIX: Dict[str, Dict[str, float]] = {
        "happy": {
            "comedy": 0.95, "musical": 0.92, "adventure": 0.85, "animation": 0.88,
            "action": 0.72, "romantic": 0.80, "horror": 0.15
        },
        "sad": {
            "drama": 0.95, "documentary": 0.85, "thriller": 0.75, "crime": 0.70,
            "horror": 0.65, "romance": 0.65, "animation": 0.30
        },
        "neutral": {
            "action": 0.85, "adventure": 0.75, "sci-fi": 0.80, "thriller": 0.75,
            "drama": 0.65, "documentary": 0.70, "horror": 0.50
        }
    }

    def __init__(self, db_path: str = "recommendation.db") -> None:
        """Initialize with SQLite db path and ensure table exists."""
        self.db_path = db_path
        self.matrix = {m: dict(genres) for m, genres in self.DEFAULT_MATRIX.items()}
        try:
            self._ensure_table()
            self._sync_to_db()
        except Exception as e:
            logger.error("Error initializing MoodContentAffinity: %s", e)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        """Create mood_affinity table if it doesn't exist."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mood_affinity (
                    mood TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    affinity_score REAL NOT NULL,
                    PRIMARY KEY (mood, genre)
                )
                """
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error("DB error creating mood_affinity table: %s", e)
            raise

    def _sync_to_db(self) -> None:
        """Persist default matrix to DB if table is empty or missing entries."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            # check existing count
            cur.execute("SELECT COUNT(1) as c FROM mood_affinity")
            row = cur.fetchone()
            count = int(row["c"]) if row is not None else 0

            if count == 0:
                # insert defaults
                for mood, genres in self.matrix.items():
                    for genre, score in genres.items():
                        cur.execute(
                            "INSERT OR REPLACE INTO mood_affinity (mood, genre, affinity_score) VALUES (?, ?, ?)",
                            (mood, genre, float(score)),
                        )
                conn.commit()
            else:
                # optionally update in-memory from DB (prefer DB values)
                cur.execute("SELECT mood, genre, affinity_score FROM mood_affinity")
                rows = cur.fetchall()
                for r in rows:
                    m = r["mood"]
                    g = r["genre"]
                    s = float(r["affinity_score"])
                    if m not in self.matrix:
                        self.matrix[m] = {}
                    self.matrix[m][g] = s

            conn.close()
        except sqlite3.Error as e:
            logger.error("DB error syncing mood_affinity: %s", e)

    def get_affinity_score(self, mood: str, genre: str) -> float:
        """Return the affinity score (0-1) for a mood and genre.

        Returns 0.5 when the genre or mood is unknown.
        """
        try:
            m = (mood or "").lower()
            g = (genre or "").lower()
            if m not in self.matrix:
                return 0.5
            # direct lookup
            if g in self.matrix[m]:
                return float(self.matrix[m][g])
            # fallback: try other moods or default
            return 0.5
        except Exception as e:
            logger.error("Error in get_affinity_score: %s", e)
            return 0.5

    def get_best_genres_for_mood(self, mood: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Return top N genres for a mood as list of dicts {'genre', 'score'}."""
        try:
            m = (mood or "").lower()
            if m not in self.matrix:
                return []
            items = sorted(self.matrix[m].items(), key=lambda kv: kv[1], reverse=True)
            return [{"genre": g, "score": float(s)} for g, s in items[:top_n]]
        except Exception as e:
            logger.error("Error in get_best_genres_for_mood: %s", e)
            return []

    def score_content(self, content: Dict[str, Any], mood: str) -> float:
        """Score a content item against a mood.

        Content dict expected to have 'genres' (list[str]) or 'genre' (str).
        Returns average affinity across genres, default 0.5 when missing.
        """
        try:
            genres = []
            if not content:
                return 0.5
            if "genres" in content and isinstance(content["genres"], (list, tuple)):
                genres = [str(g).lower() for g in content["genres"]]
            elif "genre" in content and isinstance(content["genre"], str):
                genres = [content["genre"].lower()]
            elif "categories" in content and isinstance(content["categories"], (list, tuple)):
                genres = [str(g).lower() for g in content["categories"]]

            if not genres:
                return 0.5

            scores = [self.get_affinity_score(mood, g) for g in genres]
            avg = sum(scores) / len(scores)
            return float(max(0.0, min(1.0, avg)))
        except Exception as e:
            logger.error("Error in score_content: %s", e)
            return 0.5

    def rank_recommendations_by_mood(self, recommendations: List[Dict[str, Any]], mood: str) -> List[Dict[str, Any]]:
        """Return recommendations sorted by affinity to the mood.

        Each returned item will include an `affinity_score` field.
        """
        try:
            out = []
            for item in recommendations:
                score = self.score_content(item, mood)
                item_copy = dict(item)
                item_copy["affinity_score"] = score
                out.append(item_copy)
            out.sort(key=lambda x: x.get("affinity_score", 0.0), reverse=True)
            return out
        except Exception as e:
            logger.error("Error in rank_recommendations_by_mood: %s", e)
            return recommendations

    def get_mood_diversity_score(self, content_list: List[Dict[str, Any]], mood: str) -> Dict[str, Any]:
        """Analyze diversity of a list of content items for a mood.

        Returns dict with: unique_genres_count, genre_entropy (approx), avg_affinity
        """
        try:
            genres = []
            affinities = []
            for c in content_list or []:
                if "genres" in c and isinstance(c["genres"], (list, tuple)):
                    gs = [str(g).lower() for g in c["genres"]]
                elif "genre" in c and isinstance(c["genre"], str):
                    gs = [c["genre"].lower()]
                else:
                    gs = []
                genres.extend(gs)
                affinities.append(self.score_content(c, mood))

            unique = set(genres)
            total = len(genres)
            # simple entropy-like score (not true entropy but indicative)
            genre_counts = {}
            for g in genres:
                genre_counts[g] = genre_counts.get(g, 0) + 1
            entropy = 0.0
            import math
            for cnt in genre_counts.values():
                p = cnt / total if total > 0 else 0
                if p > 0:
                    entropy -= p * math.log(p)

            avg_affinity = float(sum(affinities) / len(affinities)) if affinities else 0.0

            return {
                "unique_genres_count": len(unique),
                "genre_entropy": entropy,
                "avg_affinity": avg_affinity
            }
        except Exception as e:
            logger.error("Error in get_mood_diversity_score: %s", e)
            return {"unique_genres_count": 0, "genre_entropy": 0.0, "avg_affinity": 0.0}

    # Utility: allow updating DB/persisting new affinity
    def upsert_affinity(self, mood: str, genre: str, score: float) -> bool:
        """Insert or update an affinity score in DB and memory."""
        try:
            m = (mood or "").lower()
            g = (genre or "").lower()
            s = float(score)
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO mood_affinity (mood, genre, affinity_score) VALUES (?, ?, ?)",
                (m, g, s),
            )
            conn.commit()
            conn.close()
            if m not in self.matrix:
                self.matrix[m] = {}
            self.matrix[m][g] = s
            return True
        except sqlite3.Error as e:
            logger.error("DB error in upsert_affinity: %s", e)
            return False


if __name__ == "__main__":
    ma = MoodContentAffinity()
    print(ma.get_affinity_score('happy', 'comedy'))
    print(ma.get_best_genres_for_mood('happy', 5))
import sqlite3
import logging
from typing import Dict, List, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MoodContentAffinity:
    """
    Manages the affinity relationships between user moods and content genres.
    Used to score content relevance based on the user's current emotional state.
    """

    def __init__(self, db_path: str = 'recommendation.db'):
        self.db_path = db_path
        self._initialize_affinity_matrix()
        self.initialize_db()

    def _initialize_affinity_matrix(self):
        """Define the static affinity scores between moods and genres."""
        self.affinity_matrix = {
            "happy": {
                "comedy": 0.95, "musical": 0.92, "adventure": 0.85, 
                "animation": 0.88, "action": 0.72, "romance": 0.80, "horror": 0.15
            },
            "sad": {
                "drama": 0.95, "documentary": 0.85, "thriller": 0.75, 
                "crime": 0.70, "horror": 0.65, "romance": 0.65, "animation": 0.30
            },
            "neutral": {
                "action": 0.85, "adventure": 0.75, "sci-fi": 0.80, 
                "thriller": 0.75, "drama": 0.65, "documentary": 0.70, "horror": 0.50
            }
        }

    def initialize_db(self):
        """create table for persistent storage if needed (optional for this phase but good for future)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mood_genre_affinity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mood TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    score REAL NOT NULL,
                    UNIQUE(mood, genre)
                )
            """)
            conn.commit()
            conn.close()
            # In a full production app, we might sync self.affinity_matrix to DB here
        except sqlite3.Error as e:
            logger.error(f"Error initializing affinity DB: {e}")

    def get_affinity_score(self, mood: str, genre: str) -> float:
        """
        Get the affinity score (0.0 - 1.0) for a specific mood and genre.
        
        Args:
            mood (str): User mood.
            genre (str): Content genre.
            
        Returns:
            float: Affinity score.
        """
        mood = mood.lower()
        genre = genre.lower()
        
        # 1. Exact match in matrix
        if mood in self.affinity_matrix:
            return self.affinity_matrix[mood].get(genre, 0.5) # Default to 0.5 if genre not listed
            
        logger.warning(f"Unknown mood: {mood}")
        return 0.5

    def score_content(self, content: Dict, mood: str) -> float:
        """
        Score a content item based on its genres and the user's mood.
        
        Args:
            content (Dict): Content metadata, must contain 'genres' (List[str] or comma-separated str).
            mood (str): User mood.
            
        Returns:
            float: Aggregate affinity score.
        """
        genres = content.get("genres", [])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(',')]
            
        if not genres:
            return 0.5
            
        scores = [self.get_affinity_score(mood, g) for g in genres]
        return sum(scores) / len(scores)

    def get_best_genres_for_mood(self, mood: str, top_n: int = 5) -> List[Dict]:
        """
        Get the top N matching genres for a given mood.
        
        Args:
            mood (str): User mood.
            top_n (int): Number of genres to return.
            
        Returns:
            List[Dict]: List of {"genre": name, "score": value}.
        """
        mood = mood.lower()
        if mood not in self.affinity_matrix:
            return []
            
        scored_genres = [
            {"genre": g, "score": s} 
            for g, s in self.affinity_matrix[mood].items()
        ]
        
        # Sort by score descending
        scored_genres.sort(key=lambda x: x["score"], reverse=True)
        return scored_genres[:top_n]

    def rank_recommendations_by_mood(self, recommendations: List[Dict], mood: str) -> List[Dict]:
        """
        Re-rank a list of recommendations based on mood affinity.
        
        Args:
            recommendations (List[Dict]): List of content items.
            mood (str): User mood.
            
        Returns:
            List[Dict]: Re-ranked list with 'mood_score' added.
        """
        for rec in recommendations:
            rec['mood_score'] = self.score_content(rec, mood)
            
        # Sort by mood_score descending
        return sorted(recommendations, key=lambda x: x['mood_score'], reverse=True)

    def get_mood_diversity_score(self, content_list: List[Dict], mood: str) -> Dict:
        """
        Analyze if the recommendations provide enough diversity for the mood.
        For now, returns a simple count of unique high-affinity genres.
        """
        if not content_list:
            return {"score": 0, "message": "No content"}
            
        unique_genres = set()
        for c in content_list:
            genres = c.get("genres", [])
            if isinstance(genres, str):
                genres = [g.strip() for g in genres.split(',')]
            unique_genres.update(genres)
            
        return {
            "score": len(unique_genres) / 10.0, # Normalizing factor
            "unique_genres": len(unique_genres),
            "message": "Good diversity" if len(unique_genres) > 3 else "Low diversity"
        }
