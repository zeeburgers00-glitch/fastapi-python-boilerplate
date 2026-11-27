# YouTube AI Factory — Backend foundation

Local-first FastAPI backend for an original YouTube production workflow.

## Included modules
- FastAPI project/job API with SQLite persistence.
- Topic-to-production-package and competitor-link modes.
- Specialist agents: research planner, script writer, storyboard director, SEO editor, quality reviewer.
- Local Ollama model adapter (optional).
- Official YouTube Data API competitor metadata lookup, including channel handles and a sample of recent uploads ranked by public views (optional).
- Piper local text-to-speech adapter (optional).
- Pexels stock-video search adapter (optional API key; respect each asset's license and terms).
- Pillow thumbnail generator.
- FFmpeg slideshow renderer with narration audio.
- Upload endpoint with size and file-extension limits; render/thumbnail inputs are restricted to the uploads directory.
- Dockerfile, Docker Compose, CI test workflow and starter tests.

This is an early working backend foundation, not yet the complete one-click studio. Durable distributed queues, authentication, full timeline editing, caption burn-in, auto B-roll matching, advanced thumbnail layouts, channel OAuth/upload scheduling and production hardening are still required.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Copy .env.example to .env and edit optional settings
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

## Optional AI services
- Ollama: install locally and run `ollama pull qwen2.5:3b`; configure `OLLAMA_BASE_URL` and `OLLAMA_MODEL`.
- Piper: install Piper, download a compatible voice model, set `PIPER_BINARY` and `PIPER_MODEL_PATH`.
- YouTube competitor metadata: set `YOUTUBE_DATA_API_KEY` from Google Cloud.
- Stock video search: set `PEXELS_API_KEY`.

No API key is required for the basic local API, SQLite storage, Pillow thumbnails, or FFmpeg rendering. Optional provider accounts/quotas may apply.

## Docker
Copy `.env.example` to `.env`, then:
```bash
docker compose up --build
```
For Ollama, pull a model inside the Ollama container after it starts:
```bash
docker compose exec ollama ollama pull qwen2.5:3b
```

## API flow
1. `POST /api/v1/projects` with a topic or competitor URL.
2. Poll `GET /api/v1/jobs/{job_id}`.
3. Read the result at `GET /api/v1/projects/{project_id}`.
4. Upload images/audio using `POST /api/v1/assets/upload`.
5. Optional: `POST /api/v1/voice/synthesize`, `POST /api/v1/media/search`, `POST /api/v1/thumbnails/generate`.
6. Render supplied images/audio using `POST /api/v1/render/slideshow`.
7. Retrieve generated files via `GET /api/v1/outputs/{filename}`.

## Important limitations and safety
- FastAPI in-process background tasks are for local development only. Replace with Celery + Redis and durable retries before multi-user production.
- Competitor analysis uses official public metadata; it does not scrape/download competitor videos or copy their content.
- The renderer currently creates a slideshow, not a full nonlinear editing timeline.
- Generated scripts/SEO are drafts; fact-check claims, verify rights and human-review before publishing.
- This starter has no user authentication. Do not expose it to the public internet until authentication, authorization, rate limits, quotas and secure storage are added.
- Free tools do not imply unlimited cloud compute, voice generation, storage or stock API usage.
