from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


def test_register_login_and_ai_chat_flow():
    register = client.post(
        '/auth/register',
        json={
            'email': 'seeker_test@example.com',
            'password': 'Password123!',
            'display_name': 'Seeker One',
            'role': 'support_seeker',
            'is_anonymous': True,
        },
    )
    assert register.status_code == 200
    token = register.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    session_resp = client.post('/sessions/request-ai', headers=headers, json={'cause': 'Stress'})
    assert session_resp.status_code == 200
    session_id = session_resp.json().get('id') or session_resp.json().get('session_id')

    ai_resp = client.post(
        f'/sessions/{session_id}/ai-message',
        headers=headers,
        json={'content': 'I feel lonely'},
    )
    assert ai_resp.status_code == 200
    content = ai_resp.json().get('content', '')
    assert len(content) > 0

    msgs = client.get(f'/sessions/{session_id}/messages', headers=headers)
    assert msgs.status_code == 200
    assert len(msgs.json()) >= 1
