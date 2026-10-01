#!/usr/bin/env python3
"""Render a single Markdown content file into an HTML page using the
shared template in templates/page.html.

Usage:
    python ssg/generate.py --content content/hello-world.md --output output/hello-world.html

This is the first rendering step in the roadmap: it handles one file at a
time. Building a full multi-page site (looping over every file in a
content/ directory, shared navigation, etc.) is a later roadmap step.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import markdown

from frontmatter import parse as parse_frontmatter

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "page.html"


def render_markdown_file(md_path: Path, template_path: Path = TEMPLATE_PATH) -> str:
    """Read ``md_path``, convert it to HTML, and inject it into the page template.

    Returns the final HTML document as a string.
    """
    raw = md_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw)

    title = metadata.get("title", md_path.stem.replace("-", " ").title())
    date = metadata.get("date", "")

    content_html = markdown.markdown(body, extensions=["fenced_code"])

    template = template_path.read_text(encoding="utf-8")
    page = (
        template.replace("{{ title }}", title)
        .replace("{{ date }}", date)
        .replace("{{ content }}", content_html)
    )
    return page


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", required=True, help="Path to a single Markdown file")
    parser.add_argument("--output", required=True, help="Path to write the rendered HTML file")
    parser.add_argument(
        "--template",
        default=str(TEMPLATE_PATH),
        help="Path to the HTML template (default: templates/page.html)",
    )
    args = parser.parse_args()

    md_path = Path(args.content)
    output_path = Path(args.output)
    template_path = Path(args.template)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_markdown_file(md_path, template_path)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
