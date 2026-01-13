# 🚀 VS CODE AI CODING GUIDE - MOOD & ANTI-ADDICTION SYSTEM

**Use this file with GitHub Copilot, Cody, or any VS Code AI assistant**

Copy each phase into your AI assistant and follow the prompts. Each phase is self-contained and builds on previous phases.

---

## 📋 BEFORE YOU START

### Prerequisites
- ✅ Python 3.9+ installed
- ✅ Node.js 16+ installed
- ✅ VS Code with AI extension (Copilot, Cody, etc.)
- ✅ Project folder created
- ✅ Read: MOOD_ANTI_ADDICTION_SUMMARY.md
- ✅ Read: ENHANCED_SYSTEM_ARCHITECTURE.md (skim phases)

### Directory Structure Ready
```
recommendation-system/
├── backend/
│   ├── models/
│   ├── routes/
│   ├── data/
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
└── frontend/
    ├── src/
    
    └── package.json
```

---

## 🎯 PHASE 1: DATABASE SCHEMA & INITIALIZATION

### Context for AI Assistant

**Goal**: Create database schema and initialization for mood/anti-addiction tracking

**Files to create**: `backend/db_schema.sql` and `backend/init_db.py`

**Your prompt**:

```
I'm building a mood-aware recommendation system with anti-addiction features. 
Help me create the database schema and initialization script.

Requirements:
1. Create 4 SQLite tables:
   - user_mood_profile: user_id (PK), current_mood, mood_last_updated, wellness_score, addiction_risk_score
   - mood_history: mood_id (PK), user_id (FK), mood, confidence, timestamp, source
   - watch_sessions: session_id (PK), user_id (FK), content_id, mood_at_start, time_period, start_time, end_time, duration_minutes, completed, user_satisfied
   - addiction_metrics: metric_id (PK), user_id (FK), date, total_watch_minutes, session_count, max_session_duration, addiction_risk_score, wellness_score, break_count

2. Create `backend/db_schema.sql` with all CREATE TABLE statements with proper data types and constraints

3. Create `backend/init_db.py` with Python class DatabaseInitializer that:
   - Reads db_schema.sql
   - Creates all tables if they don't exist
   - Has verify_schema() method to check all tables exist
   - Has reset_database() method for testing

4. Use SQLite and ensure all foreign keys work correctly

5. Add proper indexes for performance

Make sure the code is production-ready with error handling.
```

### Expected Output
- ✅ `backend/db_schema.sql` (complete schema)
- ✅ `backend/init_db.py` (initialization class)

### Testing
```bash
cd backend
python -c "from init_db import DatabaseInitializer; db = DatabaseInitializer(); db.initialize_database()"
```

---

## 🎭 PHASE 2: MOOD DETECTOR MODULE

### Context for AI Assistant

**Goal**: Create complete MoodDetector class with mood detection, storage, and history tracking

**File to create**: `backend/models/mood_detector.py`

**Your prompt**:

```
I need you to implement the complete MoodDetector class for mood tracking. 
Based on the ENHANCED_SYSTEM_ARCHITECTURE.md Phase 2.

Requirements:
1. Class: MoodDetector with these methods:
   - __init__(db_path): Initialize with database path
   - initialize_db(): Create mood tracking tables if needed
   - detect_mood_from_input(user_id, mood) -> Dict: User selects mood directly, return {user_id, mood, confidence, timestamp, status}
   - infer_mood_from_behavior(user_id, watch_data) -> str: Infer mood from watch patterns (comedy/adventure = happy, drama/thriller = sad, else neutral)
   - get_current_mood(user_id) -> Dict: Return current mood or default to "neutral"
   - get_mood_history(user_id, hours=24) -> List[Dict]: Return list of moods in past N hours
   - get_mood_trend(user_id, hours=24) -> Dict: Return mood analysis with dominant mood and trend

2. Mood options: ["happy", "sad", "neutral"]

3. Use SQLite for persistence with tables: mood_history, user_mood_profile

4. Features:
   - Store mood with timestamp
   - Track confidence scores (0.0-1.0)
   - User input has high confidence (0.95)
   - Support source tracking (user_input, inferred)
   - Return datetime in ISO format

5. Error handling: Try/except blocks for all DB operations

6. Add docstrings to all methods

Make the code production-ready and well-documented.
```

### Expected Output
- ✅ `backend/models/mood_detector.py` (complete class, 300+ lines)

