"""Render the homepage from the public catalog and profile, without client-side JavaScript."""

import argparse
import json
import posixpath
import re
import shutil
from datetime import date
from html import escape
from itertools import groupby
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://hoshinokeisuke.github.io"
CV = "https://raw.githubusercontent.com/HoshinoKeisuke/CV/pdf/main.pdf"
SECTIONS = {"paper": "Papers", "talk": "Talks", "note": "Notes"}
JSON_PATH = "/data/works.json"


def anchor(label, url, attributes=""):
    return f'<a href="{escape(url, quote=True)}"{attributes}>{escape(label)}</a>'


def inline_markdown(line):
    """Render the plain text and Markdown links used in the profile."""
    parts = []
    start = 0
    for match in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", line):
        parts.append(escape(line[start:match.start()]))
        parts.append(anchor(*match.groups()))
        start = match.end()
    parts.append(escape(line[start:]))
    return "".join(parts)


def profile_blocks():
    """The opening paragraph introduces the home page; Contact starts with the primary address."""
    source = (ROOT / "site/profile.md").read_text(encoding="utf-8")
    email = source.split("\n## Contact\n\n", 1)[1].split("\n\n", 1)[0].strip()
    blocks = []
    for block in source.strip().split("\n\n"):
        if block.startswith("## "):
            blocks.append(f"<h2>{inline_markdown(block[3:])}</h2>")
        elif block.startswith("- "):
            items = "".join(f"<li>{inline_markdown(line[2:])}</li>" for line in block.splitlines())
            blocks.append(f"<ul>{items}</ul>")
        else:
            blocks.append(f"<p>{inline_markdown(' '.join(block.splitlines()))}</p>")
    return blocks, email


def navigation(active, path="/"):
    links = []
    for title in SECTIONS.values():
        target = f"/{title.lower()}/"
        current = ""
        if active == title:
            current = ' aria-current="page"' if target == path else ' aria-current="location"'
        links.append(anchor(title, target, current))
    links.append(anchor("CV", CV, ' type="application/pdf"'))
    return '<nav aria-label="Main">' + "".join(links) + "</nav>"


def document(path, title, description, content, section=None, structured=None):
    caption = "Keisuke Hoshino | 星野 恵佑" if path == "/" else f"{title} · Keisuke Hoshino"
    header = ""
    if path != "/":
        header = ('<header class="masthead">' + anchor("Keisuke Hoshino", "/", ' class="name"')
                  + navigation(section, path) + "</header>")
    metadata = {"@context": "https://schema.org", "@type": "WebPage", "url": BASE + path,
                "name": title, "description": description}
    if structured:
        metadata.update(structured)
    json_ld = json.dumps(metadata, ensure_ascii=False).replace("<", "\\u003c")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#b5bcba">
  <title>{escape(caption)}</title>
  <meta name="description" content="{escape(description, quote=True)}">
  <link rel="canonical" href="{escape(BASE + path, quote=True)}">
  <link rel="alternate" type="application/json" href="{JSON_PATH}" title="Complete research catalog">
  <link rel="stylesheet" href="{posixpath.relpath('/assets/site.css', path)}">
  <script type="application/ld+json">{json_ld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header}
{content}
</body>
</html>
"""


def home(intro, email):
    return f"""<main id="main" class="home">
