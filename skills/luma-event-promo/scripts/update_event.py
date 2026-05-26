#!/usr/bin/env python3
"""
Update fields on an existing Luma event via the admin API.

The cookies and event_api_id should be available — either passed via CLI flags
or read from environment variables LUMA_COOKIE and LUMA_EVENT_ID.

Examples
--------
Set start time + duration:
    python update_event.py --start-at 2026-06-03T17:30:00.000Z --duration 3h

Change visibility:
    python update_event.py --visibility private

Update appearance:
    python update_event.py --tint-color "#4ab2ea" --font-title ivy-mode

Set capacity:
    python update_event.py --capacity 20

Inspect current state (no changes):
    python update_event.py --get

The cookie can also be loaded from ~/.luma_cookie (one line). The event_api_id
from ~/.luma_event_id (one line).

Cookie format expected:
    luma.did=<random>; luma.auth-session-key=usr-<id>.<secret>

Both cookies are required; the auth-session-key alone is not enough — some
endpoints want the did to pass Cloudflare checks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://api.lu.ma"
COOKIE_FILE = Path.home() / ".luma_cookie"
EVENT_ID_FILE = Path.home() / ".luma_event_id"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)


def read_cookie(arg_value: str | None) -> str:
    if arg_value:
        return arg_value
    env = os.environ.get("LUMA_COOKIE")
    if env:
        return env
    if COOKIE_FILE.exists():
        return COOKIE_FILE.read_text().strip()
    sys.exit(
        "No cookie. Pass --cookie, set LUMA_COOKIE, or write the cookie to "
        f"{COOKIE_FILE}.\nFormat: 'luma.did=...; luma.auth-session-key=usr-....'"
    )


def read_event_id(arg_value: str | None) -> str:
    if arg_value:
        return arg_value
    env = os.environ.get("LUMA_EVENT_ID")
    if env:
        return env
    if EVENT_ID_FILE.exists():
        return EVENT_ID_FILE.read_text().strip()
    sys.exit(
        "No event_api_id. Pass --event-id, set LUMA_EVENT_ID, or write the id "
        f"to {EVENT_ID_FILE}.\nFormat: evt-XXXXXXXXXXXXX"
    )


def api_get(path: str, cookie: str) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={"Cookie": cookie, "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def api_post(path: str, body: dict[str, Any], cookie: str, referer: str) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Cookie": cookie,
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Origin": "https://luma.com",
            "Referer": referer,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")


def parse_duration(text: str) -> str:
    """
    Parse a friendly duration like '90m', '2h', '2h30m', '3h0m', '1d' to
    Luma's ISO 8601 format (P0Y0M{days}DT{hours}H{minutes}M0S).
    """
    text = text.strip().lower()
    if text.startswith("p") and text.endswith("s"):
        # already ISO 8601
        return text.upper()

    days = hours = minutes = 0
    m = re.match(
        r"^(?:(?P<d>\d+)d)?(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?$",
        text.replace(" ", ""),
    )
    if not m or not (m.group("d") or m.group("h") or m.group("m")):
        sys.exit(f"Could not parse duration: {text!r}. Try '90m', '2h', '2h30m', '1d'.")
    days = int(m.group("d") or 0)
    hours = int(m.group("h") or 0)
    minutes = int(m.group("m") or 0)
    return f"P0Y0M{days}DT{hours}H{minutes}M0S"


def show_summary(event: dict[str, Any]) -> None:
    fields = [
        "api_id", "url", "name", "visibility",
        "start_at", "end_at", "duration_interval", "timezone",
        "max_capacity", "tint_color", "font_title", "cover_url",
    ]
    print("Current event state:")
    for f in fields:
        if f in event:
            print(f"  {f}: {event[f]}")
    addr = event.get("geo_address_info") or {}
    if addr:
        print(f"  address: {addr.get('full_address')}")
        print(f"  further_instructions: {addr.get('description')}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cookie", help="luma.did=...; luma.auth-session-key=...")
    p.add_argument("--event-id", help="evt-XXXXXXXXXXXXX")

    p.add_argument("--get", action="store_true", help="Just fetch and print current state")

    p.add_argument("--name", help="Event title")
    p.add_argument("--start-at", help="ISO datetime in UTC, e.g. 2026-06-03T17:30:00.000Z")
    p.add_argument("--duration", help="'90m', '2h', '2h30m', '3h', '1d', or raw ISO 8601")
    p.add_argument("--timezone", help="IANA timezone name, e.g. Europe/London")
    p.add_argument("--visibility", choices=["public", "private"])
    p.add_argument("--capacity", type=int, help="max_capacity (omit or 0 for unlimited)")
    p.add_argument("--tint-color", help='Hex like "#4ab2ea"')
    p.add_argument("--font-title", help='e.g. "ivy-mode", or "default" for null')
    p.add_argument("--cover-url", help="Must be on images.lumacdn.com")
    p.add_argument("--description-json", help="Path to a JSON file containing description_mirror")

    args = p.parse_args()

    cookie = read_cookie(args.cookie)
    event_id = read_event_id(args.event_id)
    referer = f"https://luma.com/event/manage/{event_id}"

    if args.get:
        data = api_get(f"/event/admin/get?event_api_id={event_id}", cookie)
        show_summary(data["event"])
        return

    payload: dict[str, Any] = {"event_api_id": event_id}
    if args.name:
        payload["name"] = args.name
    if args.start_at:
        payload["start_at"] = args.start_at
    if args.duration:
        payload["duration_interval"] = parse_duration(args.duration)
    if args.timezone:
        payload["timezone"] = args.timezone
    if args.visibility:
        payload["visibility"] = args.visibility
    if args.capacity is not None:
        payload["max_capacity"] = args.capacity if args.capacity > 0 else None
    if args.tint_color:
        payload["tint_color"] = args.tint_color
    if args.font_title:
        payload["font_title"] = None if args.font_title == "default" else args.font_title
    if args.cover_url:
        if "images.lumacdn.com" not in args.cover_url:
            sys.exit("cover_url must point to images.lumacdn.com. Upload through the UI first.")
        payload["cover_url"] = args.cover_url
    if args.description_json:
        with open(args.description_json) as f:
            payload["description_mirror"] = json.load(f)

    if len(payload) == 1:
        sys.exit("Nothing to update. Pass at least one field, or use --get to inspect.")

    api_post("/event/admin/update", payload, cookie, referer)
    data = api_get(f"/event/admin/get?event_api_id={event_id}", cookie)
    show_summary(data["event"])


if __name__ == "__main__":
    main()
