#!/usr/bin/env python3
"""Import a public image URL into the Brevo image gallery and print the hosted URL.

Brevo's API can only import an image from a PUBLIC url (no local-file upload, no
base64). The returned img.mailinblue.com url is permanent and email-safe, so use
it for headers instead of hot-linking a third-party CDN (which may expire/block).

Gotcha handled here: Brevo derives the image format from the `name` field, so the
name MUST carry a valid extension (.jpeg/.jpg/.png/.bmp/.gif). Max size 2 MB.

Loads BREVO_API_KEY from the shell env or a local .env.local in the CWD.

Usage:
  scripts/brevo_image_import.py --url https://host/path/pic.jpeg --name m3-bench
  # -> prints: https://img.mailinblue.com/<account>/images/rnb/original/<id>.jpeg
"""
from __future__ import annotations
import argparse, json, os, re, sys, urllib.error, urllib.request
from pathlib import Path

BASE = "https://api.brevo.com/v3"
VALID_EXT = ("jpeg", "jpg", "png", "bmp", "gif")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def ensure_ext(name: str, url: str) -> str:
    if name.lower().rsplit(".", 1)[-1] in VALID_EXT:
        return name
    m = re.search(r"\.(jpeg|jpg|png|bmp|gif)(?:$|[?#])", url, re.I)
    ext = m.group(1).lower() if m else "jpeg"
    return f"{name}.{ext}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True, help="public image url to import")
    ap.add_argument("--name", required=True, help="gallery name (extension auto-added)")
    args = ap.parse_args()

    load_dotenv(Path.cwd() / ".env.local")
    key = os.environ.get("BREVO_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing BREVO_API_KEY in env or .env.local")

    name = ensure_ext(args.name, args.url)
    body = json.dumps({"imageUrl": args.url, "name": name}).encode()
    req = urllib.request.Request(
        f"{BASE}/emailCampaigns/images", data=body, method="POST",
        headers={"api-key": key, "accept": "application/json",
                 "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            hosted = json.load(r).get("url")
            print(hosted)
            return 0
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"ERROR {e.code}: {e.read().decode()[:300]}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