<h1>Keisuke Hoshino<span lang="ja">星野 恵佑</span></h1>
<div class="intro">{intro}</div>
{navigation(None)}
<p class="home-contact"><span>{escape(email)}</span>{anchor("Profile", "/profile/")}</p>
</main>"""


def date_label(value):
    if not value or len(value) == 4:
        return value or ""
    if len(value) == 7:
        return date.fromisoformat(value + "-01").strftime("%B %Y")
    full = date.fromisoformat(value)
    return f"{full.day} {full:%B %Y}"


def time_tag(value):
    return f'<time datetime="{escape(value)}">{escape(date_label(value))}</time>' if value else ""


def lang_attr(title):
    return ' lang="ja"' if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", title) else ""


def resources(links):
    if not links:
        return ""
    return '<span class="item-links">' + "".join(anchor(link["label"], link["url"]) for link in links) + "</span>"


def list_item(work):
    attrs = ' class="item-title"' + lang_attr(work["title"])
    title = anchor(work["title"], urlsplit(work["url"]).path, attrs)
    if work["type"] == "paper":
        authors = escape(", ".join(work["authors"]))
        venue = escape(work.get("venue") or (work.get("status") or "").capitalize())
        entry = f'<p class="item-info">{authors}</p>' if authors else ""
        kinds = {"doi", "arxiv", "pdf"}
    elif work["type"] == "talk":
        entry = ""
        venue = " · ".join(filter(None, [escape(work.get("venue") or ""), time_tag(work.get("date"))]))
        kinds = {"slides", "video"}
    else:
        entry = ""
        venue = ""
        kinds = None
    links = resources([link for link in work["links"] if kinds is None or link["kind"].lower() in kinds])
    if venue or links:
        entry += f'<p class="item-info">{venue}{links}</p>'
    return f"<li>{title}{entry}</li>"


def listing(section, works):
    groups = []
    for year, records in groupby(works, key=lambda w: (w.get("date") or "")[:4]):
        rows = "".join(list_item(w) for w in records)
        entries = f'<ol class="work-list">{rows}</ol>'
        if year:
            groups.append(f'<section class="year-group"><h2>{escape(year)}</h2>{entries}</section>')
        else:
            groups.append(entries)
    return (f'<main id="main" class="page"><h1>{section}</h1>{"".join(groups)}'
            f'<footer class="data-link">{anchor("Data (JSON)", JSON_PATH)}</footer></main>')


def citation(work):
    parts = [work.get("venue") or (work.get("status") or "").capitalize()]
    volume = work.get("volume", "")
    if work.get("issue"):
        volume += f'({work["issue"]})'
    parts.extend([volume, work.get("pages")])
    return escape(", ".join(filter(None, parts)))


def detail(work, by_id):
    kind = work["type"]
    content = [f'<h1{lang_attr(work["title"])}>{escape(work["title"])}</h1>']
    alternate = work.get("subtitle") or work.get("alternate_title")
    if alternate:
        content.append(f'<p class="translation"{lang_attr(alternate)}>{escape(alternate)}</p>')
    if work["authors"]:
        content.append(f'<p>{escape(", ".join(work["authors"]))}</p>')
    venue = citation(work) if kind == "paper" else escape(work.get("venue") or "")
    info = " · ".join(filter(None, [venue, time_tag(work.get("date"))]))
    if info:
        content.append(f'<p class="item-info">{info}</p>')
    if work.get("location") and work["location"] not in (work.get("venue") or ""):
        content.append(f'<p class="item-info">{escape(work["location"])}</p>')
    if work.get("program_date") and work["program_date"] != work.get("date"):
        content.append(f'<p class="item-info">The organizer’s program lists {time_tag(work["program_date"])}.</p>')
    if work.get("description"):
        content.append(f'<p>{escape(work["description"])}</p>')
    if work["links"]:
        content.append(f'<p>{resources(work["links"])}</p>')
    if work["related"]:
        rows = []
        for other_id in work["related"]:
            other = by_id[other_id]
            link = anchor(other["title"], urlsplit(other["url"]).path, lang_attr(other["title"]))
            context = " · ".join(filter(None, [other["type"].capitalize(), escape(other.get("venue") or ""),
                                              time_tag(other.get("date"))]))
            rows.append(f'<li>{link}<p class="item-info">{context}</p></li>')
        content.append(f'<section class="related"><h2>Related works</h2><ul>{"".join(rows)}</ul></section>')
    footer = []
    if work.get("updated"):
        footer.append(f'Record updated {time_tag(work["updated"])}')
    if work.get("source"):
        footer.append(anchor("Source (BibTeX)", work["source"]))
    if footer:
        content.append('<footer class="record-date">' + ' · '.join(footer) + '</footer>')
    entity_type = {"paper": "ScholarlyArticle", "talk": "Event", "note": "CreativeWork"}[kind]
    entity = {"@type": entity_type, "@id": work["url"] + "#work", "name": work["title"]}
    if work["authors"] and kind != "talk":
        entity["author"] = [{"@type": "Person", "name": name} for name in work["authors"]]
    if work.get("date"):
        field = "startDate" if kind == "talk" else "datePublished"
        entity[field] = work["date"]
    if work.get("language"):
        entity["inLanguage"] = work["language"]
    if work.get("description"):
        entity["description"] = work["description"]
    metadata = {"mainEntity": entity}
    if work.get("updated"):
        metadata["dateModified"] = work["updated"]
    return '<main id="main" class="page detail">' + "".join(content) + "</main>", metadata


def render(works, output_dir):
    """Write the public site to an empty staging directory, leaving the source untouched."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    by_id = {w["id"]: w for w in works}
    blocks, email = profile_blocks()
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    def page(path, title, description, content, sheet=None, metadata=None):
        folder = output / path.strip("/")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(document(path, title, description, content, sheet, metadata), encoding="utf-8")
        node = ET.SubElement(sitemap, "url")
        ET.SubElement(node, "loc").text = BASE + path
        if metadata and metadata.get("dateModified"):
            ET.SubElement(node, "lastmod").text = metadata["dateModified"]

    bio = ("Keisuke Hoshino (星野 恵佑), a researcher in category theory at the "
           "Research Institute for Mathematical Sciences, Kyoto University.")
    page("/", "Keisuke Hoshino", bio, home(blocks[0], email))
    page("/profile/", "Profile", bio, '<main id="main" class="page"><h1>Profile</h1>'
         f'<div class="prose">{"".join(blocks)}</div></main>')
    for kind, section in SECTIONS.items():
        items = sorted((w for w in works if w["type"] == kind), key=lambda w: w.get("date") or "", reverse=True)
        if kind == "note":
            items.sort(key=lambda w: w.get("resource_type") == "collection")
        page(f"/{section.lower()}/", section, f"{section} by Keisuke Hoshino.", listing(section, items), section)
    for work in works:
        body, metadata = detail(work, by_id)
        description = work.get("description") or ". ".join(filter(None, [work["title"], work.get("venue"), work.get("date")]))
        page(urlsplit(work["url"]).path, work["title"], description, body, SECTIONS[work["type"]], metadata)
    data = output / "data"
    data.mkdir(exist_ok=True)
    (data / "works.json").write_text(json.dumps(works, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "site/site.css", assets / "site.css")
    shutil.copytree(ROOT / "assets/fonts", assets / "fonts", dirs_exist_ok=True)
    ET.indent(sitemap)
    ET.ElementTree(sitemap).write(output / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path, help="JSON array from catalog.py")
    parser.add_argument("output", type=Path, help="empty staging directory")
    args = parser.parse_args()
    render(json.loads(args.catalog.read_text(encoding="utf-8")), args.output)
