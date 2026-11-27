from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db
from app.schemas import VideoEditRequest, VoiceRequest


def test_health():
    init_db()
    response = TestClient(app).get("/health")
    assert response.status_code == 200 and response.json()["status"] == "ok"


def test_capabilities():
    init_db()
    response = TestClient(app).get("/api/v1/capabilities")
    data = response.json()
    assert response.status_code == 200
    assert "competitor" in data["modes"]
    assert "download_only" in data["publishing"]
    assert "ffmpeg-multiclip-editor" in data["modules"]
    assert "sadtalker-avatar-adapter" in data["modules"]


def test_topic_project_accepted():
    init_db()
    response = TestClient(app).post("/api/v1/projects", json={"topic": "How solar power works", "mode": "topic"})
    assert response.status_code == 202
    assert response.json()["status"] == "queued"


def test_video_editor_request_defaults():
    request = VideoEditRequest(clip_paths=["uploads/clip.mp4"])
    assert request.width == 1920 and request.height == 1080
    assert request.music_volume == 0.12


def test_voice_request_supports_both_engines():
    assert VoiceRequest(text="Hello", engine="edge").voice == "en-US-AriaNeural"
    assert VoiceRequest(text="Hello", engine="piper").engine == "piper"


def test_provider_fallback_order():
    from app.services.ollama import provider_status
    assert provider_status()["fallback_order"] == ["groq", "gemini", "openrouter", "ollama"]


def test_project_schema_exposes_automatic_production_options():
    from app.schemas import ProjectCreate
    project = ProjectCreate(topic="A useful explainer topic")
    assert project.generate_video is True
    assert project.voice_engine == "edge"
    assert project.target_format == "long"
