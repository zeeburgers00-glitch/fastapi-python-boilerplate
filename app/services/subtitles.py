import re
from pathlib import Path


def create_srt(text: str, duration_seconds: float, filename: str = "captions.srt") -> str:
    """Create readable timed captions by distributing sentence chunks over narration duration."""
    if not filename.endswith(".srt") or not re.fullmatch(r"[A-Za-z0-9_.-]+", filename):
        raise ValueError("Invalid SRT filename.")
    clean = re.sub(r"(?m)^\s*(HOOK|INTRO|OUTRO|SCENE\s*\d+|CHAPTER\s*\d+)[^\n]*$", "", text, flags=re.I)
    clean = re.sub(r"\[[^\]]*\]", "", clean)
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", clean) if x.strip()]
    chunks = []
    for sentence in sentences:
        words = sentence.split()
        for i in range(0, len(words), 10):
            chunks.append(" ".join(words[i:i + 10]))
    if not chunks:
        chunks = [text.strip()[:120]]
    weights = [max(1, len(chunk.split())) for chunk in chunks]
    total = sum(weights)
    cursor = 0.0
    lines = []
    for index, (chunk, weight) in enumerate(zip(chunks, weights), 1):
        start = cursor
        cursor += duration_seconds * weight / total
        end = min(duration_seconds, cursor)
        def stamp(seconds):
            millis = int(seconds * 1000)
            hours, millis = divmod(millis, 3600000)
            minutes, millis = divmod(millis, 60000)
            seconds, millis = divmod(millis, 1000)
            return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"
        lines.extend([str(index), f"{stamp(start)} --> {stamp(end)}", chunk, ""])
    target = Path("uploads") / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return str(target)
