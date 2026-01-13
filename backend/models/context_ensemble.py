import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

# Import all our modules
from models.mood_detector import MoodDetector
from models.time_analyzer import TimeOfDayAnalyzer
from models.mood_content_affinity import MoodContentAffinity
from models.anti_addiction import AntiAddictionModule

logger = logging.getLogger(__name__)

class ContextAwareEnsemble:
    """
    Integrates Collaborative Filtering, Content-Based, Mood, Time, and Anti-Addiction
    components to generate final weighted recommendations.
    """

    def __init__(self, ml_model, mappings, mood_detector, time_analyzer, affinity_model, anti_addiction):
        self.ml_model = ml_model # SVD model
        self.mappings = mappings # Dict with user_map, item_map, etc.
        self.mood_detector = mood_detector
        self.time_analyzer = time_analyzer
        self.affinity_model = affinity_model
        self.anti_addiction = anti_addiction
        
        # Weights for final score
        self.weights = {
            "collaborative": 0.40,
            "mood": 0.20,
            "time": 0.10,
            # For this prototype, we treat base popularity/metadata implicitly or via SVD
            # We'll assign remaining weight to 'content' if we had a pure CB model. 
            # Here we will re-distribute:
            "content_bias": 0.30 
        }

    def get_recommendations(self, user_id: int, mood: str = None, n_recommendations: int = 10) -> Dict:
        """
        Generate context-aware recommendations.
        """
        # 1. Addiction Check
        throttle_info = self.anti_addiction.should_throttle_recommendations(user_id)
        if throttle_info['should_throttle']:
            # Adjust N based on throttle percentage
            # e.g., if throttle 0.8 (show 20%), we reduce N.
            # OR we just return a flag to UI.
            # Let's reduce N for backend enforcement.
            limit_factor = 1.0 - throttle_info['throttle_percentage']
            n_recommendations = max(1, int(n_recommendations * limit_factor))
            logger.info(f"Throttling recommendations for user {user_id} to {n_recommendations}")

        # 2. Get Context
        if not mood:
            mood_data = self.mood_detector.get_current_mood(user_id)
            mood = mood_data['mood']
            
        time_info = self.time_analyzer.get_current_period()
        
        # 3. Generate Candidates (ML Layer)
        # In a real system, we'd predict for all items or use ANN (Approx Nearest Neighbors).
        # For this prototype/demo with SVD, we'll take top rated items from SVD reconstruction if feasible,
        # OR just sample a candidate set if matrix is too big. 
        # Since standard SVD predict is slow for all items, let's assume we have a list of 'popular' or 'candidate' items.
        # For ML-100k (1700 items), we can scan all.
        
        candidates = self._get_ml_candidates(user_id, n=100) # Get top 100 raw candidates
        
        # 4. Contextual Re-ranking
        ranked_items = []
        for item_id, pred_rating in candidates:
            # Metadata lookup (simulated for now, would come from u.item)
            # We need genre info for Affinity/Time scoring.
            # In Phase 4 we loaded u.data. We assume we can get u.item info.
            # For this prototype, I'll simulate genre lookup or we need to load u.item.
            # Let's assume we have a helper or random genres for demo if file not loaded.
            # Phase 4 didn't persist item metadata map. I will add a simple metadata loader placeholder here.
            item_meta = self._get_item_metadata(item_id) 
            
            # Scores
            cf_score = (pred_rating / 5.0) # Normalize 1-5 to 0-1
            
            # Mood Score
            mood_score = self.affinity_model.score_content(item_meta, mood)
            
            # Time Score
            # Use primary genre for time scoring
            genres = item_meta.get('genres', [])
            if genres:
                time_score = self.time_analyzer.get_genre_score_for_time(genres[0])
            else:
                time_score = 0.5
                
            # Time Duration Check (Penalty)
            if not self.time_analyzer.is_optimal_time_for_duration(item_meta.get('duration', 90)):
                time_score *= 0.5 # Penalize long content at wrong time
            
            # Final Ensemble Formula
            final_score = (
                cf_score * self.weights['collaborative'] + 
                mood_score * self.weights['mood'] +
                time_score * self.weights['time'] +
                0.3 # content bias/baseline
            )
            
            ranked_items.append({
                "item_id": item_id,
                "title": item_meta.get("title", f"Movie {item_id}"),
                "genres": item_meta.get("genres", []),
                "final_score": final_score,
                "scores": {
                    "ml": round(cf_score, 2),
                    "mood": round(mood_score, 2),
                    "time": round(time_score, 2)
                },
                "mood_match": mood_score > 0.7,
                "reasoning": self._generate_reasoning(mood, time_info, item_meta)
            })
            
        # Sort desc
        ranked_items.sort(key=lambda x: x['final_score'], reverse=True)
        
        return {
            "recommendations": ranked_items[:n_recommendations],
            "context": {
                "mood": mood,
                "time_period": time_info['label'],
                "throttled": throttle_info['should_throttle']
            }
        }

    def _get_ml_candidates(self, user_id, n=50):
        # Uses self.ml_model (SVD) to predict ratings
        # Access user row in SVD matrix
        # This requires mapping user_id to matrix index
        try:
            u_idx = self.mappings['user_map'][user_id]
            # Since SVD model in scikit-learn transforms X, we need the user vector.
            # For simplistic demo with 100k, we might not have the full matrix strictly loaded here.
            # We'll use a Placeholder for the ML prediction to avoid complex matrix reloading logic 
            # in this single file. In production, this queries a Vector DB or Feature Store.
            # For verified working code without the full matrix object in memory:
            # We'll return dummy high-rated items for now to prove the PIPELINE works.
            # OR better: use random + metadata to simulate "candidates".
            pass
        except KeyError:
            # New user or cold start
            pass
            
        # SIMULATION for Prototype (to ensure it runs without 200MB matrix files):
        # Return list of (item_id, predicted_rating)
        return [(i, np.random.uniform(3.5, 5.0)) for i in range(1, n+1)]

    def _get_item_metadata(self, item_id):
        # Placeholder: In real app, query DB/CSV loaded in Phase 4.
        # Simulating variety for demo:
        genres_pool = [
             ["Comedy", "Romance"], ["Action", "Thriller"], ["Drama"], 
             ["Sci-Fi", "Adventure"], ["Horror"], ["Documentary"]
        ]
        g = genres_pool[item_id % len(genres_pool)]
        return {
            "item_id": item_id,
            "title": f"Movie Title {item_id}",
            "genres": g,
            "duration": 90 + (item_id % 60) # Random duration 90-150
        }

    def _generate_reasoning(self, mood, time_info, item_meta):
        genres = item_meta.get("genres", [])
        return f"Matches your {mood} mood and fits {time_info['label']} time."
