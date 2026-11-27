from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db
def test_health():
 init_db();r=TestClient(app).get("/health")
 assert r.status_code==200 and r.json()["status"]=="ok"
def test_capabilities():
 init_db();r=TestClient(app).get("/api/v1/capabilities")
 assert r.status_code==200 and "competitor" in r.json()["modes"]
def test_topic_project_accepted():
 init_db()
 r=TestClient(app).post("/api/v1/projects",json={"topic":"How solar power works","mode":"topic"})
 assert r.status_code==202
 assert r.json()["status"]=="queued"


def test_capabilities_exposes_download_only_and_llm_fallback():
    from app.services.ollama import provider_status
    response = TestClient(app).get("/api/v1/capabilities")
    data = response.json()
    assert "download_only" in data["publishing"]
    assert "llm" in data["providers"]
    assert provider_status()["fallback_order"] == ["groq", "gemini", "openrouter", "ollama"]
