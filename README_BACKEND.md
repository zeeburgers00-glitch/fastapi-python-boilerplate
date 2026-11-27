# YouTube AI Factory — Backend

Local-first FastAPI backend for creating original YouTube Shorts and long-form videos, with downloadable video and SEO assets. It does not publish to YouTube.

## Current modules
- Topic and competitor-channel research using official public YouTube metadata.
- Multi-provider LLM router: Groq, Gemini, OpenRouter and local Ollama.
- Research, script, storyboard, SEO and quality-review agents.
- Pexels stock-video search **and download** endpoints with source/photographer metadata.
- FFmpeg multi-clip editor: 1080p/vertical output, narration, background music mixing, and optional SRT caption burn-in.
- Multilingual Edge neural TTS adapter and offline Piper adapter.
- Optional SadTalker talking-avatar adapter for a user-provided portrait and generated narration.
- Pillow thumbnail generation and downloadable output files.
- SQLite project/job tracking, Docker and GitHub Actions tests.

## Important quality and cost notes
- Cloud LLM/TTS/stock services have changing quotas, terms and availability. No free API is guaranteed unlimited.
- Edge TTS is an online voice adapter, not a contractual unlimited voice service. Piper is local/offline but quality and language coverage depend on the selected voice model.
- SadTalker is an optional local adapter. Install its repository, dependencies and model checkpoints separately; model weights are not included. Talking-avatar generation is compute-heavy and will be slow or may not run well on an older CPU-only computer.
- Pexels clips must be checked against the current Pexels license and any applicable asset restrictions before publication. Downloaded stock media is stored locally.
- The FFmpeg editor is a practical multi-clip assembly pipeline, not a full professional nonlinear editor with keyframed motion graphics or a Premiere-style timeline.
- AI-generated facts, captions, voice, avatar and SEO must be reviewed by a human.

## Setup
Python 3.11+, FFmpeg and a local working directory are required.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Optional providers
Configure in `.env`:
- `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY` for cloud text models; or install Ollama and pull `qwen2.5:3b`.
- `PEXELS_API_KEY` for stock video search and download.
- `PIPER_BINARY` and `PIPER_MODEL_PATH` for offline TTS.
- SadTalker checkout path in `SADTALKER_PATH`; set `AVATAR_PYTHON` to its compatible Python interpreter. Install the official SadTalker dependencies and checkpoints separately.
- FFmpeg must be available on PATH (or configure `FFMPEG_BINARY`).

## API workflow
1. `POST /api/v1/projects` creates a research/script/SEO production package.
2. Poll `GET /api/v1/jobs/{job_id}`; inspect `GET /api/v1/projects/{project_id}`.
3. `POST /api/v1/media/search` searches stock clips; `POST /api/v1/media/download` downloads a selected Pexels clip into `uploads/`.
4. Upload narration/music/SRT or portrait/audio through `POST /api/v1/assets/upload`.
5. `POST /api/v1/voice/synthesize` creates voiceover; `GET /api/v1/voice/voices` lists Edge voice names/locales.
6. `POST /api/v1/render/video` assembles clips, voice, music and optional SRT captions.
7. `POST /api/v1/avatar/talking` invokes configured SadTalker for a portrait/audio pair.
8. `GET /api/v1/outputs/{filename}` downloads generated assets.

## Download-only scope
The product scope is video and SEO download only. There is no YouTube OAuth upload, channel publishing or scheduling. The asset upload endpoint only supplies local source assets to the renderer; it does not publish anything.

## Production hardening still required
This branch is an advanced backend foundation, not a claim of a fully production-ready hosted studio. Before public deployment, add authentication/authorization, a durable worker queue, rate limits, storage lifecycle controls, provider spend/usage tracking, full end-to-end tests with real FFmpeg and provider mocks, and deployment-specific secrets. Do not expose this development API publicly without those controls.
