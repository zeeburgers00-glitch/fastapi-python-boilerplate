import asyncio
import shutil
import subprocess
from pathlib import Path
from ..config import get_settings


def synthesize_piper(text: str, filename: str = "voice.wav"):
    s = get_settings()
    if not s.piper_model_path:
        raise RuntimeError("Set PIPER_MODEL_PATH to a downloaded Piper voice model (.onnx).")
    exe = shutil.which(s.piper_binary)
    if not exe:
        raise RuntimeError("Piper executable not found. Install Piper locally and set PIPER_BINARY.")
    outdir = Path("outputs").resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / filename
    p = subprocess.run([exe, "--model", s.piper_model_path, "--output_file", str(out)],
                       input=text, text=True, capture_output=True, timeout=600)
    if p.returncode:
        raise RuntimeError(p.stderr[-2000:])
    return {"audio_path": str(out), "filename": out.name, "bytes": out.stat().st_size, "engine": "Piper"}


def synthesize_edge(text: str, filename: str = "voice.mp3", voice: str = "en-US-AriaNeural"):
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("Install edge-tts to enable online multilingual neural voices.") from exc
    if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
        raise ValueError("Invalid output filename.")
    outdir = Path("outputs").resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / filename
    async def _run():
        await edge_tts.Communicate(text, voice).save(str(out))
    try:
        asyncio.run(_run())
    except RuntimeError as exc:
        if "running event loop" not in str(exc).lower():
            raise
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()
    return {"audio_path": str(out), "filename": out.name, "bytes": out.stat().st_size,
            "engine": "Edge TTS", "voice": voice,
            "note": "Online service availability and terms/limits may change; unlimited usage is not guaranteed."}


def list_edge_voices():
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("Install edge-tts to list multilingual neural voices.") from exc
    return asyncio.run(edge_tts.list_voices())
