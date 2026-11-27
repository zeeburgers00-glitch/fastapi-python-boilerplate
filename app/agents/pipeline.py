import asyncio
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .research_agent import research_brief
from .script_agent import write_script
from .storyboard_agent import make_storyboard
from .seo_agent import optimize_seo
from .quality_agent import review_package
from ..services.youtube import analyze
from ..services.media import search_pexels, download_pexels_video
from ..services.voice import synthesize_edge, synthesize_piper
from ..services.subtitles import create_srt
from ..services.editor import render_video
from ..services.avatar import render_talking_avatar
from ..config import get_settings


def _audio_duration(path: str) -> float:
    ffprobe_name = get_settings().ffmpeg_binary.replace("ffmpeg", "ffprobe")
    ffprobe = shutil.which(ffprobe_name)
    if not ffprobe:
        raise RuntimeError("ffprobe is required to time captions and match footage to narration.")
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", path],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Could not read voiceover duration.")
    return max(1.0, float(result.stdout.strip()))


def _save_seo_package(project_id: str, topic: str, language: str, script: str, seo: str):
    outdir = Path("outputs").resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    data = {"project_id": project_id, "topic": topic, "language": language,
            "script": script, "seo": seo, "created_at": datetime.now(timezone.utc).isoformat()}
    json_path = outdir / f"{project_id}_seo.json"
    text_path = outdir / f"{project_id}_seo.txt"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    text_path.write_text(f"SEO METADATA\n\n{seo}\n\nSCRIPT\n\n{script}", encoding="utf-8")
    return {"seo_json": str(json_path), "seo_text": str(text_path)}


async def _auto_produce(project, opts, script):
    settings = get_settings()
    assets = {"status": "not_started", "clips": [], "voiceover": None,
              "captions": None, "renders": [], "avatar": None, "warnings": []}
    if not opts.get("generate_video", True):
        assets["status"] = "skipped_by_request"
        return assets

    voice_path = None
    try:
        voice_name = opts.get("voice_name", "en-US-AriaNeural")
        voice_engine = opts.get("voice_engine", "edge")
        voice_filename = f"{project['id']}_voice.mp3" if voice_engine == "edge" else f"{project['id']}_voice.wav"
        if voice_engine == "piper":
            voice = await asyncio.to_thread(synthesize_piper, script, voice_filename)
        else:
            voice = await asyncio.to_thread(synthesize_edge, script, voice_filename, voice_name)
        voice_path = voice["audio_path"]
        assets["voiceover"] = voice
    except Exception as exc:
        assets["warnings"].append(f"Voiceover unavailable: {str(exc)[:300]}")

    if settings.pexels_api_key:
        try:
            query = opts.get("stock_query") or project["topic"]
            found = await search_pexels(query, per_page=10)
            # Keep a small, diverse set of stock clips for the first automatic cut.
            selected = found[:5]
            for item in selected:
                try:
                    clip = await download_pexels_video(item["id"], "hd")
                    assets["clips"].append({**clip, "asset_path": clip["asset_path"]})
                except Exception as exc:
                    assets["warnings"].append(f"Stock clip {item['id']} skipped: {str(exc)[:180]}")
        except Exception as exc:
            assets["warnings"].append(f"Stock footage unavailable: {str(exc)[:300]}")
    else:
        assets["warnings"].append("PEXELS_API_KEY is not configured; stock footage search/download skipped.")

    if voice_path and assets["clips"]:
        try:
            duration = await asyncio.to_thread(_audio_duration, voice_path)
            srt_path = create_srt(script, duration, f"{project['id']}_captions.srt")
            assets["captions"] = srt_path
            music_path = opts.get("background_music_path")
            if music_path:
                # Renderer validates that all local media paths are inside uploads/.
                pass
            target_format = opts.get("target_format", "long")
            formats = ["short", "long"] if target_format == "both" else [target_format]
            for format_name in formats:
                width, height = (1080, 1920) if format_name == "short" else (1920, 1080)
                rendered = await asyncio.to_thread(
                    render_video,
                    [c["asset_path"] for c in assets["clips"]],
                    voice_path, music_path, srt_path,
                    f"{project['id']}_{format_name}.mp4", width, height, 30, 0.12
                )
                rendered["download_url"] = f"/api/v1/outputs/{rendered['filename']}"
                assets["renders"].append(rendered)
        except Exception as exc:
            assets["warnings"].append(f"Video assembly did not finish: {str(exc)[:500]}")

    avatar_image = opts.get("avatar_image_path")
    if avatar_image and voice_path:
        try:
            avatar = await asyncio.to_thread(
                render_talking_avatar, avatar_image, voice_path, f"{project['id']}_avatar.mp4"
            )
            avatar["download_url"] = f"/api/v1/outputs/{avatar['filename']}"
            assets["avatar"] = avatar
        except Exception as exc:
            assets["warnings"].append(f"Talking avatar unavailable: {str(exc)[:300]}")

    assets["status"] = "video_ready" if assets["renders"] else (
        "partial" if assets["voiceover"] or assets["clips"] else "blocked"
    )
    return assets


