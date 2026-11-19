"""Assemble the public catalog from the pinned CV snapshot and site material."""

import json
import re
import tomllib
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


DATA = Path(__file__).resolve().parents[1] / "data"
SITE = "https://hoshinokeisuke.github.io"
SECTIONS = {"paper": "papers", "talk": "talks", "note": "notes"}
LINK_LABELS = {
    "doi": "DOI", "arxiv": "arXiv", "pdf": "PDF", "event": "Event",
    "slides": "Slides", "video": "Recording", "archive": "Browse archive", "source": "Source",
}
CV_CATEGORIES = {
    "published": ("paper", "published"),
    "preprint": ("paper", "preprint"),
    "iv-talk": ("talk", "invited"),
    "nr-talk": ("talk", "non-refereed"),
}


def author_name(person):
    if "literal" in person:
        return person["literal"]
    parts = ("given", "dropping-particle", "non-dropping-particle", "family", "suffix")
    return " ".join(person[part] for part in parts if person.get(part))


def cv_record(entry, source, supplement):
    keywords = re.split(r"\s*[,;]\s*", entry.get("keyword", ""))
    categories = [key for key in keywords if key in CV_CATEGORIES]
    if len(categories) != 1:
        raise ValueError(f"Expected one catalog category for {entry['id']}, found {categories}")
    kind, status = CV_CATEGORIES[categories[0]]
    parts = entry["issued"]["date-parts"][0]
    issued = "-".join(f"{value:02d}" for value in parts)
    title = entry["title"]
    record = {
        "id": entry["id"], "bib_key": entry["id"], "type": kind, "title": title,
        "authors": [author_name(person) for person in entry["author"]],
        "venue": entry.get("note") if kind == "talk" else entry.get("container-title"),
        "date": issued, "status": status, "source": source,
        "language": entry.get("language", "").split("-")[0] or None,
    }
    links = {}
    if doi := entry.get("DOI"):
        record["doi"] = doi
        links["doi"] = f"https://doi.org/{doi}"
    if url := entry.get("URL"):
        parsed = urlsplit(url)
        if parsed.hostname == "arxiv.org" and parsed.path.startswith("/abs/"):
            record["arxiv"] = parsed.path.removeprefix("/abs/")
            links["arxiv"] = url
        elif parsed.hostname not in {"doi.org", "dx.doi.org"}:
            if kind == "talk":
                link_type = "event"
            elif parsed.path.lower().endswith(".pdf"):
                link_type = "pdf"
            else:
                link_type = "source"
            links[link_type] = url
    if kind == "paper":
        for original, field in (("volume", "volume"), ("issue", "issue"), ("page", "pages"), ("ISSN", "issn")):
            if original in entry:
                record[field] = entry[original]
        if "note" in entry:
            record["description"] = entry["note"]
        # BibLaTeX subtitles are folded into CSL's title; preserve the Japanese original.
        short = entry.get("title-short")
        if short and title.startswith(short + ": "):
            record["title"] = short
            record["subtitle"] = title[len(short) + 2:]
    record.update(supplement)
    if arxiv := record.get("arxiv"):
        links["arxiv"] = f"https://arxiv.org/abs/{arxiv}"
    record["links"] = {**links, **supplement.get("links", {})}
    return record


def note_record(path):
    front, body = path.read_text(encoding="utf-8").removeprefix("+++\n").split("\n+++", 1)
    record = tomllib.loads(front)
    if body.strip():
        record["description"] = body.strip()
    record.update(id=path.stem, type="note")
    if len(record.get("languages", [])) == 1:
        record["language"] = record["languages"][0]
    return record


def load_works():
    snapshot = json.loads((DATA / "cv.json").read_text(encoding="utf-8"))
    source = f"https://github.com/HoshinoKeisuke/CV/blob/{snapshot['revision']}/bibliography.bib"
    details = json.loads((DATA / "details.json").read_text(encoding="utf-8"))
    works = [cv_record(entry, source, details.pop(entry["id"], {})) for entry in snapshot["entries"]]
    if details:
        raise ValueError(f"Supplement has no corresponding CV record: {', '.join(details)}")
    works.extend(note_record(path) for path in sorted((DATA / "notes").glob("*.md")))
    by_id = {work["id"]: work for work in works}
    if len(by_id) != len(works):
        raise ValueError("Duplicate catalog ID")
    for work in works:
        key = work["id"]
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", key):
            raise ValueError(f"Invalid catalog ID: {key}")
        work["url"] = f"{SITE}/{SECTIONS[work['type']]}/{key}/"
        for field in ("date", "venue", "language", "status", "updated"):
            work.setdefault(field, None)
        if work["updated"] is not None:
            date.fromisoformat(work["updated"])
        links = []
        for kind, url in work["links"].items():
            address = urlsplit(url)
            if address.scheme not in ("https", "http") or not address.hostname:
                raise ValueError(f"Invalid {kind} link in {key}: {url}")
            links.append({"kind": kind, "url": url, "label": LINK_LABELS[kind]})
        work["links"] = links
        for related in work.setdefault("related", []):
            peers = by_id[related].setdefault("related", [])
            if key not in peers:
                peers.append(key)
    return sorted(works, key=lambda work: work["date"] or "", reverse=True)


if __name__ == "__main__":
    print(json.dumps(load_works(), ensure_ascii=False, indent=2))
