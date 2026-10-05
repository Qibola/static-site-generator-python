#!/usr/bin/env python3
"""Render Markdown content into HTML pages using the shared template in
templates/page.html.

Two modes are supported:

Single file (original roadmap step)::

    python ssg/generate.py --content content/hello-world.md --output output/hello-world.html

Whole site (loops over every ``*.md`` file in a content directory, builds a
shared navigation bar linking all the pages together, generates a page per
tag, and writes an RSS feed)::

    python ssg/generate.py --content-dir content --output-dir output
"""
from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import markdown

from frontmatter import parse as parse_frontmatter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "page.html"
TAG_TEMPLATE_PATH = PROJECT_ROOT / "templates" / "tag.html"
STATIC_DIR = PROJECT_ROOT / "static"

SITE_TITLE = "static-site-generator-python demo"
SITE_DESCRIPTION = "A tiny site built with static-site-generator-python."


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return slug.strip("-") or "tag"


def _parse_tags(raw: str) -> list[str]:
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _read_page(md_path: Path) -> tuple[str, str, str, list[str]]:
    """Return (title, date, content_html, tags) for a single markdown file."""
    raw = md_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw)
    title = metadata.get("title", md_path.stem.replace("-", " ").title())
    date = metadata.get("date", "")
    tags = _parse_tags(metadata.get("tags", ""))
    content_html = markdown.markdown(body, extensions=["fenced_code"])
    return title, date, content_html, tags


def _tags_html(tags: list[str]) -> str:
    if not tags:
        return ""
    links = [f'<a href="tag-{_slugify(t)}.html">#{t}</a>' for t in tags]
    return "Tags: " + ", ".join(links)


def render_markdown_file(
    md_path: Path, template_path: Path = TEMPLATE_PATH, nav_html: str = ""
) -> str:
    """Read ``md_path``, convert it to HTML, and inject it into the page template.

    ``nav_html`` is dropped into the template's ``{{ nav }}`` slot; it is
    empty by default so single-file rendering keeps working exactly as
    before.

    Returns the final HTML document as a string.
    """
    title, date, content_html, tags = _read_page(md_path)

    template = template_path.read_text(encoding="utf-8")
    page = (
        template.replace("{{ title }}", title)
        .replace("{{ date }}", date)
        .replace("{{ content }}", content_html)
        .replace("{{ nav }}", nav_html)
        .replace("{{ tags }}", _tags_html(tags))
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


def _parse_date(date_str: str) -> datetime:
    """Best-effort parse of a ``YYYY-MM-DD`` date string, defaulting to epoch."""
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _build_rss(
    page_info: dict, output_dir: Path, site_title: str = SITE_TITLE,
    site_description: str = SITE_DESCRIPTION, site_link: str = "./",
) -> Path:
    """Write an RSS 2.0 feed (``feed.xml``) listing every page, newest first."""
    entries = sorted(
        page_info.values(), key=lambda info: _parse_date(info[2]), reverse=True
    )

    items = []
    for href, title, date, content_html, _tags in entries:
        link = f"{site_link}{href}"
        pub_date = format_datetime(_parse_date(date))
        items.append(
            "    <item>\n"
            f"      <title>{escape(title)}</title>\n"
            f"      <link>{escape(link)}</link>\n"
            f"      <guid>{escape(link)}</guid>\n"
            f"      <pubDate>{pub_date}</pubDate>\n"
            f"      <description>{escape(content_html)}</description>\n"
            "    </item>"
        )

    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{escape(site_title)}</title>\n"
        f"    <link>{escape(site_link)}</link>\n"
        f"    <description>{escape(site_description)}</description>\n"
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )

    out_path = output_dir / "feed.xml"
    out_path.write_text(rss, encoding="utf-8")
    return out_path


def _build_tag_pages(
    page_info: dict, pages: list[tuple[str, str]], output_dir: Path,
    tag_template_path: Path,
) -> list[Path]:
    """Write one HTML page per tag, listing every post that carries it."""
    tags_to_entries: dict[str, list[tuple[str, str, str]]] = {}
    for href, title, date, _content_html, tags in page_info.values():
        for tag in tags:
            tags_to_entries.setdefault(tag, []).append((href, title, date))

    if not tags_to_entries:
        return []

    template = tag_template_path.read_text(encoding="utf-8")
    written = []
    for tag, entries in tags_to_entries.items():
        entries.sort(key=lambda e: e[1])
        tag_href = f"tag-{_slugify(tag)}.html"
        items_html = "\n        ".join(
            f'<li><a href="{href}">{title}</a> <span class="date">{date}</span></li>'
            for href, title, date in entries
        )
        nav_html = _build_nav(pages, tag_href)
        page = (
            template.replace("{{ title }}", f"Posts tagged ‘{tag}’")
            .replace("{{ content }}", items_html)
            .replace("{{ nav }}", nav_html)
        )
        out_path = output_dir / tag_href
        out_path.write_text(page, encoding="utf-8")
        written.append(out_path)
    return written


def build_site(
    content_dir: Path, output_dir: Path, template_path: Path = TEMPLATE_PATH,
    tag_template_path: Path = TAG_TEMPLATE_PATH,
) -> list[Path]:
    """Render every ``*.md`` file in ``content_dir`` into ``output_dir``.

    All rendered pages share a navigation bar linking to one another, each
    post's tags link to a generated tag page, and an RSS feed (``feed.xml``)
    is written listing every page newest-first.

    Returns the list of HTML/XML files written.
    """
    md_files = sorted(content_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No markdown files found in {content_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # First pass: collect (href, title) for every page so the nav can list them all.
    pages: list[tuple[str, str]] = []
    page_info = {}
    for md_path in md_files:
        title, date, content_html, tags = _read_page(md_path)
        href = md_path.stem + ".html"
        pages.append((href, title))
        page_info[md_path] = (href, title, date, content_html, tags)

    template = template_path.read_text(encoding="utf-8")
    written = []
    for md_path in md_files:
        href, title, date, content_html, tags = page_info[md_path]
        nav_html = _build_nav(pages, href)
        page = (
            template.replace("{{ title }}", title)
            .replace("{{ date }}", date)
            .replace("{{ content }}", content_html)
            .replace("{{ nav }}", nav_html)
            .replace("{{ tags }}", _tags_html(tags))
        )
        out_path = output_dir / href
        out_path.write_text(page, encoding="utf-8")
        written.append(out_path)

    written.extend(_build_tag_pages(page_info, pages, output_dir, tag_template_path))
    written.append(_build_rss(page_info, output_dir))

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
