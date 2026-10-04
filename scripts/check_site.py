#!/usr/bin/env python3
"""Checks the built Jekyll site (_site/) for problems before it is published.

- Required pages and files exist.
- Internal links, images, scripts and stylesheets point to files that exist.
- Same-page and cross-page #anchors point to an element with that id.
- Inline <script> blocks are valid JavaScript (via `node --check`) and
  JSON-LD blocks are valid JSON.

Usage: python3 scripts/check_site.py [site_dir]   (defaults to _site)
Exits with status 1 and a list of problems if anything fails.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

REQUIRED_FILES = [
    "index.html",
    "blog/index.html",
    "blog/feed.xml",
    "sitemap.xml",
    "robots.txt",
    "cv/Franco_Secchi_CV_EN.pdf",
    "cv/Franco_Secchi_CV_ES.pdf",
]

URL_ATTRIBUTES = {"a": "href", "link": "href", "img": "src", "script": "src", "source": "src"}
EXTERNAL_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:", "javascript:", "data:")
JS_SCRIPT_TYPES = {"", "text/javascript", "module", "application/javascript"}


class PageParser(HTMLParser):
    """Collects the URLs, element ids and inline scripts of one HTML page."""

    def __init__(self):
        super().__init__()
        self.urls = []  # (tag, url, line)
        self.ids = set()
        self.scripts = []  # (type, source, line)
        self._script = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        url_attribute = URL_ATTRIBUTES.get(tag)
        if url_attribute and attributes.get(url_attribute) is not None:
            self.urls.append((tag, attributes[url_attribute], self.getpos()[0]))
        if tag == "script" and attributes.get("src") is None:
            self._script = {"type": (attributes.get("type") or "").lower(), "line": self.getpos()[0], "parts": []}

    def handle_data(self, data):
        if self._script is not None:
            self._script["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.scripts.append((self._script["type"], "".join(self._script["parts"]), self._script["line"]))
            self._script = None


def resolve(site, page, url):
    """Maps an internal URL to (file in site, anchor), or None if it is external."""
    if url.startswith(EXTERNAL_PREFIXES):
        return None
    parts = urlsplit(url)
    path = unquote(parts.path)
    if not path:
        return page, parts.fragment  # "#anchor" or "?query" on the same page
    target = site / path.lstrip("/") if path.startswith("/") else page.parent / path
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    elif not target.suffix and target.with_suffix(".html").exists():
        target = target.with_suffix(".html")
    return target, parts.fragment


def check_javascript(source, node):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(source)
        path = handle.name
    try:
        result = subprocess.run([node, "--check", path], capture_output=True, text=True)
        if result.returncode == 0:
            return None
        lines = result.stderr.strip().splitlines()
        return next((line for line in lines if "Error" in line), lines[-1])
    finally:
        Path(path).unlink()


def main():
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "_site").resolve()
    if not site.is_dir():
        sys.exit(f"{site} does not exist: run `jekyll build` first")

    problems = []
    for required in REQUIRED_FILES:
        if not (site / required).is_file():
            problems.append(f"missing required file: {required}")

    pages = {}
    for page in sorted(site.rglob("*.html")):
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        pages[page] = parser

    node = shutil.which("node")
    links_checked = 0
    for page, parser in pages.items():
        name = page.relative_to(site)

        for tag, url, line in parser.urls:
            if url in ("", "#"):
                continue
            resolved = resolve(site, page, url)
            if resolved is None:
                continue
            target, anchor = resolved
            links_checked += 1
            if not target.is_file():
                problems.append(f"{name}:{line} <{tag}> points to a missing file: {url}")
            elif anchor and target in pages and anchor not in pages[target].ids:
                problems.append(f"{name}:{line} <{tag}> points to a missing anchor: {url}")

        for script_type, source, line in parser.scripts:
            if script_type == "application/ld+json":
                try:
                    json.loads(source)
                except json.JSONDecodeError as error:
                    problems.append(f"{name}:{line} invalid JSON-LD: {error}")
            elif script_type in JS_SCRIPT_TYPES and source.strip() and node:
                error = check_javascript(source, node)
                if error:
                    problems.append(f"{name}:{line} invalid JavaScript: {error}")

    print(f"Checked {len(pages)} pages and {links_checked} internal links.")
    if not node:
        print("warning: node not found, inline JavaScript was not checked")
    if problems:
        print(f"\n{len(problems)} problem(s) found:")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
