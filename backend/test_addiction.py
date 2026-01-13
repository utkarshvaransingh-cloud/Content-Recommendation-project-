from models.anti_addiction import AntiAddictionModule
import time

def test_addiction_module():
    print("Testing AntiAddictionModule...")
    
    aa = AntiAddictionModule()
    user_id = 999 
    
    # Test 1: Start Session
    print("\nTest 1: Start Session")
    session_id = aa.start_watch_session(user_id, 101, "happy", "evening")
    print(f"Session started: {session_id}")
    
    # Test 2: Update Progress (Break Check)
    print("\nTest 2: Update Progress (Break Check)")
    # Simulate 30 mins
    update = aa.update_watch_progress(session_id, 30)
    print(f"Update at 30m: {update['message']}")
    
    # Test 3: End Session
    print("\nTest 3: End Session (Simulating 150 min binge)")
    # We will manually override the start time in DB or just pass duration if we modified logic, 
    # but since our logic calculates from DB start time, we can't easily fake duration without waiting.
    # However, for this TEST script, we can rely on the fact that end_watch_session updates metrics.
    # Actually, the python script uses real time. So duration will be 0.
    # Let's mock a long session by updating the start_time in DB directly for testing purposes.
    import sqlite3
    conn = sqlite3.connect('recommendation.db')
    cursor = conn.cursor()
    # Set start time to 3 hours ago
    cursor.execute(f"UPDATE watch_sessions SET start_time = datetime('now', '-180 minutes') WHERE session_id = '{session_id}'")
    conn.commit()
    conn.close()
    
    result = aa.end_watch_session(session_id, user_id)
    print(f"Session Ended. Duration: {result.get('session_duration')} min")
    
    # Test 4: Dashboard & Risk Score
    print("\nTest 4: Dashboard & Risk Score")
    dash = aa.get_daily_dashboard(user_id)
    print(f"Risk Score: {dash['addiction_risk_score']}")
    print(f"Level: {dash['addiction_level']}")
    print(f"Watch Time: {dash['today_watch_time']} min")
    
    # Test 5: Throttling
    print("\nTest 5: Throttling Check")
    throttle = aa.should_throttle_recommendations(user_id)
    print(f"Should throttle? {throttle['should_throttle']}")
    print(f"Throttle %: {throttle['throttle_percentage']}")

if __name__ == "__main__":
    test_addiction_module()
