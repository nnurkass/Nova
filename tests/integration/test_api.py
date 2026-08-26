"""Integration tests for FastAPI REST API endpoints."""
import pytest
from fastapi.testclient import TestClient

from nova.api.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestAPI:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Nova Multi-Agent Construction AI"
        assert data["status"] == "online"

    def test_health_check_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in {"ok", "degraded"}
        assert "components" in data
        assert "database" in data["components"]
        assert "goszakup_api" in data["components"]
        assert "llm_provider" in data["components"]

    def test_create_task_and_get_lifecycle(self, client):
        # 1. Create and execute task
        create_resp = client.post(
            "/api/v1/tasks",
            json={"task": "Поиск тендеров на капремонт школ в г. Алматы"},
        )
        assert create_resp.status_code == 201
        create_data = create_resp.json()
        assert "task_id" in create_data
        assert create_data["status"] == "completed"

        task_id = create_data["task_id"]

        # 2. Get task status and result
        status_resp = client.get(f"/api/v1/tasks/{task_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["task_id"] == task_id
        assert status_data["status"] == "completed"
        assert status_data["result"] is not None
        assert "selected_tender" in status_data["result"]
        assert "executive_summary" in status_data["result"]

        # 3. Get task report
        report_resp = client.get(f"/api/v1/tasks/{task_id}/report")
        assert report_resp.status_code == 200
        report_data = report_resp.json()
        assert report_data["task_id"] == task_id
        assert "recommendations" in report_data

        # 4. List tasks
        list_resp = client.get("/api/v1/tasks?limit=5")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert isinstance(list_data, list)
        assert any(t["task_id"] == task_id for t in list_data)
