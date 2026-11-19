"""Verify the generated, JavaScript-independent routes and their catalog."""

import json
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlsplit

from render import BASE


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = set()
        self.links = []
        self.text = []
        self.in_main = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "main":
            self.in_main = True
        if attrs.get("id"):
            self.targets.add(attrs["id"])
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.links.append(attrs[attr])

    def handle_data(self, data):
        if self.in_main:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False


def check_site(root, works):
    problems = []
    catalog = json.loads((root / "data/works.json").read_text(encoding="utf-8"))
    if catalog != works:
        problems.append("The published catalog differs from the build input.")

    pages = {}
    for file in root.rglob("*.html"):
        page = Page()
        page.feed(file.read_text(encoding="utf-8"))
        pages[file] = page

    hostname = urlsplit(BASE).netloc
    for file, page in pages.items():
        base = f"{BASE}/{file.relative_to(root).as_posix()}"
        for link in page.links:
            absolute = urlsplit(urljoin(base, link))
            # The CV repository publishes its own Pages project under this prefix.
            if absolute.netloc != hostname or absolute.path.startswith("/CV/"):
                continue
            target = root / unquote(absolute.path).lstrip("/")
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                problems.append(f"{file.relative_to(root)}: missing {link}")
            elif absolute.fragment and target in pages:
                if unquote(absolute.fragment) not in pages[target].targets:
                    problems.append(f"{file.relative_to(root)}: missing anchor {link}")

    for work in works:
        route = urlsplit(work["url"]).path.strip("/")
        page = pages.get(root / unquote(route) / "index.html")
        if page is None or work["title"] not in " ".join(page.text):
            problems.append(f"{work['id']}: missing title in static HTML at /{route}/")
    if problems:
        raise ValueError("\n".join(problems))
