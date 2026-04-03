from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "mock" in data["available_providers"]


def test_chat_with_mock_provider():
    response = client.post(
        "/chat",
        json={
            "message": "hello world",
            "preferred_provider": "mock",
            "allow_fallback": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["provider_used"] == "mock"
    assert "Mock reply" in data["message"]
