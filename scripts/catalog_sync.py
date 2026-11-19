"""Refresh data/cv.json from a committed CV checkout. Requires Git and Pandoc 3."""

import argparse
import json
import subprocess
from pathlib import Path


def convert(source, input_format, output_format):
    return subprocess.check_output(
        ["pandoc", "--from", input_format, "--to", output_format, "--wrap=none"],
        input=source,
    ).decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="Checkout of HoshinoKeisuke/CV")
    parser.add_argument("revision", help="Commit or ref containing bibliography.bib")
    args = parser.parse_args()
    git = ["git", "-C", str(args.checkout)]
    commit = subprocess.check_output(
        [*git, "rev-parse", "--verify", args.revision + "^{commit}"], text=True
    ).strip()
    bib = subprocess.check_output([*git, "show", commit + ":bibliography.bib"])
    entries = json.loads(convert(bib, "biblatex", "csljson"))
    for entry in entries:
        for field in ("title", "title-short", "container-title"):
            value = entry.get(field, "")
            if any(marker in value for marker in ("<", "$", "&")):
                entry[field] = convert(value.encode(), "html+tex_math_dollars", "plain").strip()
    snapshot = {"revision": commit, "entries": entries}
    output = Path(__file__).resolve().parents[1] / "data" / "cv.json"
    content = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