### Testing
```bash
cd backend
python -c "
from models.mood_detector import MoodDetector
md = MoodDetector()
result = md.detect_mood_from_input(1, 'happy')
print(result)
print(md.get_current_mood(1))
"
```

---

## ⏰ PHASE 3: TIME-OF-DAY ANALYZER

### Context for AI Assistant

**Goal**: Create TimeOfDayAnalyzer class for time-aware recommendations

**File to create**: `backend/models/time_analyzer.py`

**Your prompt**:

```
I need the complete TimeOfDayAnalyzer class for time-of-day aware recommendations.
Based on ENHANCED_SYSTEM_ARCHITECTURE.md Phase 3.

Requirements:
1. Class: TimeOfDayAnalyzer with these methods:
   - __init__(): Initialize time periods and genre recommendations
   - get_current_period() -> Dict: Return current time period with info
   - get_period_by_hour(hour: int) -> str: Return period for specific hour (0-23)
   - get_genre_score_for_time(genre: str) -> float: Suitability of genre for current time (0-1)
   - get_all_genre_scores_for_time(genres: List[str]) -> Dict: Scores for multiple genres
   - is_optimal_time_for_duration(duration_minutes: int) -> bool: Check if duration suitable
   - get_time_info_str() -> str: Human readable time period info

2. Define 4 time periods:
   - morning (6-11): educational, news, documentary, short_film (max 30 min)
   - afternoon (12-16): action, adventure, comedy, thriller (max 90 min)
   - evening (17-21): drama, thriller, sci-fi, action, any (max 180 min)
   - night (22-5): relaxing, documentary, slice_of_life, short_film, asmr (max 45 min)

3. Create comprehensive genre scoring for each period:
   - Morning: educational=1.0, news=0.95, documentary=0.85, action=0.40, horror=0.10
   - Afternoon: action=1.0, adventure=0.95, comedy=0.90, horror=0.30
   - Evening: drama=0.95, thriller=0.90, sci-fi=0.90, all=0.80
   - Night: relaxing=1.0, documentary=0.90, action=0.30, horror=0.05

4. Include period labels with emojis (🌅 Morning, ☀️ Afternoon, 🌆 Evening, 🌙 Night)

5. Use datetime library, no database needed

6. Add docstrings and type hints

Make it production-ready with clear logic.
```

### Expected Output
- ✅ `backend/models/time_analyzer.py` (complete class, 250+ lines)

### Testing
```bash
cd backend
python -c "
from models.time_analyzer import TimeOfDayAnalyzer
ta = TimeOfDayAnalyzer()
print(ta.get_current_period())
print(ta.get_genre_score_for_time('comedy'))
"
```

---

## 📊 PHASE 4: MOOD-CONTENT AFFINITY MODEL

### Context for AI Assistant

**Goal**: Create MoodContentAffinity class for mood-content matching

**File to create**: `backend/models/mood_content_affinity.py`

**Your prompt**:

```
I need the complete MoodContentAffinity class for mood-content matching.
Based on ENHANCED_SYSTEM_ARCHITECTURE.md Phase 4.

Requirements:
1. Class: MoodContentAffinity with these methods:
   - __init__(db_path): Initialize with database path
   - initialize_db(): Create affinity table if needed
   - get_affinity_score(mood: str, genre: str) -> float: Return 0-1 score
   - get_best_genres_for_mood(mood: str, top_n: int = 5) -> List[Dict]: Top genres for mood
   - score_content(content: Dict, mood: str) -> float: Score how well content matches mood
   - rank_recommendations_by_mood(recommendations: List[Dict], mood: str) -> List[Dict]: Re-rank by mood
   - get_mood_diversity_score(content_list: List[Dict], mood: str) -> Dict: Analyze recommendation diversity

2. Create comprehensive affinity matrix:
   Happy: comedy=0.95, musical=0.92, adventure=0.85, animation=0.88, action=0.72, romantic=0.80, horror=0.15
   Sad: drama=0.95, documentary=0.85, thriller=0.75, crime=0.70, horror=0.65, romance=0.65, animation=0.30
   Neutral: action=0.85, adventure=0.75, sci-fi=0.80, thriller=0.75, drama=0.65, documentary=0.70, horror=0.50

3. Store affinity matrix in both:
   - Python dict for fast lookup
   - SQLite table for persistence (mood, genre, affinity_score)

4. When scoring content with multiple genres:
   - Average affinity across all genres
   - Return float between 0-1

5. Methods should handle missing genres gracefully (return 0.5 default)

6. Add docstrings and type hints

7. Include error handling for invalid moods

Make it production-ready with clear documentation.
```

