"""Flask routes for contextual recommendations."""
from flask import Blueprint, request, jsonify
from models.mood_detector import MoodDetector
from models.time_analyzer import TimeOfDayAnalyzer
from models.mood_content_affinity import MoodContentAffinity
from models.anti_addiction import AntiAddictionModule
from models.context_ensemble import ContextAwareEnsemble
import logging

logger = logging.getLogger(__name__)

# Blueprint
contextual_bp = Blueprint('contextual', __name__)

# Initialize modules (singleton-style for the simple prototype)
mood_detector = MoodDetector()
time_analyzer = TimeOfDayAnalyzer()
affinity_model = MoodContentAffinity()
anti_addiction = AntiAddictionModule()

# Ensemble: pass None for CF/CB models in prototype
ensemble = ContextAwareEnsemble(None, None, affinity_model, time_analyzer, anti_addiction)


@contextual_bp.route('/mood/<int:user_id>', methods=['GET', 'POST'])
def handle_mood(user_id):
    if request.method == 'POST':
        data = request.json or {}
        mood = data.get('mood')
        if not mood:
            return jsonify({"error": "Mood is required"}), 400
        result = mood_detector.detect_mood_from_input(user_id, mood)
        return jsonify(result)
    else:
        result = mood_detector.get_current_mood(user_id)
        return jsonify(result)


@contextual_bp.route('/mood-trend/<int:user_id>', methods=['GET'])
def get_mood_trend(user_id):
    hours = request.args.get('hours', default=24, type=int)
    result = mood_detector.get_mood_trend(user_id, hours)
    return jsonify(result)


@contextual_bp.route('/recommend-with-context/<int:user_id>', methods=['POST'])
def get_recommendations(user_id):
    data = request.json or {}
    mood = data.get('mood', 'neutral')
    n = int(data.get('n', 10))
    try:
        results = ensemble.get_recommendations(user_id, mood, n_recommendations=n)
        return jsonify(results)
    except Exception as e:
        logger.exception('recommend error')
        return jsonify({"error": str(e)}), 500


@contextual_bp.route('/time-info', methods=['GET'])
def get_time_info():
    return jsonify(time_analyzer.get_current_period())


@contextual_bp.route('/wellness/<int:user_id>', methods=['GET'])
def get_wellness_dashboard(user_id):
    dashboard = anti_addiction.get_daily_dashboard(user_id)
    return jsonify(dashboard)


@contextual_bp.route('/watch-session/start', methods=['POST'])
def start_watch_session():
    data = request.json or {}
    try:
        session_id = anti_addiction.start_watch_session(
            int(data.get('user_id', 0)),
            int(data.get('content_id', 0)),
            data.get('mood', 'neutral'),
            data.get('time_period', 'unknown')
        )
        return jsonify({"session_id": session_id})
    except Exception as e:
        logger.exception('start session error')
        return jsonify({"error": str(e)}), 500


@contextual_bp.route('/watch-session/update', methods=['POST'])
def update_watch_session():
    data = request.json or {}
    try:
        result = anti_addiction.update_watch_progress(data.get('session_id'), int(data.get('duration_minutes', 0)))
        return jsonify(result)
    except Exception as e:
        logger.exception('update session error')
        return jsonify({"error": str(e)}), 500


@contextual_bp.route('/watch-session/end', methods=['POST'])
def end_watch_session():
    data = request.json or {}
    try:
        result = anti_addiction.end_watch_session(data.get('session_id'), int(data.get('user_id', 0)))
        return jsonify(result)
    except Exception as e:
        logger.exception('end session error')
        return jsonify({"error": str(e)}), 500
