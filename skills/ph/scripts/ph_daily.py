#!/usr/bin/env python3
"""Fetch the Product Hunt daily leaderboard, group by topic, suggest
cross-topic upvote targets.

Usage:
    python3 ph_daily.py                 # today's leaderboard
    python3 ph_daily.py 2026-05-18      # specific date (UTC-anchored)
    python3 ph_daily.py --picks 5       # how many cross-topic picks to suggest

Reads PH_ACCESS_TOKEN from the environment first; falls back to
./.ph_tokens.json (a JSON object with an "access_token" field).

Set PH_TOKENS=/custom/path/to/tokens.json to override the fallback location.

Get an access token at https://www.producthunt.com/v2/oauth/applications and
issue a client-credentials or developer token. The script only reads; it
does not upvote.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import requests

API = "https://api.producthunt.com/v2/api/graphql"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "date",
        nargs="?",
        default=None,
        help="ISO date (YYYY-MM-DD). Defaults to today UTC.",
    )
    p.add_argument(
        "--picks",
        type=int,
        default=8,
        help="How many cross-topic upvote suggestions to print. Default 8.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the human-readable digest.",
    )
    return p.parse_args()


def load_token() -> str:
    env = os.environ.get("PH_ACCESS_TOKEN", "").strip()
    if env:
        return env

    override = os.environ.get("PH_TOKENS")
    path = Path(override) if override else Path.cwd() / ".ph_tokens.json"
    if not path.exists():
        raise SystemExit(
            f"Set PH_ACCESS_TOKEN env var or write a JSON file with "
            f"`access_token` at {path}."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid token JSON at {path}: {exc}") from exc
    token = data.get("access_token", "").strip()
    if not token:
        raise SystemExit(f"`access_token` missing in {path}.")
    return token


def query(graphql: str, variables: dict | None = None) -> dict:
    resp = requests.post(
        API,
        headers={
            "Authorization": f"Bearer {load_token()}",
            "Content-Type": "application/json",
            "User-Agent": "haili-auto-mkt-ph/0.1",
        },
        json={"query": graphql, "variables": variables or {}},
        timeout=20,
    )
    data = resp.json()
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {data['errors']}")
    return data.get("data", {})


def fetch_daily(date_str: str | None) -> dict:
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    posted_after = f"{date_str}T00:00:00Z"
    posted_before = f"{date_str}T23:59:59Z"

    gql = """
    query ($after: DateTime, $before: DateTime) {
      posts(
        postedAfter: $after,
        postedBefore: $before,
        order: VOTES,
        first: 30
      ) {
        edges {
          node {
            id
            name
            tagline
            slug
            votesCount
            commentsCount
            url
            topics(first: 5) {
              edges { node { name } }
            }
            user { username name }
            makers { username name }
          }
        }
      }
    }
    """
    return query(gql, {"after": posted_after, "before": posted_before})


def group_by_topic(posts: dict) -> dict:
    by_topic: dict = defaultdict(list)
    for edge in posts.get("posts", {}).get("edges", []):
        p = edge["node"]
        topics = [t["node"]["name"] for t in p.get("topics", {}).get("edges", [])]
        primary = topics[0] if topics else "Other"
        by_topic[primary].append(
            {
                "name": p["name"],
                "tagline": p["tagline"],
                "votes": p["votesCount"],
                "comments": p["commentsCount"],
                "slug": p["slug"],
                "topics": topics,
                "makers": [m["username"] for m in (p.get("makers") or [])],
            }
        )
    return by_topic


def pick_cross_topic(by_topic: dict, count: int) -> list:
    picks: list = []
    for topic in sorted(by_topic.keys()):
        if by_topic[topic]:
            picks.append((topic, by_topic[topic][0]))
        if len(picks) >= count:
            break
    return picks


def main() -> int:
    args = parse_args()
    today = args.date or datetime.date.today().isoformat()
    data = fetch_daily(args.date)
    by_topic = group_by_topic(data)

    if args.json:
        print(
            json.dumps(
                {
                    "date": today,
                    "by_topic": dict(by_topic),
                    "picks": [
                        {"topic": t, "product": p}
                        for t, p in pick_cross_topic(by_topic, args.picks)
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(f"PH {today} leaderboard (grouped by topic)\n")
    if not by_topic:
        print(
            "No data. The date may be too recent (PH boards close on Pacific time) "
            "or the API is rate-limiting."
        )
        return 0

    for topic, prods in sorted(by_topic.items()):
        print(f"=== {topic} ===")
        for p in prods:
            print(f"  [{p['votes']} up / {p['comments']} comments] {p['name']} -- {p['tagline']}")
            print(f"    https://producthunt.com/posts/{p['slug']}")
        print()

    print(f"\nSuggested upvote targets across {args.picks} different topics:")
    for topic, p in pick_cross_topic(by_topic, args.picks):
        print(f"  - [{topic}] {p['name']} ({p['votes']} up)")
        print(f"    https://producthunt.com/posts/{p['slug']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