### Expected Output
- ✅ `backend/models/mood_content_affinity.py` (complete class, 200+ lines)

### Testing
```bash
cd backend
python -c "
from models.mood_content_affinity import MoodContentAffinity
ma = MoodContentAffinity()
print(ma.get_affinity_score('happy', 'comedy'))
print(ma.get_best_genres_for_mood('happy', 5))
"
```

---

## 🛡️ PHASE 5: ANTI-ADDICTION MODULE

### Context for AI Assistant

**Goal**: Create AntiAddictionModule class for watch tracking and addiction prevention

**File to create**: `backend/models/anti_addiction.py`

**Your prompt**:

```
I need the complete AntiAddictionModule class for watch session tracking and addiction scoring.
Based on ENHANCED_SYSTEM_ARCHITECTURE.md Phase 5. This is the most complex module.

Requirements:
1. Class: AntiAddictionModule with constants:
   - DAILY_WATCH_GOAL = 120 (minutes)
   - BREAK_INTERVAL = 30 (minutes)
   - BINGE_THRESHOLD = 180 (minutes)
   - CRITICAL_THRESHOLD = 300 (minutes)

2. Methods:
   - __init__(db_path): Initialize database
   - initialize_db(): Create watch_sessions and addiction_metrics tables
   - start_watch_session(user_id, content_id, mood, time_period) -> str: Start tracking, return session_id
   - update_watch_progress(session_id, duration_minutes) -> Dict: Update progress, check for break recommendation
   - end_watch_session(session_id, user_id, user_satisfied) -> Dict: End session, update metrics
   - get_addiction_risk_score(user_id, date=None) -> float: Return 0-100 score
   - get_wellness_score(user_id, date=None) -> float: Return 100 - addiction_score
   - get_daily_dashboard(user_id) -> Dict: Return complete wellness dashboard
   - should_throttle_recommendations(user_id) -> Dict: Check if recommendations should be throttled

3. Addiction calculation (0-100 score):
   - Factor 1: Time vs Goal (40%): total_watch_minutes / daily_goal * 100
   - Factor 2: Session Frequency (30%): (session_count / 5) * 100
   - Factor 3: Binge Patterns (20%): 0 if <180min, 50 if <180min, 80 if <300min, 100 if >300min
   - Factor 4: Unhealthy Hours (10%): 50 if watching after 11 PM, else 0
   - Total = sum of (factor * weight), capped at 100

4. Break recommendation logic:
   - Should break if: duration_minutes % 30 == 0
   - Return dict with: should_break, addiction_score, message, break_recommendation

5. Recommendation throttling:
   - Score < 60: Show all (100%)
   - Score 60-75: Show 50%
   - Score > 75: Show 20%

6. Daily dashboard includes:
   - today_watch_time, daily_goal, remaining_goal, exceeded_goal
   - addiction_risk_score (0-100)
   - addiction_level ("Healthy", "Moderate", "High", "Very High", "Critical")
   - wellness_score (100 - addiction)
   - week_trend (last 7 days)
   - status_message
   - recommendations list

7. Use SQLite for persistence

8. Generate session_id as: f"sess_{user_id}_{content_id}_{timestamp}"

9. Add comprehensive error handling

10. Add docstrings and type hints

Make it production-ready with all edge cases handled.
```

### Expected Output
- ✅ `backend/models/anti_addiction.py` (complete class, 500+ lines)

### Testing
```bash
cd backend
python -c "
from models.anti_addiction import AntiAddictionModule
aa = AntiAddictionModule()
session_id = aa.start_watch_session(1, 127, 'happy', 'afternoon')
print(f'Session: {session_id}')
aa.update_watch_progress(session_id, 30)
result = aa.end_watch_session(session_id, 1, True)
print(result)
dashboard = aa.get_daily_dashboard(1)
print(dashboard)
"
```

---

## 🔄 PHASE 6: CONTEXT-AWARE ENSEMBLE & API ROUTES

### Context for AI Assistant

**Goal**: Create ContextAwareEnsemble class and Flask API routes

**Files to create**: `backend/models/context_ensemble.py` and `backend/routes/contextual_recommend.py`

**Your prompt**:

