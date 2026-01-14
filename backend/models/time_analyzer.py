"""TimeOfDayAnalyzer

Implements time-period aware genre scoring and duration guidance.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Dict


class TimeOfDayAnalyzer:
    """Time-of-day analyzer for recommendations.

    Defines four periods and provides genre suitability scoring and
    utility helpers required by the system.
    """

    def __init__(self) -> None:
        # Define periods and their hour ranges (inclusive)
        self.periods = {
            "morning": list(range(6, 12)),    # 6-11
            "afternoon": list(range(12, 17)), # 12-16
            "evening": list(range(17, 22)),   # 17-21
            "night": list(range(22, 24)) + list(range(0, 6)), # 22-5
        }

        # Emoji labels and max durations
        self.meta = {
            "morning": {"label": "🌅 Morning", "max_minutes": 30},
            "afternoon": {"label": "☀️ Afternoon", "max_minutes": 90},
            "evening": {"label": "🌆 Evening", "max_minutes": 180},
            "night": {"label": "🌙 Night", "max_minutes": 45},
        }

        # Genre scoring per period (as specified)
        self.genre_scores = {
            "morning": {"educational": 1.0, "news": 0.95, "documentary": 0.85, "short_film": 0.8, "action": 0.4, "horror": 0.1},
            "afternoon": {"action": 1.0, "adventure": 0.95, "comedy": 0.9, "horror": 0.3},
            "evening": {"drama": 0.95, "thriller": 0.9, "sci-fi": 0.9, "all": 0.8},
            "night": {"relaxing": 1.0, "documentary": 0.9, "action": 0.3, "horror": 0.05},
        }

    def _current_hour(self) -> int:
        return datetime.now().hour

    def get_current_period(self) -> Dict:
        """Return current period info: key, label, max_minutes and genres mapping."""
        hour = self._current_hour()
        for key, hrs in self.periods.items():
            if hour in hrs:
                return {"period": key, "label": self.meta[key]["label"], "max_minutes": self.meta[key]["max_minutes"], "genres": self.genre_scores.get(key, {})}
        # fallback
        key = "night"
        return {"period": key, "label": self.meta[key]["label"], "max_minutes": self.meta[key]["max_minutes"], "genres": self.genre_scores.get(key, {})}

    def get_period_by_hour(self, hour: int) -> str:
        """Return the period name for a specific hour (0-23)."""
        h = int(hour) % 24
        for key, hrs in self.periods.items():
            if h in hrs:
                return key
        return "night"

    def get_genre_score_for_time(self, genre: str) -> float:
        """Return suitability score (0-1) for `genre` at current time."""
        g = (genre or "").lower()
        info = self.get_current_period()
        scores = info.get("genres", {})
        if g in scores:
            return float(scores[g])
        if "all" in scores:
            return float(scores["all"])
        return 0.5

    def get_all_genre_scores_for_time(self, genres: List[str]) -> Dict[str, float]:
        """Return mapping of input genres to their current time scores."""
        return {g: self.get_genre_score_for_time(g) for g in genres}

    def is_optimal_time_for_duration(self, duration_minutes: int) -> bool:
        """Check if a given duration is appropriate for the current period."""
        info = self.get_current_period()
        return int(duration_minutes) <= int(info.get("max_minutes", 60))

    def get_time_info_str(self) -> str:
        """Return a human readable summary for the current period."""
        info = self.get_current_period()
        genres = ", ".join(sorted(info.get("genres", {}).keys()))
        return f"{info.get('label')} — max {info.get('max_minutes')} min; genres: {genres}"


if __name__ == "__main__":
    ta = TimeOfDayAnalyzer()
    print(ta.get_current_period())
    print(ta.get_genre_score_for_time('comedy'))
