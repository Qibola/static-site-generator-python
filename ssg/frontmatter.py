"""Tiny front-matter parser.

Expects a markdown file that starts with simple ``key: value`` metadata
lines, followed by a blank line, followed by the markdown body, e.g.::

    title: Hello World
    date: 2026-01-01

    # Hello World
    Body text here.
"""
from __future__ import annotations


def parse(text: str) -> tuple[dict, str]:
    """Split ``text`` into (metadata dict, body markdown string).

    If the file doesn't start with recognisable ``key: value`` lines,
    metadata is empty and the whole file is treated as the body.
    """
    lines = text.splitlines()
    metadata = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            break
        if ":" not in line:
            # Not a metadata line -> there's no front matter at all.
            return {}, text
        key, _, value = line.partition(":")
        metadata[key.strip().lower()] = value.strip()
        i += 1
    body = "\n".join(lines[i:])
    return metadata, body