```
I need the ContextAwareEnsemble class and API routes for context-aware recommendations.
Based on ENHANCED_SYSTEM_ARCHITECTURE.md Phase 6.

PART A: ContextAwareEnsemble class (backend/models/context_ensemble.py)

Requirements:
1. Class: ContextAwareEnsemble with:
   - __init__(cf_model, cb_model, mood_affinity, time_analyzer, anti_addiction)
   - weights dict: collaborative=0.40, content=0.30, mood=0.20, time=0.10
   - get_recommendations(user_id, mood, n_recommendations, user_watch_data) -> Dict
   - _generate_reasoning(rec, mood, time_info) -> str

2. get_recommendations method:
   - Get 20 recommendations from cf_model (collaborative filtering)
   - Get 20 recommendations from cb_model (content-based)
   - Combine and rank by mood affinity
   - Score each with weighted ensemble formula
   - Apply time period suitability
   - Apply addiction throttling
   - Return top N recommendations

3. Scoring formula:
   final_score = (cf_score * 0.40) + (cb_score * 0.30) + (mood_affinity * 0.20) + (time_score * 0.10)

4. For each recommendation include:
   - final_score, mood_match, time_period, reasoning, genres

5. Handle throttling:
   - Check addiction throttle percentage
   - Return throttled=True/False in response
   - Include throttle message if needed

6. Add error handling and docstrings

---

PART B: Flask routes (backend/routes/contextual_recommend.py)

Requirements:
1. Create Flask Blueprint: contextual_bp with url_prefix='/api'

2. Initialize modules at top:
   - mood_detector = MoodDetector()
   - time_analyzer = TimeOfDayAnalyzer()
   - mood_affinity = MoodContentAffinity()
   - anti_addiction = AntiAddictionModule()

3. Create 8 API endpoints:

   POST /mood/<int:user_id>
   - Body: {"mood": "happy"}
   - Returns: mood detection result

   GET /mood/<int:user_id>
   - Returns: current user mood

   GET /mood-trend/<int:user_id>
   - Query: ?hours=24
   - Returns: mood trend

   POST /recommend-with-context/<int:user_id>
   - Body: {"mood": "happy", "n": 10}
   - Returns: context-aware recommendations

   GET /time-info
   - Returns: current time period info

   GET /wellness/<int:user_id>
   - Returns: complete wellness dashboard

   POST /watch-session/start
   - Body: {"user_id": 1, "content_id": 127, "mood": "happy"}
   - Returns: {"session_id": "..."}

   POST /watch-session/update
   - Body: {"session_id": "...", "duration_minutes": 30}
   - Returns: break recommendation if needed

   POST /watch-session/end
   - Body: {"session_id": "...", "user_id": 1, "satisfied": true}
   - Returns: session stats and addiction score

4. All routes should:
   - Use request.json for body data
   - Return jsonify(result)
   - Handle errors gracefully
   - Return appropriate HTTP status codes

5. Add error handling with try/except

6. Add route docstrings

Make it production-ready with proper error handling.
```

### Expected Output
- ✅ `backend/models/context_ensemble.py` (150+ lines)
- ✅ `backend/routes/contextual_recommend.py` (150+ lines)

### Testing
```bash
cd backend
python app.py
# Then test endpoints with curl or Postman
```

---

## 🖥️ PHASE 7: BACKEND APP.PY UPDATE

### Context for AI Assistant

**Goal**: Update backend/app.py to integrate all modules

**File to update**: `backend/app.py`

**Your prompt**:

```
I need to update the main Flask app (backend/app.py) to integrate all new modules and add WebSocket support.

Requirements:
1. Current imports to keep:
   - Flask, CORS, Blueprint, request, jsonify (existing)

2. Add new imports:
   - from flask_socketio import SocketIO, emit
   - from routes.contextual_recommend import contextual_bp
   - from init_db import DatabaseInitializer
   - from datetime import datetime

3. Initialize database on startup:
   - Create DatabaseInitializer instance
   - Call initialize_database() before app runs
   - Add /api/health endpoint that returns {"status": "ok"}

4. Add WebSocket support:
   - Initialize: socketio = SocketIO(app, cors_allowed_origins="*")
   - Keep CORS enabled

5. Register new blueprint:
   - app.register_blueprint(contextual_bp, url_prefix='/api')

6. Add WebSocket event handlers:
   
   @socketio.on('mood_update')
   - Input: {user_id, mood}
   - Process: Call mood_detector.detect_mood_from_input()
   - Emit: 'mood_updated' with {mood, timestamp}
   
   @socketio.on('watch_progress')
   - Input: {session_id, duration_minutes}
   - Process: Call anti_addiction.update_watch_progress()
   - Emit: 'break_recommended' if needed
   
   @socketio.on('get_recommendations')
   - Input: {user_id, mood, watch_history}
   - Process: Get contextual recommendations
   - Emit: 'recommendations' with results

7. Change main execution:
   - from: app.run(debug=True, port=5000)
   - to: socketio.run(app, debug=True, port=5000)

8. Add error handling for WebSocket

9. Add logging setup

Make sure the app starts correctly and all endpoints work.
```

