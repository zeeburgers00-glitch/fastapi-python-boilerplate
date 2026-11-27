# YouTube AI Factory — Backend

A modular FastAPI backend for researching topics, creating original YouTube scripts and packaging downloadable Shorts or long-form video assets. The product is **download-only**: it does not upload to YouTube or schedule posts.

## What is implemented

- **Production workflow:** research brief → original script → storyboard → SEO metadata → quality-review notes → optional media production.
- **Specialist agents:** research, script, storyboard, SEO and quality review.
- **Model routing:** Groq, Gemini, OpenRouter and local Ollama adapters with fallback order. Providers must be configured and reachable.
- **Voice:** Edge TTS neural voice adapter with language-aware selection, plus optional local Piper TTS.
- **Stock media:** Pexels search and download endpoints, including source/photographer metadata.
- **Video editing:** FFmpeg multi-clip assembly, 16:9 or 9:16 output, transitions, narration, optional background music, SRT subtitles and optional avatar overlay.
- **Talking avatar:** optional SadTalker adapter. SadTalker, its compatible dependencies and model checkpoints are installed separately.
- **Thumbnails:** locally generated Pillow thumbnails.
- **Project tracking:** SQLite project/job records with stage, progress percentage, status and error details.
- **Capability discovery:** `GET /api/v1/skills` and `GET /api/v1/agents` report built-in modules and whether their dependencies/configuration appear present.
- **API security:** in production mode (`APP_ENV=production`), every `/api/*` route requires `X-API-Key` or a Bearer token. When `API_KEY` is missing, API routes fail closed with HTTP 503. `/health` and `/ready` remain public for platform health checks.
- **Docker:** FFmpeg is included and the app binds to Render's `PORT` environment variable.
- **Tests:** GitHub Actions runs the Python test suite on pushes and pull requests.

## Start locally

Requirements: Python 3.11+, FFmpeg/ffprobe and optional provider configuration.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Copy .env.example to .env, then configure the providers you want to use.
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Configuration

Copy `.env.example` to `.env`. Common options:

- `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`: optional hosted model providers.
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`: optional local Ollama provider.
- `PEXELS_API_KEY`: enables stock video search/download.
- `PIPER_BINARY`, `PIPER_MODEL_PATH`: enables offline Piper voice.
- `SADTALKER_PATH`, `AVATAR_PYTHON`: optional talking avatar installation.
- `FFMPEG_BINARY`: FFmpeg executable.
- `API_KEY`: set a long random secret before using the API in production.
- `CORS_ORIGINS`: comma-separated frontend origins.

Do not commit `.env` or provider credentials. Do not place API keys in frontend source code.

## API workflow

1. `POST /api/v1/projects` creates a project and returns a `job_id`.
2. Poll `GET /api/v1/jobs/{job_id}` for `status`, `stage`, `progress`, `message` and any error.
3. Read `GET /api/v1/projects/{project_id}` for the completed research/script/storyboard/SEO package.
4. Use `GET /api/v1/skills` and `GET /api/v1/agents` to inspect built-in modules and their configuration state.
5. Download generated files through `GET /api/v1/outputs/{filename}`.

Additional endpoints cover media search/download, voice synthesis/catalogue, manual video rendering, thumbnails and optional avatar generation. See the OpenAPI docs for request schemas.

## Security and deployment notes

- For a hosted production deployment set `APP_ENV=production` and `API_KEY` in the host's secret/environment-variable settings. Requests to `/api/*` must include `X-API-Key: <your-key>` or `Authorization: Bearer <your-key>`.
- Never expose the API without setting `API_KEY`.
- The current job runner uses FastAPI in-process background tasks. It records job progress in SQLite, but it is **not a durable distributed queue**: a restart, deploy or free-host sleep may interrupt an active job. A separate worker and durable queue are required for reliable long renders.
- SQLite, uploads and outputs are on the service filesystem. Free Render services do not provide persistent disks, so locally stored data/files can disappear during restarts or redeploys. Use external durable storage before relying on hosted file retention.
- The `/ready` endpoint reports local dependency visibility; it does not prove third-party providers are online or that a full render will succeed.

## Free-tier reality and model limits

The code is free/open-source oriented, but external providers and hosting impose independent quotas, cold starts, execution limits and changing terms. No free GPU, API or cloud host is guaranteed unlimited. This project does not bypass provider limits.

- Edge TTS is an online adapter and is not guaranteed unlimited; Piper can run locally after you install a compatible voice model.
- Pexels access requires an API key and must follow its current terms/license.
- SadTalker is not bundled; a GPU is recommended, and CPU-only rendering may be impractically slow.
- An older CPU-only machine can run the API and light tasks, but long 1080p video renders and talking-avatar generation may be slow or fail from resource limits.

## Not yet implemented / not claimed

- No YouTube OAuth upload, automatic publishing or scheduling.
- No 900+ independent autonomous agents. The current built-in catalogue reports the real modules shipped in this branch; additional agents should be added as tested skills, not placeholder names.
- No professional nonlinear-editor timeline, advanced motion-graphics suite, semantic scene-to-footage matching or guaranteed studio-grade avatar output.
- No durable worker queue, distributed scheduling, multi-user roles, billing/usage system or persistent cloud object storage.
- No real end-to-end test against live cloud APIs or production GPU avatar runtime has been claimed.

AI research and quality review are assistants, not guarantees of factual accuracy. Human review remains necessary for claims, captions, media rights, voice, thumbnail and final video.
