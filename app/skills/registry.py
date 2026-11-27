"""Live catalogue of built-in skills and their configuration state.

The catalogue reports configuration, not guaranteed provider uptime. External
services may still rate-limit, change terms, or become unavailable.
"""
import importlib.util
import shutil
from pathlib import Path

from ..config import get_settings


def _module_installed(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def list_skills() -> list[dict]:
    settings = get_settings()
    llm_configured = any((
        bool(settings.groq_api_key),
        bool(settings.gemini_api_key),
        bool(settings.openrouter_api_key),
        bool(settings.ollama_base_url and settings.ollama_model),
    ))
    ffmpeg_ready = bool(shutil.which(settings.ffmpeg_binary))
    edge_ready = _module_installed("edge_tts")
    piper_binary = bool(shutil.which(settings.piper_binary))
    piper_ready = piper_binary and bool(settings.piper_model_path) and Path(settings.piper_model_path).is_file()
    avatar_ready = bool(settings.sadtalker_path) and Path(settings.sadtalker_path).is_dir()

    rows = [
        {
            "id": "research-agent", "name": "Research Agent", "category": "agent",
            "description": "Builds a research brief and highlights claims that need verification.",
            "state": "configured" if llm_configured else "needs_provider",
            "requirements": ["At least one reachable LLM provider"],
            "execution": "LLM-backed; verify citations and factual claims manually",
        },
        {
            "id": "script-agent", "name": "Script Agent", "category": "agent",
            "description": "Creates an original narration script for the selected language, audience and duration.",
            "state": "configured" if llm_configured else "needs_provider",
            "requirements": ["At least one reachable LLM provider"],
            "execution": "LLM-backed",
        },
        {
            "id": "storyboard-agent", "name": "Storyboard Agent", "category": "agent",
            "description": "Turns the narration into a scene-by-scene visual plan.",
            "state": "configured" if llm_configured else "needs_provider",
            "requirements": ["At least one reachable LLM provider"],
            "execution": "LLM-backed",
        },
        {
            "id": "seo-agent", "name": "SEO Agent", "category": "agent",
            "description": "Drafts titles, descriptions and search-oriented metadata.",
            "state": "configured" if llm_configured else "needs_provider",
            "requirements": ["At least one reachable LLM provider"],
            "execution": "LLM-backed; review metadata before publishing",
        },
        {
            "id": "quality-agent", "name": "Quality Review Agent", "category": "agent",
            "description": "Reviews the script, storyboard and SEO package for quality risks.",
            "state": "configured" if llm_configured else "needs_provider",
            "requirements": ["At least one reachable LLM provider"],
            "execution": "AI review is advisory, not a fact-check guarantee",
        },
        {
            "id": "llm-router", "name": "Multi-provider Model Router", "category": "provider",
            "description": "Tries configured Groq, Gemini, OpenRouter and Ollama providers in fallback order.",
            "state": "configured" if llm_configured else "needs_provider",
            "requirements": ["Cloud API key or a reachable local Ollama server"],
            "execution": "Provider quotas and availability vary",
        },
        {
            "id": "edge-neural-voice", "name": "Neural Voiceover", "category": "media",
            "description": "Generates speech through the Edge TTS adapter with language-aware voice selection.",
            "state": "installed" if edge_ready else "dependency_missing",
            "requirements": ["edge-tts package", "Internet access"],
            "execution": "Online service; not guaranteed unlimited",
        },
        {
            "id": "piper-local-voice", "name": "Offline Piper Voice", "category": "media",
            "description": "Generates local speech using a downloaded Piper model.",
            "state": "ready" if piper_ready else ("needs_model_or_binary" if piper_binary else "dependency_missing"),
            "requirements": ["Piper executable", "Compatible .onnx voice model"],
            "execution": "Offline after model installation; quality and language coverage vary",
        },
        {
            "id": "pexels-stock-footage", "name": "Stock Footage", "category": "media",
            "description": "Searches and downloads Pexels video clips for the storyboard.",
            "state": "configured" if settings.pexels_api_key else "needs_api_key",
            "requirements": ["PEXELS_API_KEY"],
            "execution": "External API quota and license terms apply",
        },
        {
            "id": "ffmpeg-video-editor", "name": "FFmpeg Video Editor", "category": "media",
            "description": "Assembles clips, narration, music, captions, transitions and optional avatar overlay.",
            "state": "ready" if ffmpeg_ready else "dependency_missing",
            "requirements": ["FFmpeg and ffprobe binaries"],
            "execution": "Rendering is CPU/RAM intensive",
        },
        {
            "id": "sadtalker-avatar", "name": "Talking Avatar Adapter", "category": "media",
            "description": "Optional SadTalker adapter for animating a supplied portrait with generated speech.",
            "state": "configured_path" if avatar_ready else "needs_installation",
            "requirements": ["SadTalker checkout", "Compatible dependencies", "Model checkpoints"],
            "execution": "Not included in the base image; GPU strongly recommended",
        },
        {
            "id": "thumbnail-generator", "name": "Thumbnail Generator", "category": "media",
            "description": "Creates downloadable thumbnail images using Pillow.",
            "state": "ready" if _module_installed("PIL") else "dependency_missing",
            "requirements": ["Pillow"],
            "execution": "Local image generation",
        },
        {
            "id": "subtitle-generator", "name": "Subtitle Generator", "category": "media",
            "description": "Creates timed SRT captions from narration and burns them into video.",
            "state": "ready" if ffmpeg_ready else "needs_ffmpeg",
            "requirements": ["FFmpeg for burned-in captions"],
            "execution": "Timing is approximate; review captions",
        },
    ]
    return rows
