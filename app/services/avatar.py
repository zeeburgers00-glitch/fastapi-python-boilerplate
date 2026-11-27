import shutil
import subprocess
from pathlib import Path

from ..config import get_settings
from .asset_paths import safe_media_path


def render_talking_avatar(image_path: str, audio_path: str, filename: str = "talking_avatar.mp4"):
    """Run a user-installed SadTalker checkout; model weights are intentionally not bundled."""
    settings = get_settings()
    repo = settings.sadtalker_path
    python_bin = settings.avatar_python
    if not repo:
        raise RuntimeError("Set SADTALKER_PATH to a locally installed SadTalker repository.")
    repo_path = Path(repo).resolve()
    inference = repo_path / "inference.py"
    if not inference.is_file():
        raise RuntimeError("SadTalker inference.py was not found at SADTALKER_PATH.")
    image = safe_media_path(image_path)
    audio = safe_media_path(audio_path)
    if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
        raise ValueError("Invalid output filename.")
    outdir = Path("outputs") / "avatar"
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [python_bin, str(inference), "--driven_audio", str(audio),
           "--source_image", str(image), "--result_dir", str(outdir.resolve()),
           "--still", "--preprocess", "full", "--enhancer", "gfpgan"]
    result = subprocess.run(cmd, cwd=str(repo_path), capture_output=True, text=True, timeout=7200)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:] or result.stdout[-3000:])
    videos = sorted(outdir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not videos:
        raise RuntimeError("SadTalker finished but did not produce an MP4 file.")
    target = (Path("outputs") / filename).resolve()
    shutil.copy2(videos[0], target)
    return {"output_path": str(target), "filename": target.name, "bytes": target.stat().st_size,
            "engine": "SadTalker", "note": "Local model quality and speed depend on installed checkpoints and hardware."}
