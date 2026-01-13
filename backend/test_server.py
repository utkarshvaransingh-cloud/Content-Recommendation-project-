from app import app

def test_server_setup():
    print("Testing Server Setup...")
    
    # 1. Test Client
    client = app.test_client()
    
    # 2. Check Index
    print("\n[Test] Checking / (Health Check)")
    resp = client.get('/')
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.json}")
    
    # 3. Check API Route
    print("\n[Test] Checking /api/time-info")
    resp = client.get('/api/time-info')
    if resp.status_code == 200:
        print(f"Success! Time info: {resp.json}")
    else:
        print(f"Failed. Status: {resp.status_code}")
        
    # 4. Check Routes List
    print("\n[Test] Registered Routes:")
    for rule in app.url_map.iter_rules():
        if "static" not in str(rule):
            print(f" - {rule} {rule.methods}")

if __name__ == "__main__":
    test_server_setup()
