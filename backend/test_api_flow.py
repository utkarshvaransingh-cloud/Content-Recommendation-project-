from flask import Flask
from routes.contextual_recommend import contextual_bp
import json

def test_api_flow():
    print("Testing API Flow/Integration...")
    
    # Setup Mock App
    app = Flask(__name__)
    app.register_blueprint(contextual_bp, url_prefix='/api')
    client = app.test_client()
    
    user_id = 777
    
    # 1. Set Mood
    print("\n[Step 1] Setting User Mood")
    resp = client.post(f'/api/mood/{user_id}', json={"mood": "happy"})
    print(f"Status: {resp.status_code}, Body: {resp.json}")
    
    # 2. Get Recommendations (Check Context)
    print("\n[Step 2] Getting Recommendations")
    resp = client.post(f'/api/recommend-with-context/{user_id}', json={"n": 3})
    data = resp.json
    print(f"Context: {data.get('context')}")
    print("Top Recs:")
    for rec in data.get('recommendations', []):
        print(f" - {rec['title']} (Score: {rec['final_score']:.2f}) [Reason: {rec.get('reasoning')}]")
        
    # 3. Start Watch Session
    print("\n[Step 3] Start Watch Session")
    rec_item = data.get('recommendations', [])[0]
    resp = client.post('/api/watch-session/start', json={
        "user_id": user_id,
        "content_id": rec_item['item_id'],
        "mood": "happy",
        "time_period": "afternoon"
    })
    session_id = resp.json.get('session_id')
    print(f"Session ID: {session_id}")
    
    # 4. Check Wellness (Dashboard)
    print("\n[Step 4] Check Initial Wellness")
    resp = client.get(f'/api/wellness/{user_id}')
    print(f"Wellness Info: {resp.json}")
    
    # 5. End Session
    print("\n[Step 5] End Session")
    resp = client.post('/api/watch-session/end', json={
        "session_id": session_id,
        "user_id": user_id
    })
    print(f"End Result: {resp.json}")

if __name__ == "__main__":
    test_api_flow()
