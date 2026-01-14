import sys
import pathlib
import pytest

# Ensure project root is on sys.path so `backend` package imports work when tests run
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from backend.models.context_ensemble import ContextAwareEnsemble


class MockAffinity:
    def __init__(self):
        # simple genre matrix for mock recommendations
        self.matrix = {"doc": ["documentary"], "ent": ["comedy"]}

    def score_content(self, content, mood: str):
        # return a deterministic affinity based on mood length
        return 0.7 if mood else 0.5


class MockTimeAnalyzer:
    def get_current_period(self):
        return {"period": "afternoon"}

    def get_genre_score_for_time(self, genre: str):
        return 0.8


class MockAntiAddiction:
    def should_throttle_recommendations(self, user_id: int):
        return {"throttle_percent": 100, "throttled": False, "message": ""}


def test_get_recommendations_basic():
    affinity = MockAffinity()
    time_analyzer = MockTimeAnalyzer()
    anti = MockAntiAddiction()

    ensemble = ContextAwareEnsemble(None, None, affinity, time_analyzer, anti)

    res = ensemble.get_recommendations(user_id=1, mood="happy", n_recommendations=3)

    assert isinstance(res, dict)
    assert res.get("user_id") == 1
    assert res.get("requested") == 3
    assert "recommendations" in res
    recs = res["recommendations"]
    assert 1 <= len(recs) <= 3
    for r in recs:
        assert "content_id" in r
        assert "final_score" in r


def test_get_recommendations_no_models_returns_mocked_count():
    # Use empty affinity to force mock generation path
    class EmptyAffinity:
        def __init__(self):
            self.matrix = {}

        def score_content(self, content, mood: str):
            return 0.5

    affinity = EmptyAffinity()
    time_analyzer = MockTimeAnalyzer()
    anti = MockAntiAddiction()

    ensemble = ContextAwareEnsemble(None, None, affinity, time_analyzer, anti)
    res = ensemble.get_recommendations(user_id=2, mood="", n_recommendations=4)
    assert res.get("requested") == 4
    assert len(res.get("recommendations", [])) >= 1
