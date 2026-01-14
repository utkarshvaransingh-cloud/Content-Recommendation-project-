"""Context-aware ensemble recommender

Clean, minimal implementation used for integration and tests.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
"""Context-aware ensemble recommender

Clean, minimal implementation used for integration and tests.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ContextAwareEnsemble:
    """Simple ensemble combining CF/CB/mood/time signals."""

    def __init__(self, cf_model: Optional[Any], cb_model: Optional[Any], mood_affinity: Any, time_analyzer: Any, anti_addiction: Any) -> None:
        self.cf_model = cf_model
        self.cb_model = cb_model
        self.mood_affinity = mood_affinity
        self.time_analyzer = time_analyzer
        self.anti_addiction = anti_addiction
        self.weights = {"collaborative": 0.4, "content": 0.3, "mood": 0.2, "time": 0.1}

    def _generate_mock_recs(self, n: int) -> List[Dict[str, Any]]:
        matrix = getattr(self.mood_affinity, 'matrix', {})
        items: List[Dict[str, Any]] = []
        idx = 1
        for genres in matrix.values():
            for g in genres:
                items.append({"content_id": idx, "title": f"{g.title()} Pick", "genres": [g], "cf_score": 0.5, "cb_score": 0.5})
                idx += 1
                if len(items) >= n:
                    return items
        while len(items) < n:
            items.append({"content_id": idx, "title": f"Item {idx}", "genres": ["documentary"], "cf_score": 0.5, "cb_score": 0.5})
            idx += 1
        return items

    def _collect_candidates(self, user_id: int, n: int) -> List[Dict[str, Any]]:
        cf_list = []
        cb_list = []
        try:
            if self.cf_model and hasattr(self.cf_model, 'get_recommendations'):
                cf_list = self.cf_model.get_recommendations(user_id, 20)
        except Exception:
            cf_list = []
        try:
            if self.cb_model and hasattr(self.cb_model, 'get_recommendations'):
                cb_list = self.cb_model.get_recommendations(user_id, 20)
        except Exception:
            cb_list = []

        if not cf_list and not cb_list:
            return self._generate_mock_recs(max(n, 20))

        by_id: Dict[Any, Dict[str, Any]] = {}
        for it in cf_list:
            cid = it.get('content_id')
            if cid is None:
                continue
            by_id.setdefault(cid, {}).update({**it, 'cf_score': float(it.get('cf_score', 0.5))})
        for it in cb_list:
            cid = it.get('content_id')
            if cid is None:
                continue
            by_id.setdefault(cid, {}).update({**it, 'cb_score': float(it.get('cb_score', 0.5))})

        return list(by_id.values())

    def get_recommendations(self, user_id: int, mood: str, n_recommendations: int, user_watch_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        try:
            candidates = self._collect_candidates(user_id, n_recommendations)
            time_info = self.time_analyzer.get_current_period() if self.time_analyzer else {"period": "unknown"}
            scored: List[Dict[str, Any]] = []
            for c in candidates:
                cf = float(c.get('cf_score', 0.5))
                cb = float(c.get('cb_score', 0.5))
                mood_aff = self.mood_affinity.score_content(c, mood) if self.mood_affinity else 0.5
                genres = c.get('genres', []) or []
                if genres and self.time_analyzer:
                    ts = [self.time_analyzer.get_genre_score_for_time(g) for g in genres]
                    time_score = sum(ts) / len(ts)
                else:
                    time_score = 0.5

                final = (cf * self.weights['collaborative']) + (cb * self.weights['content']) + (mood_aff * self.weights['mood']) + (time_score * self.weights['time'])
                item = dict(c)
                item.update({'final_score': round(final, 4), 'mood_affinity': round(mood_aff, 4), 'time_score': round(time_score, 4)})
                scored.append(item)

            scored.sort(key=lambda x: x.get('final_score', 0.0), reverse=True)

            throttle = self.anti_addiction.should_throttle_recommendations(user_id) if self.anti_addiction else {"throttle_percent": 100, "throttled": False, "message": ""}
            pct = int(throttle.get('throttle_percent', 100))
            limit = n_recommendations if pct >= 100 else max(1, int(round(n_recommendations * pct / 100.0)))

            return {'user_id': user_id, 'requested': n_recommendations, 'returned': min(limit, len(scored)), 'throttled': throttle.get('throttled', False), 'throttle_message': throttle.get('message', ''), 'recommendations': scored[:limit]}
        except Exception as e:
            logger.error("Error generating recommendations: %s", e)
            return {"error": str(e)}


if __name__ == '__main__':
    print('ContextAwareEnsemble module loaded')
