from pathlib import Path


def _safe_path(value: str, roots: tuple[str, ...]) -> Path:
    path = Path(value).resolve()
    allowed = [Path(root).resolve() for root in roots]
    if not any(root in path.parents for root in allowed):
        raise ValueError(f"Media inputs must be inside one of: {', '.join(roots)}.")
    if not path.is_file():
        raise ValueError(f"Media asset does not exist: {path.name}")
    return path


def safe_upload_path(value: str) -> Path:
    Path("uploads").mkdir(parents=True, exist_ok=True)
    return _safe_path(value, ("uploads",))


def safe_media_path(value: str) -> Path:
    Path("uploads").mkdir(parents=True, exist_ok=True)
    Path("outputs").mkdir(parents=True, exist_ok=True)
    return _safe_path(value, ("uploads", "outputs"))