### Expected Output
- ✅ Updated `backend/app.py` with all integrations

### Testing
```bash
cd backend
python app.py
# Should see: "Running on http://0.0.0.0:5000"
# Test: curl http://localhost:5000/api/health
```

---

## ⚛️ PHASE 8: FRONTEND REACT COMPONENTS

### Context for AI Assistant

**Goal**: Create React components for mood selection and wellness tracking

**Files to create**: 6 React components in `frontend/src/components/`

### Component 1: MoodSelector

**Your prompt**:

```
Create a React component for mood selection (frontend/src/components/MoodSelector.jsx).

Requirements:
1. Functional component: MoodSelector(props)
   - Props: {user_id, onMoodSelect, currentMood}

2. Features:
   - 3 buttons: Happy 😊, Sad 😢, Neutral 😐
   - Button color changes when selected
   - Hover effects
   - Smooth transitions

3. Styling (Tailwind CSS):
   - Center aligned
   - Buttons: rounded, with hover effects
   - Active button: highlighted with primary color
   - Padding: 8px 16px
   - Font: medium weight

4. Functionality:
   - onClick handler sends mood to backend (POST /api/mood/{user_id})
   - Loading state while submitting
   - Success/error feedback
   - Display current mood above buttons

5. API call:
   - Use axios
   - POST to http://localhost:5000/api/mood/{user_id}
   - Body: {mood: "happy"/"sad"/"neutral"}

6. Export default component

Make it clean, user-friendly, and production-ready.
```

### Component 2: TimeDisplay

**Your prompt**:

```
Create a React component for current time display (frontend/src/components/TimeDisplay.jsx).

Requirements:
1. Functional component: TimeDisplay(props)

2. Features:
   - Display current time (HH:MM format)
   - Display time period with emoji (🌅 Morning, ☀️ Afternoon, 🌆 Evening, 🌙 Night)
   - Show recommended genres for current time
   - Update every minute

3. Styling (Tailwind CSS):
   - Card layout
   - Centered text
   - Large time display
   - Smaller text for period and genres

4. Functionality:
   - Use useEffect to update time every 60 seconds
   - Fetch time info from /api/time-info on mount
   - Calculate time period locally (morning 6-11, afternoon 12-16, evening 17-21, night 22-5)
   - Display comma-separated genres

5. Data structure to display:
   - Current time
   - Time period name with emoji
   - Recommended genres list
   - Max watch duration for current period

6. Error handling for API call

Make it informative and always-visible in dashboard.
```

### Component 3: WellnessTracker

**Your prompt**:

```
Create a React component for wellness metrics display (frontend/src/components/WellnessTracker.jsx).

Requirements:
1. Functional component: WellnessTracker(props)
   - Props: {user_id, autoRefresh=true}

2. Display metrics (real-time):
   - Today's watch time (vs daily goal with progress bar)
   - Wellness score (gauge 0-100)
   - Addiction risk level (with color coding)
   - Session count
   - Status message

3. Progress bars with Tailwind:
   - Watch time: filled to percentage
   - Colors based on health:
     - Green: < 50% of goal
     - Yellow: 50-100% of goal
     - Orange: 100-150% of goal
     - Red: > 150% of goal

4. Addiction level colors:
   - Healthy (0-20): green ✨
   - Moderate (20-40): blue 👍
   - High (40-60): orange ⚠️
   - Very High (60-80): red 🔴
   - Critical (80-100): dark red 🚨

5. Functionality:
   - Fetch from /api/wellness/{user_id}
   - Auto-refresh every 30 seconds if autoRefresh=true
   - Use WebSocket 'mood_updated' to refresh on demand

6. Responsive design for mobile

Make it visually clear and easy to understand wellness status.
```

### Component 4: BreakReminder

