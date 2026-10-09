from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ready_endpoint_empty():
    with patch("app.main.app.state.vector_store") as mock_vs:
        mock_vs.count.return_value = 0
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "not_ready"


def test_ready_endpoint_populated():
    with patch("app.main.app.state.vector_store") as mock_vs:
        mock_vs.count.return_value = 100
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
