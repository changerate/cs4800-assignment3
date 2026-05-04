#!/usr/bin/env python3
"""Load backend/.env and call OpenAI once (no secrets printed)."""
import os
from pathlib import Path

from dotenv import load_dotenv

_backend = Path(__file__).resolve().parent.parent
_env_path = _backend / ".env"
# Default dotenv does not override shell env. This script uses override=True
# so the file matches what you are testing; Flask still uses default order.
had_key_before = bool(os.environ.get("OPENAI_API_KEY"))
load_dotenv(_env_path, override=True)

from openai import OpenAI  # noqa: E402


def main() -> None:
    k = (os.environ.get("OPENAI_API_KEY") or "").strip()
    print("OPENAI_API_KEY was set in shell before .env:", had_key_before)
    print("OPENAI_API_KEY set (after loading .env with override=True):", bool(k))
    if k:
        print("Prefix:", k[:12], "... length:", len(k))
    model = (
        os.environ.get("OPENAI_MODEL")
        or os.environ.get("OPENAI_SUMMARY_MODEL")
        or "gpt-4o-mini"
    ).strip()
    try:
        c = OpenAI(api_key=k)
        r = c.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: ok"}],
            max_tokens=10,
        )
        print("API OK:", (r.choices[0].message.content or "").strip())
    except Exception as exc:
        print("API error:", type(exc).__name__, exc)


if __name__ == "__main__":
    main()
