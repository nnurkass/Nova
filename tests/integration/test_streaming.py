"""Integration tests for SSE streaming and WebSocket endpoints in Nova API."""
import json
import uuid
import pytest
from fastapi.testclient import TestClient

from nova.api.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestStreamingAPI:
    def test_sse_stream_new_task(self, client):
        task_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/tasks/{task_id}/stream?task=Капремонт школы в Алматы"
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(lines) >= 4

        events = [json.loads(line.replace("data: ", "")) for line in lines]
        event_types = [e.get("event") for e in events]

        assert "pipeline_start" in event_types
        assert "node_complete" in event_types
        assert "pipeline_complete" in event_types

        # Verify task is now completed in database
        status_resp = client.get(f"/api/v1/tasks/{task_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["status"] == "completed"
        assert "selected_tender" in status_data["result"]

    def test_post_stream_endpoint(self, client):
        response = client.post(
            "/api/v1/tasks/stream",
            json={"task": "Строительство водопровода в Астане"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "x-task-id" in response.headers

        task_id = response.headers["x-task-id"]
        lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(lines) >= 4

        # Verify task exists in DB
        status_resp = client.get(f"/api/v1/tasks/{task_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "completed"

    def test_sse_replay_completed_task(self, client):
        # Create task first
        create_resp = client.post(
            "/api/v1/tasks",
            json={"task": "Благоустройство парка в Шымкенте"},
        )
        assert create_resp.status_code == 201
        task_id = create_resp.json()["task_id"]

        # Request stream replay
        stream_resp = client.get(f"/api/v1/tasks/{task_id}/stream")
        assert stream_resp.status_code == 200
        lines = [line.strip() for line in stream_resp.text.split("\n") if line.startswith("data: ")]
        assert len(lines) >= 2
        events = [json.loads(line.replace("data: ", "")) for line in lines]
        assert any(e.get("event") == "pipeline_complete" for e in events)

    def test_websocket_streaming(self, client):
        task_id = uuid.uuid4()
        # Seed task first
        client.post("/api/v1/tasks", json={"task": "Тест WebSocket"})

        # Test WebSocket connect & receive
        with client.websocket_connect(f"/api/v1/tasks/{task_id}/ws") as websocket:
            received_messages = []
            while True:
                try:
                    data = websocket.receive_text()
                    parsed = json.loads(data)
                    received_messages.append(parsed)
                    if parsed.get("event") in {"pipeline_complete", "error"}:
                        break
                except Exception:
                    break

            assert len(received_messages) >= 1
