import re
import shutil
import subprocess
from pathlib import Path

from ..config import get_settings
from .asset_paths import safe_media_path


def _output_path(filename: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", filename):
        raise ValueError("Invalid output filename.")
    root = Path("outputs").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root / filename


def _duration_seconds(path: Path) -> float | None:
    ffprobe = shutil.which(get_settings().ffmpeg_binary.replace("ffmpeg", "ffprobe"))
    if not ffprobe:
        return None
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                            capture_output=True, text=True, timeout=30)
    try:
        return max(1.0, float(result.stdout.strip())) if result.returncode == 0 else None
    except ValueError:
        return None


def render_video(clips: list[str], narration: str | None = None,
                 music: str | None = None, subtitles: str | None = None,
                 output_name: str = "final_video.mp4", width: int = 1920,
                 height: int = 1080, fps: int = 30, music_volume: float = 0.12, avatar_overlay: str | None = None):
    """Assemble footage to narration length, mixing audio and burning optional SRT captions."""
    ffmpeg = shutil.which(get_settings().ffmpeg_binary)
    if not ffmpeg:
        raise RuntimeError("FFmpeg is required. Install it and ensure it is on PATH.")
    if not clips or len(clips) > 80:
        raise ValueError("Provide between 1 and 80 video clips.")
    if width % 2 or height % 2:
        raise ValueError("Video width and height must be even numbers.")
    inputs = [safe_media_path(p) for p in clips]
    narration_path = safe_media_path(narration) if narration else None
    music_path = safe_media_path(music) if music else None
    avatar_path = safe_media_path(avatar_overlay) if avatar_overlay else None
    subtitle_path = safe_media_path(subtitles) if subtitles else None
    duration = _duration_seconds(narration_path) if narration_path else None
    out = _output_path(output_name)

    cmd = [ffmpeg, "-y"]
    transition = 0.45 if duration and len(inputs) > 1 else 0.0
    segment = (duration + transition * (len(inputs) - 1)) / len(inputs) if duration else None
    for path in inputs:
        if segment:
            cmd += ["-stream_loop", "-1", "-t", f"{segment:.3f}"]
        cmd += ["-i", str(path)]
    audio_index = len(inputs)
    if narration_path:
        cmd += ["-i", str(narration_path)]
        narration_index = audio_index
        audio_index += 1
    else:
        narration_index = None
    if music_path:
        cmd += ["-stream_loop", "-1", "-i", str(music_path)]
        music_index = audio_index
        audio_index += 1
    else:
        music_index = None
    if avatar_path:
        if duration:
            cmd += ["-stream_loop", "-1", "-t", f"{duration:.3f}"]
        cmd += ["-i", str(avatar_path)]
        avatar_index = audio_index
    else:
        avatar_index = None

    filters = []
    labels = []
    for i in range(len(inputs)):
        label = f"v{i}"
        filters.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,fps={fps},"
            f"eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.35:3:3:0.0,"
            f"format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[{label}]"
        )
        labels.append(f"[{label}]")
    if duration and len(inputs) > 1:
        previous = labels[0]
        for index in range(1, len(inputs)):
            output_label = f"x{index}"
            offset = index * (segment - transition)
            filters.append(
                f"{previous}[v{index}]xfade=transition=fade:duration={transition}:"
                f"offset={offset:.3f}[{output_label}]"
            )
            previous = f"[{output_label}]"
        filters.append(f"{previous}null[outv]")
    elif len(inputs) == 1:
        filters.append(f"{labels[0]}null[outv]")
    else:
        filters.append("".join(labels) + f"concat=n={len(inputs)}:v=1:a=0[outv]")
    if narration_index is not None and music_index is not None:
        filters.append(
            f"[{music_index}:a]volume={music_volume},aresample=async=1[bg];"
            f"[{narration_index}:a]aresample=async=1[voice];"
            f"[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
    elif narration_index is not None:
        filters.append(f"[{narration_index}:a]aresample=async=1[outa]")
    elif music_index is not None:
        filters.append(f"[{music_index}:a]volume={music_volume},aresample=async=1[outa]")

    video_label = "[outv]"
    if avatar_index is not None:
        filters.append(
            f"[{avatar_index}:v]scale={int(width * 0.28)}:-1,format=rgba[avatarpip];"
            f"[outv][avatarpip]overlay=x=W-w-48:y=H-h-48:eof_action=pass:shortest=0[withavatar]"
        )
        video_label = "[withavatar]"
    if subtitle_path:
        srt = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
        filters.append(f"{video_label}subtitles='{srt}':force_style='FontName=Arial,FontSize=22,Outline=2,Shadow=1,Alignment=2'[captioned]")
        video_map = "[captioned]"
    else:
        video_map = video_label
    cmd += ["-filter_complex", ";".join(filters), "-map", video_map]
    if narration_index is not None or music_index is not None:
        cmd += ["-map", "[outa]", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return {"output_path": str(out), "filename": out.name, "bytes": out.stat().st_size,
            "width": width, "height": height, "fps": fps, "format": "mp4",
            "clips_used": len(inputs), "subtitles_burned": bool(subtitle_path),
            "narration_mixed": bool(narration_path), "music_mixed": bool(music_path), "avatar_overlay": bool(avatar_path),
            "target_duration_seconds": duration}
