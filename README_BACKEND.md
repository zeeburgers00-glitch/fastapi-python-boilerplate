# YouTube AI Factory — Backend foundation

A local-first, open-source-first FastAPI backend for an original YouTube content production workflow.

## Included now
- FastAPI API and interactive OpenAPI docs.
- SQLite persistence for projects and job status.
- Topic mode and competitor-link mode.
- Background production-package generation.
- Optional Ollama integration; returns a clearly marked fallback draft if Ollama is unavailable.
- Optional official YouTube Data API metadata lookup.
- FFmpeg slideshow renderer for local images and optional narration audio.
- Basic API tests.

This is a working backend foundation, not yet a finished one-click studio. Voice synthesis, stock-footage search, full timeline editing, animated captions, thumbnail generation, durable distributed workers, authentication, and upload scheduling remain follow-on modules.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Copy .env.example to .env, then:
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

## Optional local AI
Install Ollama, then:
```bash
ollama pull qwen2.5:3b
```
Set `OLLAMA_BASE_URL` and `OLLAMA_MODEL` in `.env`.

## Optional competitor metadata
Set `YOUTUBE_DATA_API_KEY` to a Google YouTube Data API key. The app reads public channel/video metadata through the official API. It does not download, copy, or reproduce competitor videos.

## Start a project
```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects -H "Content-Type: application/json" -d '{"topic":"How solar panels work","mode":"topic","target_format":"long","target_minutes":5,"language":"English"}'
```
Poll the returned `poll_url`, then fetch the project to retrieve its production package.

## Current limitations
- In-process FastAPI background tasks are suitable for local development, not durable high-volume production. Move jobs to Celery + Redis before scaling.
- The render endpoint currently assembles supplied local images into an MP4 slideshow; it is not yet a complete nonlinear editor.
- AI output is a draft. Fact-check and approve it before publishing.
- Respect copyright, media licenses, YouTube API terms, and platform policies.
