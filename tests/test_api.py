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
    assert VoiceRequest(text="Hello").filename == "voice.mp3"
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

def test_srt_caption_generation(tmp_path, monkeypatch):
    from app.services.subtitles import create_srt
    monkeypatch.chdir(tmp_path)
    result = create_srt("First sentence. Second sentence.", 8.0, "captions.srt")
    content = (tmp_path / result).read_text(encoding="utf-8")
    assert "00:00:00,000 -->" in content
    assert "First sentence." in content
    assert "Second sentence." in content

def test_auto_pipeline_selects_language_voice_without_unbound_engine(monkeypatch):
    import asyncio
    import app.agents.pipeline as pipeline

    class Settings:
        pexels_api_key = ""

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(pipeline, "get_settings", lambda: Settings())
    monkeypatch.setattr(pipeline.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(pipeline, "select_edge_voice", lambda language, preferred: "ur-PK-UzmaNeural")
    monkeypatch.setattr(
        pipeline, "synthesize_edge",
        lambda text, filename, voice: {"audio_path": "outputs/voice.mp3", "filename": filename, "voice": voice},
    )
    monkeypatch.setattr(
        pipeline, "create_thumbnail",
        lambda title, background, filename: {"thumbnail_path": "outputs/" + filename},
    )

    result = asyncio.run(
        pipeline._auto_produce(
            {"id": "test-project", "topic": "Test topic"},
            {"language": "Urdu", "voice_engine": "edge", "voice_name": "auto"},
            "This is narration.",
        )
    )
    assert result["voiceover"]["voice"] == "ur-PK-UzmaNeural"
    assert result["status"] == "partial"


def test_skill_catalogue_reports_real_configuration_state():
    from app.skills.registry import list_skills

    items = list_skills()
    ids = {item["id"] for item in items}
    assert {"research-agent", "script-agent", "ffmpeg-video-editor", "sadtalker-avatar"} <= ids
    assert all("state" in item and "requirements" in item for item in items)


def test_skills_endpoint():
    response = TestClient(app).get("/api/v1/skills")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 10
    assert any(item["id"] == "seo-agent" for item in data["items"])


def test_production_api_fails_closed_and_accepts_valid_key():
    import app.main as main

    previous_env, previous_key = main.s.app_env, main.s.api_key
    try:
        main.s.app_env = "production"
        main.s.api_key = ""
        client = TestClient(app)
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/skills").status_code == 503

        main.s.api_key = "test-secret"
        assert client.get("/api/v1/skills").status_code == 401
        authorized = client.get("/api/v1/skills", headers={"X-API-Key": "test-secret"})
        assert authorized.status_code == 200
    finally:
        main.s.app_env, main.s.api_key = previous_env, previous_key


def test_job_progress_is_persisted(tmp_path):
    from app.config import get_settings
    from app.db import init_db, create_project, create_job, update_job, get_job

    settings = get_settings()
    previous_path = settings.database_path
    try:
        settings.database_path = str(tmp_path / "progress.db")
        init_db()
        create_project({
            "id": "p-progress", "title": "Progress test", "topic": "Progress testing",
            "mode": "topic", "competitor_url": None,
        })
        create_job("j-progress", "p-progress")
        update_job("j-progress", "running", "script", progress=42, message="Writing script")
        job = get_job("j-progress")
        assert job["progress"] == 42
        assert job["message"] == "Writing script"
        assert job["stage"] == "script"
    finally:
        settings.database_path = previous_path


def test_openapi_documents_api_key_security():
    schema = TestClient(app).get("/openapi.json").json()
    assert "ApiKeyAuth" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/api/v1/skills"]["get"]["security"] == [{"ApiKeyAuth": []}]