async def run_production(project, opts):
    competitor = None
    if project["mode"] == "competitor" and project.get("competitor_url"):
        competitor = await analyze(project["competitor_url"])
    topic = project["topic"]
    language = opts.get("language", "English")
    audience = opts.get("audience", "general audience")
    tone = opts.get("tone", "engaging, clear, factual")
    duration = opts.get("target_minutes", 5)
    research = await research_brief(topic, language)
    if not research:
        research = f"Research plan for {topic}: verify primary sources, dates, statistics, opposing viewpoints and claims."
    context = ""
    if competitor and competitor.get("kind") == "channel":
        channel = competitor.get("channel", {})
        top = competitor.get("top_sample_by_views", [])
        context = f"Channel: {channel.get('title')}; public stats: {channel.get('statistics')}; high-view recent sample: {[{'title': v.get('title'), 'views': v.get('statistics', {}).get('viewCount'), 'duration': v.get('duration')} for v in top]}. Treat as broad audience-interest signals only."
    elif competitor and competitor.get("kind") == "video":
        context = f"Reference video's public metadata: {competitor.get('video')}. Use only as a topic/interest signal, not as a template to reproduce."
    script = await write_script(topic, language, audience, tone, duration, research, context)
    if not script:
        script = f"HOOK: What should viewers know about {topic}?\n\nOUTLINE: Context, evidence-backed key points, counterpoint, conclusion.\n\n[Start a configured LLM provider for a full original narration.]"
    storyboard = await make_storyboard(script)
    if not storyboard:
        storyboard = "Create one scene per script section. Use licensed footage or original graphics; align visuals to narration."
    seo = await optimize_seo(topic, script, language)
    if not seo:
        seo = f"SEO draft: accurate title and description for {topic}; natural keywords, no keyword stuffing."
    qa = await review_package(script, storyboard, seo)
    if not qa:
        qa = "Manual QA required: fact-check all claims, review pacing, verify media rights, captions and metadata."

    output_files = _save_seo_package(project["id"], topic, language, script, seo)
    assets = await _auto_produce(project, opts, script)
    for key, path in output_files.items():
        output_files[key + "_download"] = f"/api/v1/outputs/{Path(path).name}"

    return {
        "project_id": project["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "competitor_analysis": competitor,
        "agents": {
            "research": {"status": "completed", "output": research},
            "script": {"status": "completed", "output": script},
            "storyboard": {"status": "completed", "output": storyboard},
            "seo": {"status": "completed", "output": seo},
            "quality_review": {"status": "completed", "output": qa},
        },
        "assets": assets,
        "downloads": output_files,
        "status": "video_ready" if assets["status"] == "video_ready" else "draft_ready",
        "requires_human_review": True,
        "next_steps": ["Verify factual claims and stock-media license", "Review captions, voiceover and final cut",
                       "Download the MP4 and SEO package"],
    }
