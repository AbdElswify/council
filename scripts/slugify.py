# scripts/slugify.py
"""Filesystem-safe slug helper for council run IDs and worker dir names."""
import re

SLUG_MAX = 40
EMPTY_PLACEHOLDER = "task"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = text[:SLUG_MAX].strip("-")
    return text or EMPTY_PLACEHOLDER
