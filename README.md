# static-site-generator-python

A small Python CLI that turns a folder of Markdown files + a template into a static HTML site.

## Setup

```
pip install -r requirements.txt
```

## Usage

Build the whole site (loops over every `*.md` file in `content/`, links
them together with a shared navigation bar, and copies `static/` assets
alongside the output):

```
python ssg/generate.py --content-dir content --output-dir output
```

Render a single Markdown file instead, without navigation:

```
python ssg/generate.py --content content/hello-world.md --output output/hello-world.html
```

Each Markdown file starts with simple `key: value` front matter (e.g.
`title`, `date`), followed by a blank line and the Markdown body. The body
is converted to HTML and rendered into `templates/page.html`.

## Roadmap

- [x] Scaffold: README, requirements.txt, .gitignore, content/templates/static folders
- [x] Parse a single Markdown file to HTML via a shared template
- [x] Build a multi-page site with shared navigation across pages
- [ ] Add tag pages and an RSS feed
- [ ] CSS theme + polish
