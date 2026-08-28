#!/usr/bin/env python3
"""
Replace affiliate-link placeholders in the built website with real tracked URLs.

Site content never hardcodes a live affiliate URL. Instead every CTA uses:
    href="#affiliate:program-slug"
This script reads data/affiliate-links.csv (raw_affiliate_url populated once a
human has joined the program - see ACCESS_NEEDED.md #5), appends UTM
parameters, and rewrites every matching href across website/public/**/*.html
in place. Safe to re-run; a program with no raw_affiliate_url yet is left
untouched (and reported) rather than breaking the placeholder.

Usage:
    python3 automation/apply_affiliate_links.py [--dry-run]
"""
import csv
import glob
import re
import sys
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

REPO_ROOT = Path(__file__).resolve().parent.parent
LINKS_CSV = REPO_ROOT / "data" / "affiliate-links.csv"
SITE_GLOB = str(REPO_ROOT / "website" / "public" / "**" / "*.html")

UTM_DEFAULTS = {
    "utm_source": "ownedsite",
    "utm_medium": "affiliate",
}


def load_links():
    links = {}
    with open(LINKS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            links[row["placeholder_id"]] = row
    return links


def with_utm(url: str, campaign: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query.update(UTM_DEFAULTS)
    query["utm_campaign"] = campaign
    return urlunsplit(parts._replace(query=urlencode(query)))


def main():
    dry_run = "--dry-run" in sys.argv
    links = load_links()
    unresolved = set()
    changed_files = 0

    pattern = re.compile(r'href="#affiliate:([a-z0-9\-]+)"')

    for path_str in glob.glob(SITE_GLOB, recursive=True):
        path = Path(path_str)
        text = path.read_text(encoding="utf-8")

        def repl(match):
            slug = match.group(1)
            placeholder_id = f"affiliate:{slug}"
            row = links.get(placeholder_id)
            if not row or not row.get("raw_affiliate_url"):
                unresolved.add(placeholder_id)
                return match.group(0)  # leave placeholder untouched
            campaign = path.stem
            return f'href="{with_utm(row["raw_affiliate_url"], campaign)}"'

        new_text = pattern.sub(repl, text)
        if new_text != text:
            changed_files += 1
            if not dry_run:
                path.write_text(new_text, encoding="utf-8")

    print(f"Files updated: {changed_files}{' (dry run, not written)' if dry_run else ''}")
    if unresolved:
        print("Still-pending placeholders (no raw_affiliate_url in data/affiliate-links.csv yet):")
        for slug in sorted(unresolved):
            print(f"  - {slug}")


if __name__ == "__main__":
    main()
