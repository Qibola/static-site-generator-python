#!/usr/bin/env python3
"""Render Markdown content into HTML pages using the shared template in
templates/page.html.

Two modes are supported:

Single file (original roadmap step)::

    python ssg/generate.py --content content/hello-world.md --output output/hello-world.html

Whole site (loops over every ``*.md`` file in a content directory and
builds a shared navigation bar linking all the pages together)::

    python ssg/generate.py --content-dir content --output-dir output
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import markdown

from frontmatter import parse as parse_frontmatter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "page.html"
STATIC_DIR = PROJECT_ROOT / "static"


def _read_page(md_path: Path) -> tuple[str, str, str]:
    """Return (title, date, content_html) for a single markdown file."""
    raw = md_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw)
    title = metadata.get("title", md_path.stem.replace("-", " ").title())
    date = metadata.get("date", "")
    content_html = markdown.markdown(body, extensions=["fenced_code"])
    return title, date, content_html


def render_markdown_file(
    md_path: Path, template_path: Path = TEMPLATE_PATH, nav_html: str = ""
) -> str:
    """Read ``md_path``, convert it to HTML, and inject it into the page template.

    ``nav_html`` is dropped into the template's ``{{ nav }}`` slot; it is
    empty by default so single-file rendering keeps working exactly as
    before.

    Returns the final HTML document as a string.
    """
    title, date, content_html = _read_page(md_path)

    template = template_path.read_text(encoding="utf-8")
    page = (
        template.replace("{{ title }}", title)
        .replace("{{ date }}", date)
        .replace("{{ content }}", content_html)
        .replace("{{ nav }}", nav_html)
    )
    return page


def _build_nav(pages: list[tuple[Path, str]], current_href: str) -> str:
    """Build a simple nav bar linking every page, highlighting the current one."""
    links = []
    for href, title in pages:
        if href == current_href:
            links.append(f'<a href="{href}" aria-current="page">{title}</a>')
        else:
            links.append(f'<a href="{href}">{title}</a>')
    return " | ".join(links)


def build_site(
    content_dir: Path, output_dir: Path, template_path: Path = TEMPLATE_PATH
) -> list[Path]:
    """Render every ``*.md`` file in ``content_dir`` into ``output_dir``.

    All rendered pages share a navigation bar linking to one another.
    Returns the list of HTML files written.
    """
    md_files = sorted(content_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No markdown files found in {content_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # First pass: collect (href, title) for every page so the nav can list them all.
    pages: list[tuple[Path, str]] = []
    page_info = {}
    for md_path in md_files:
        title, date, content_html = _read_page(md_path)
        href = md_path.stem + ".html"
        pages.append((href, title))
        page_info[md_path] = (href, title, date, content_html)

    template = template_path.read_text(encoding="utf-8")
    written = []
    for md_path in md_files:
        href, title, date, content_html = page_info[md_path]
        nav_html = _build_nav(pages, href)
        page = (
            template.replace("{{ title }}", title)
            .replace("{{ date }}", date)
            .replace("{{ content }}", content_html)
            .replace("{{ nav }}", nav_html)
        )
        out_path = output_dir / href
        out_path.write_text(page, encoding="utf-8")
        written.append(out_path)

    # Copy static assets alongside the pages so stylesheets resolve.
    if STATIC_DIR.exists():
        dest_static = output_dir / "static"
        shutil.copytree(STATIC_DIR, dest_static, dirs_exist_ok=True)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", help="Path to a single Markdown file")
    parser.add_argument("--output", help="Path to write the rendered HTML file")
    parser.add_argument(
        "--content-dir", help="Path to a directory of Markdown files (builds a full site)"
    )
    parser.add_argument(
        "--output-dir", help="Directory to write the rendered site into"
    )
    parser.add_argument(
        "--template",
        default=str(TEMPLATE_PATH),
        help="Path to the HTML template (default: templates/page.html)",
    )
    args = parser.parse_args()

    template_path = Path(args.template)

    if args.content_dir or args.output_dir:
        if not (args.content_dir and args.output_dir):
            parser.error("--content-dir and --output-dir must be used together")
        written = build_site(Path(args.content_dir), Path(args.output_dir), template_path)
        for path in written:
            print(f"Wrote {path}")
        return

    if not (args.content and args.output):
        parser.error("provide either --content/--output or --content-dir/--output-dir")

    md_path = Path(args.content)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_markdown_file(md_path, template_path)
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
