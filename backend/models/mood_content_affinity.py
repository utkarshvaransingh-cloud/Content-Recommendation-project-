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
