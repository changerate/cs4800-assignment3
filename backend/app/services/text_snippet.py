from __future__ import annotations

import re


def word_safe_teaser(text: str, max_len: int = 220) -> str:
    """Word-bounded teaser for feed summaries (matches ResearchPaper.summary behavior)."""
    raw = re.sub(r"\s+", " ", (text or "").strip())
    if len(raw) <= max_len:
        return raw
    chunk = raw[: max_len + 1]
    if " " in chunk:
        chunk = chunk.rsplit(" ", 1)[0]
    return chunk.rstrip(",;:") + "…"
