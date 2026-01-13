from datetime import datetime
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeOfDayAnalyzer:
    """
    Analyzes the current time of day to provide context-aware recommendations.
    Determines time periods (Morning, Afternoon, Evening, Night) and suitable genres/durations.
    """

    def __init__(self):
        """Initialize the TimeOfDayAnalyzer."""
        # Define time periods (start hour, end hour)
        self.periods = {
            "morning": (6, 11),     # 6 AM to 11:59 AM
            "afternoon": (12, 16),  # 12 PM to 4:59 PM
            "evening": (17, 21),    # 5 PM to 9:59 PM
            "night": (22, 5)        # 10 PM to 5:59 AM (wraps around)
        }
        
        # Define period metadata
        self.period_info = {
            "morning": {
                "label": "🌅 Morning",
                "max_duration": 30,
                "desc": "Start your day with something short & educational."
            },
            "afternoon": {
                "label": "☀️ Afternoon",
                "max_duration": 90,
                "desc": "Great time for action or comedy."
            },
            "evening": {
                "label": "🌆 Evening",
                "max_duration": 180,
                "desc": "Relax with a movie or binge-worthy series."
            },
            "night": {
                "label": "🌙 Night",
                "max_duration": 45,
                "desc": "Wind down with relaxing content."
            }
        }

        # Define genre scores for each period [0.0 - 1.0]
        self.genre_affinity = {
            "morning": {
                "educational": 1.0, "news": 0.95, "documentary": 0.85, 
                "short_film": 0.80, "action": 0.40, "horror": 0.10
            },
            "afternoon": {
                "action": 1.0, "adventure": 0.95, "comedy": 0.90, 
                "thriller": 0.80, "sci-fi": 0.75, "horror": 0.30
            },
            "evening": {
                "drama": 0.95, "thriller": 0.90, "sci-fi": 0.90, 
                "action": 0.85, "romance": 0.85, "all": 0.80
            },
            "night": {
                "relaxing": 1.0, "documentary": 0.90, "slice_of_life": 0.85,
                "short_film": 0.80, "asmr": 0.95, "action": 0.30, "horror": 0.05
            }
        }

    def get_current_period(self) -> Dict:
        """
        Identify the current time period based on system time.
        
        Returns:
            Dict: Contains period key, label, and metadata.
        """
        now = datetime.now()
        hour = now.hour
        period_key = self.get_period_by_hour(hour)
        
        info = self.period_info.get(period_key, {})
        
        return {
            "period": period_key,
            "label": info.get("label", "Unknown"),
            "hour": hour,
            "max_duration": info.get("max_duration", 0),
            "description": info.get("desc", "")
        }

    def get_period_by_hour(self, hour: int) -> str:
        """
        Return the period key for a specific hour (0-23).
        
        Args:
            hour (int): Hour of the day.
            
        Returns:
            str: Period key ('morning', 'afternoon', 'evening', 'night').
        """
        for period, (start, end) in self.periods.items():
            if start <= end:
                # Normal range (e.g., 6-11)
                if start <= hour <= end:
                    return period
            else:
                # Wrap-around range (e.g., 22-5)
                if hour >= start or hour <= end:
                    return period
        return "evening" # Default fallback

    def get_genre_score_for_time(self, genre: str) -> float:
        """
        Get suitability score for a genre at the current time.
        
        Args:
            genre (str): Content genre.
            
        Returns:
            float: Score between 0.0 and 1.0.
        """
        current_period = self.get_current_period()["period"]
        genre = genre.lower()
        
        scores = self.genre_affinity.get(current_period, {})
        
        # exact match
        if genre in scores:
            return scores[genre]
            
        # Default fallback scores if not explicitly defined
        return 0.5

    def get_all_genre_scores_for_time(self, genres: List[str]) -> Dict[str, float]:
        """
        Get scores for a list of genres for the current time.
        
        Args:
            genres (List[str]): List of genres.
            
        Returns:
            Dict: Mapping of genre to score.
        """
        return {genre: self.get_genre_score_for_time(genre) for genre in genres}

    def is_optimal_time_for_duration(self, duration_minutes: int) -> bool:
        """
        Check if the content duration is appropriate for the current time.
        
        Args:
            duration_minutes (int): Content length in minutes.
            
        Returns:
            bool: True if duration is within the recommended limit.
        """
        info = self.get_current_period()
        max_duration = info.get("max_duration", 180)
        return duration_minutes <= max_duration

    def get_time_info_str(self) -> str:
        """Returns a human-readable string about the current time context."""
        info = self.get_current_period()
        return f"{info['label']} (Rec: < {info['max_duration']} min)"