**Your prompt**:

```
Create a React component for break reminder modal (frontend/src/components/BreakReminder.jsx).

Requirements:
1. Functional component: BreakReminder(props)
   - Props: {isOpen, onDismiss, breakData}
   - breakData: {duration, message, addiction_score, activity_suggestion}

2. Modal features:
   - Show/hide based on isOpen prop
   - Centered on screen
   - Semi-transparent overlay
   - Smooth fade-in animation

3. Content:
   - Emoji: ⏱️
   - Large message: "You've watched for X minutes. Take a break!"
   - Suggested activity
   - Addiction score display
   - [Dismiss] button

4. Styling (Tailwind CSS):
   - White background
   - Shadow effects
   - Rounded corners
   - Padding: 24px
   - Button: primary color, hover effects

5. Functionality:
   - Dismiss button calls onDismiss()
   - Close button (X) also dismisses
   - Click outside modal to dismiss
   - Optional: Auto-dismiss after 30 seconds

6. Animations:
   - Fade in/out (0.3s)
   - Slight scale animation

Make it noticeable but not intrusive.
```

### Component 5: EnhancedDashboard

**Your prompt**:

```
Create the main React dashboard component (frontend/src/components/EnhancedDashboard.jsx).

Requirements:
1. Main component that brings everything together

2. Layout:
   - Header with title "Mood-Aware Recommendations"
   - TimeDisplay at top right
   - MoodSelector in second row
   - WellnessTracker in third row
   - BreakReminder modal (conditional)
   - ContextualRecommendations grid below

3. State management (useState):
   - currentMood: "neutral"
   - breakReminder: {isOpen, data}
   - recommendations: []
   - userId: 1 (or from props/context)
   - loading: false

4. WebSocket integration:
   - Connect on mount
   - Listen to 'break_recommended'
   - Listen to 'recommendations'
   - Listen to 'mood_updated'
   - Emit 'get_recommendations' when mood changes

5. Effects (useEffect):
   - Initialize WebSocket on mount
   - Fetch initial recommendations on mount
   - Get initial wellness data
   - Cleanup on unmount

6. Props passed to children:
   - MoodSelector: {user_id, onMoodSelect, currentMood}
   - TimeDisplay: {}
   - WellnessTracker: {user_id, autoRefresh: true}
   - BreakReminder: {isOpen, onDismiss, breakData}
   - ContextualRecommendations: {recommendations, mood}

7. Error handling for all API calls and WebSocket

8. Responsive grid layout for mobile

Make it the main entry point for users.
```

### Component 6: ContextualRecommendations

**Your prompt**:

```
Create recommendation grid component (frontend/src/components/ContextualRecommendations.jsx).

Requirements:
1. Functional component: ContextualRecommendations(props)
   - Props: {recommendations, mood, onWatchStart}

2. Display as grid:
   - 3-4 columns on desktop
   - 2 columns on tablet
   - 1 column on mobile
   - Responsive using Tailwind

3. Each recommendation card shows:
   - Thumbnail/image
   - Title
   - Duration
   - Genres (comma-separated)
   - Mood match indicator (✓ if matches current mood)
   - Affinity score (0-100%)
   - [Watch] button

4. Card styling:
   - Rounded corners
   - Shadow on hover
   - Smooth scale animation on hover
   - Colors based on mood match

5. Functionality:
   - [Watch] button triggers onWatchStart(item_id)
   - Which calls POST /api/watch-session/start
   - Show loading state while fetching
   - Handle empty state (no recommendations)

6. Mood indicators:
   - Green checkmark if affinity > 0.75
   - Orange dot if affinity 0.50-0.75
   - Gray dot if affinity < 0.50

7. Show reasoning: "Why recommended: matches your happy mood, great for afternoon"

8. Loading skeleton for each card while fetching

Make it visually appealing and interactive.
```

### Expected Output
- ✅ `frontend/src/components/MoodSelector.jsx`
- ✅ `frontend/src/components/TimeDisplay.jsx`
- ✅ `frontend/src/components/WellnessTracker.jsx`
- ✅ `frontend/src/components/BreakReminder.jsx`
- ✅ `frontend/src/components/EnhancedDashboard.jsx`
- ✅ `frontend/src/components/ContextualRecommendations.jsx`

### Testing
```bash
cd frontend
npm install socket.io-client axios
npm start
# Should load http://localhost:3000 with all components
```

---

