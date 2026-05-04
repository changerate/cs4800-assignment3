from __future__ import annotations

import os
import re

from openai import OpenAI

_DEFAULT_MODEL = "gpt-4o-mini"
_MAX_OUT_CHARS = 500


def summarize_title(title: str) -> str:
    """Return a short plain-English line describing the paper from its title only."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    model = (
        os.environ.get("OPENAI_MODEL")
        or os.environ.get("OPENAI_SUMMARY_MODEL")
        or _DEFAULT_MODEL
    ).strip()
    client = OpenAI(api_key=key)
    system = (
        "You describe academic paper titles in one short plain-English sentence: "
        "what the work is about. No markdown, no quotes, no title repetition. "
        f"Max about 200 characters."
    )
    user = f"Title: {title.strip()}"
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=120,
        temperature=0.3,
    )
    text = (resp.choices[0].message.content or "").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > _MAX_OUT_CHARS:
        text = text[:_MAX_OUT_CHARS].rsplit(" ", 1)[0] + "…"
    return text
