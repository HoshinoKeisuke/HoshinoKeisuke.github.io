"""Build the complete GitHub Pages artifact into _site/."""

from pathlib import Path
from tempfile import TemporaryDirectory

from catalog import load_works
from check_site import check_site
from render import render


ROOT = Path(__file__).resolve().parents[1]


def main():
    works = load_works()
    target = ROOT / "_site"
    with TemporaryDirectory(prefix=".homepage-build-", dir=ROOT) as staging:
        fresh = Path(staging) / "site"
        fresh.mkdir()
        render(works, fresh)
        check_site(fresh, works)
        previous = Path(staging) / "previous"
        if target.exists():
            target.rename(previous)
        try:
            fresh.rename(target)
        except OSError:
            if previous.exists() and not target.exists():
                previous.rename(target)
            raise
    print(f"Built {len(works)} records in {target}")


if __name__ == "__main__":
    main()