## 🧪 PHASE 9: TESTING & DEBUGGING

### Context for AI Assistant

**Goal**: Create comprehensive test files and debugging utilities

### Test File 1: Backend Unit Tests

**Your prompt**:

```
Create comprehensive unit tests for all backend modules (backend/tests/test_models.py).

Requirements:
1. Use pytest framework

2. Test MoodDetector:
   - test_detect_mood_from_input: user selects happy
   - test_get_current_mood: retrieves current mood
   - test_mood_history: tracks history correctly
   - test_mood_trend: analyzes trend accurately
   - test_infer_mood_from_behavior: comedy content = happy

3. Test TimeOfDayAnalyzer:
   - test_get_current_period: returns correct period
   - test_genre_scoring: comedy score higher for afternoon
   - test_max_duration_by_period: night has lower max

4. Test MoodContentAffinity:
   - test_affinity_score: happy + comedy = high score
   - test_rank_by_mood: reranks recommendations correctly
   - test_diversity_score: calculates diversity metric

5. Test AntiAddictionModule:
   - test_start_session: creates session_id
   - test_addiction_calculation: scores correctly (time, frequency, binge, hours)
   - test_daily_dashboard: includes all metrics
   - test_throttling: recommendations limited at high score

6. Each test should:
   - Use fixtures for sample data
   - Have clear assertions
   - Clean up after (teardown)
   - Test both success and error cases

7. Add parametrized tests for multiple moods/genres

Make tests comprehensive with high coverage (>80%).
```

### Test File 2: Integration Tests

**Your prompt**:

```
Create integration tests for full workflows (backend/tests/test_integration.py).

Requirements:
1. Test end-to-end workflows:
   - Workflow 1: User sets mood → Get recommendations
   - Workflow 2: Start watch → Get break reminder → End watch
   - Workflow 3: Multiple sessions → Addiction score increases

2. Use Flask test client

3. Mock external dependencies where needed

4. Test API endpoints:
   - POST /api/mood/1 with {"mood": "happy"}
   - GET /api/mood/1
   - POST /api/recommend-with-context/1
   - POST /api/watch-session/start
   - POST /api/watch-session/end

5. Verify:
   - Database is updated correctly
   - Responses have correct format
   - Status codes are appropriate
   - Error handling works

Make tests realistic and comprehensive.
```

### Debugging Utilities

**Your prompt**:

```
Create debugging utilities file (backend/debug_utils.py) with:

1. Function: print_database_summary(user_id)
   - Print all user data (moods, sessions, metrics)
   - Show current state in readable format

2. Function: reset_user_data(user_id)
   - Delete all user data for testing
   - Useful for fresh test runs

3. Function: simulate_watch_sessions(user_id, num_sessions)
   - Create fake watch sessions for testing
   - Test addiction scoring with realistic data

4. Function: verify_system_health()
   - Check all databases exist
   - Verify all tables
   - Return status report

5. Function: test_api_endpoints()
   - Make test calls to all endpoints
   - Report any issues
   - Show response times

Make it useful for debugging and development.
```

### Expected Output
- ✅ `backend/tests/test_models.py` (comprehensive unit tests)
- ✅ `backend/tests/test_integration.py` (integration tests)
- ✅ `backend/debug_utils.py` (debugging utilities)

### Running Tests
```bash
cd backend
pytest tests/ -v
pytest tests/test_models.py -v
pytest tests/test_integration.py -v
python -c "from debug_utils import verify_system_health; verify_system_health()"
```

---

## 🚀 PHASE 10: DEPLOYMENT & PRODUCTION

### Context for AI Assistant

**Goal**: Prepare system for production deployment

**Files to create**: `backend/requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`

**Your prompt**:

