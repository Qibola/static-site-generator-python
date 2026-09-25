# static-site-generator-python

A small Python CLI that turns a folder of Markdown files + a template into a static HTML site.

## Setup

```
pip install -r requirements.txt
```

## Usage

```
python ssg/generate.py --content content --output output
```

This will read all `.md` files in `content/`, render each one through the shared HTML template, and write the result to `output/`.

## Roadmap

- [x] Scaffold: README, requirements.txt, .gitignore, content/templates/static folders
- [ ] Parse a single Markdown file to HTML via a shared template
- [ ] Build a multi-page site with shared navigation across pages
- [ ] Add tag pages and an RSS feed
- [ ] CSS theme + polish
