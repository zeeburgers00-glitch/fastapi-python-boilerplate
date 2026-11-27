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
