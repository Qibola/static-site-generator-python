# static-site-generator-python

A small Python CLI that turns a folder of Markdown files + a template into a static HTML site.

## Setup

```
pip install -r requirements.txt
```

## Usage (current: single-file rendering)

```
python ssg/generate.py --content content/hello-world.md --output output/hello-world.html
```

This reads one Markdown file, pulls simple `key: value` front matter (e.g. `title`,
`date`) off the top, converts the body to HTML, and renders it into
`templates/page.html`. Looping over a whole `content/` directory to build a
multi-page site is the next roadmap step.

## Roadmap

- [x] Scaffold: README, requirements.txt, .gitignore, content/templates/static folders
- [x] Parse a single Markdown file to HTML via a shared template
- [ ] Build a multi-page site with shared navigation across pages
- [ ] Add tag pages and an RSS feed
- [ ] CSS theme + polish