```
Create production deployment files for the recommendation system.

PART A: Requirements.txt (backend/requirements.txt)

Requirements:
1. List all Python dependencies:
   - Flask (current version)
   - Flask-CORS
   - Flask-SocketIO
   - Python-SocketIO
   - Python-EngineIO
   - Pandas
   - NumPy
   - Scikit-Learn
   - SciPy
   - Requests
   - Joblib
   - Python-DotEnv
   - Gunicorn (for production)
   - Pytest (for testing)

2. Pin versions for reproducibility

---

PART B: Dockerfile (Dockerfile for backend)

Requirements:
1. Use Python 3.9 base image
2. Set working directory to /app
3. Copy requirements.txt
4. Install dependencies
5. Copy entire backend code
6. Expose port 5000
7. CMD to run gunicorn with socketio

---

PART C: docker-compose.yml

Requirements:
1. Services:
   - backend: Python Flask app
   - frontend: Node.js React app
   - db: SQLite (optional)

2. Port mappings:
   - Backend: 5000
   - Frontend: 3000

3. Environment variables
4. Volume mounts for development

---

PART D: .env.example

Requirements:
1. Template environment variables:
   - FLASK_ENV=production
   - DAILY_WATCH_GOAL=120
   - BREAK_INTERVAL=30
   - BINGE_THRESHOLD=180
   - DATABASE_PATH=/data/recommendation.db
   - SECRET_KEY=your-secret-key-here

2. Clear comments explaining each variable

Make deployment straightforward.
```

### Expected Output
- ✅ `backend/requirements.txt`
- ✅ `Dockerfile` (backend)
- ✅ `docker-compose.yml`
- ✅ `.env.example`

### Production Deployment
```bash
# Using Docker
docker-compose up

# Using Gunicorn directly
pip install -r requirements.txt
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```

---

## ✅ FINAL CHECKLIST

After completing all 10 phases:

### Backend Checklist
- [ ] Phase 1: Database schema created ✓
- [ ] Phase 2: MoodDetector working ✓
- [ ] Phase 3: TimeAnalyzer working ✓
- [ ] Phase 4: MoodContentAffinity working ✓
- [ ] Phase 5: AntiAddictionModule working ✓
- [ ] Phase 6: ContextEnsemble + Routes working ✓
- [ ] Phase 7: app.py integrated ✓
- [ ] Phase 9: Tests passing (>80% coverage) ✓
- [ ] Phase 10: Deployment files ready ✓

### Frontend Checklist
- [ ] Phase 8: All 6 components created ✓
- [ ] Mood selector functional ✓
- [ ] Time display working ✓
- [ ] Wellness tracker updating ✓
- [ ] Break reminder modal showing ✓
- [ ] Dashboard layout correct ✓
- [ ] Recommendations grid displaying ✓
- [ ] WebSocket connected ✓
- [ ] Responsive on mobile ✓

### Integration Checklist
- [ ] Backend running on :5000 ✓
- [ ] Frontend running on :3000 ✓
- [ ] WebSocket connected ✓
- [ ] Set mood → Get recommendations ✓
- [ ] Start watch → Track → End ✓
- [ ] Addiction score updating ✓
- [ ] Break reminders triggering ✓
- [ ] Wellness dashboard live updating ✓
- [ ] All tests passing ✓

### Final Testing
- [ ] Mood detection works
- [ ] Time-aware recommendations working
- [ ] Mood-content matching accurate
- [ ] Anti-addiction tracking correct
- [ ] Break reminders at 30 min
- [ ] Addiction score calculates right
- [ ] Wellness dashboard displays
- [ ] WebSocket real-time updates
- [ ] No console errors
- [ ] Performance meets targets (<150ms)

---

## 🎯 SUCCESS CRITERIA

### Week 1 Complete When:
✅ All backend modules implemented
✅ API endpoints functional
✅ Database working
✅ Tests passing

### Week 2 Complete When:
✅ Frontend fully implemented
✅ WebSocket working
✅ Real-time updates working
✅ Ready for production

### Project Complete When:
✅ All features working
✅ All tests passing
✅ Performance optimized
✅ Documentation complete
✅ Deployed successfully

---

## 💡 TIPS FOR USING WITH AI ASSISTANT

1. **Copy-paste each phase prompt individually** - Don't do all at once
2. **Wait for completion** - Let AI finish generating code before next phase
3. **Test as you go** - Test each module before moving to next
4. **Ask for clarification** - If something doesn't make sense
5. **Request modifications** - "Change X to Y" if you want adjustments
6. **Use follow-up prompts** - "Add error handling to this function"
7. **Ask for help** - "Why isn't this working?" Include error message

---

## 🚀 YOU'RE READY!

You now have a complete AI-friendly guide to build the entire system. 

**Next step**: Open VS Code, open this file, and start with Phase 1!

Copy each prompt into your AI assistant and build incrementally. Each phase builds on previous phases.

**Good luck!** 🎉

---

**File created**: January 13, 2026
**Format**: Markdown with AI prompts
**Phases**: 10 complete phases
**Total prompts**: 13 detailed prompts
**Estimated time**: 1-2 weeks with AI assistance

