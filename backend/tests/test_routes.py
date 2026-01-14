import sys
import pathlib
import json

# Ensure project root is on sys.path so `backend` package imports work when tests run
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from backend.app import app


def test_root_endpoint():
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('message')


def test_recommend_with_context_post():
    client = app.test_client()
    payload = {"mood": "happy", "n": 3}
    resp = client.post('/api/recommend-with-context/1', data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'recommendations' in data
    assert isinstance(data['recommendations'], list)
