#!/usr/bin/env python3
"""Polling fallback: detect launch triggers by reading group history.

Use this when you cannot run the long-connection listener (no always-on
process, or the event subscription is not set up yet). A scheduled agent or
cron job calls it; it reads the last N messages of one group, finds messages
that @mention the app bot AND contain a link, dedupes against a state file so
each link fires once, and prints new triggers as JSON. Pair it with
handle_launch.py to act on them:

  python3 scripts/poll_trigger.py --chat-id oc_XXXX | \
    jq -r '.new_triggers[] | [.link, .chat_id] | @tsv' | \
    while IFS=$'\t' read -r link chat; do
      python3 scripts/handle_launch.py "$link" "$chat"; done

Needs tenant-token read access to the group (the "obtain messages in group
chats" scope, and the bot in the group).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _lark_api import api, bot_open_id, trigger_config

URL_RE = re.compile(r"https?://\S+")
DEFAULT_STATE = Path.home() / ".launch_trigger_state.json"


def message_text(item: dict) -> str:
    """Flatten a Lark message into searchable text (covers text + rich-text post)."""
    content = (item.get("body") or {}).get("content", "") or ""
    mtype = item.get("msg_type", "")
    try:
        data = json.loads(content)
    except Exception:
        return content
    if mtype == "text":
        return data.get("text", content)
    if mtype == "post":
        parts = []

        def walk(lines):
            for line in lines or []:
                for el in line:
                    if el.get("tag") == "text":
                        parts.append(el.get("text", ""))
                    elif el.get("tag") == "a":
                        parts.append(el.get("href", ""))

        if isinstance(data, dict):
            if isinstance(data.get("content"), list):
                # cloud format: {"title": ..., "content": [[...]]}
                walk(data["content"])
            else:
                # i18n format: {"zh_cn": {"title": ..., "content": [[...]]}, ...}
                for value in data.values():
                    if isinstance(value, dict) and isinstance(value.get("content"), list):
                        walk(value["content"])
                    elif isinstance(value, list):
                        walk(value)
        return " ".join(parts)
    return content


def mentions_bot(item: dict, target_open_id: str) -> bool:
    for m in (item.get("mentions") or []):
        mid = m.get("id")
        if mid == target_open_id or (isinstance(mid, dict) and mid.get("open_id") == target_open_id):
            return True
    return False


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"seen_message_ids": [], "fired_links": []}


def save_state(path: Path, state: dict) -> None:
    state["seen_message_ids"] = state["seen_message_ids"][-500:]
    state["fired_links"] = state["fired_links"][-200:]
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chat-id", required=True, help="group chat_id, e.g. oc_...")
    ap.add_argument("--state-file", default=str(DEFAULT_STATE))
    ap.add_argument("--limit", type=int, default=30, help="messages to scan per poll")
    ap.add_argument("--bot-open-id", default="",
                    help="only fire on @mentions of this bot (default: this app's bot)")
    args = ap.parse_args()

    cfg = trigger_config()
    target = args.bot_open_id or cfg.get("bot_open_id") or bot_open_id()
    url_filter = cfg.get("url_filter", "")

    resp = api("GET", "/im/v1/messages", params={
        "container_id_type": "chat", "container_id": args.chat_id,
        "page_size": args.limit, "sort_type": "ByCreateTimeDesc",
    })
    items = resp.get("items") or []

    state = load_state(Path(args.state_file))
    seen = set(state["seen_message_ids"])
    fired = set(state["fired_links"])
    triggers = []

    for it in items:
        mid = it.get("message_id")
        if not mid or mid in seen:
            continue
        seen.add(mid)
        state["seen_message_ids"].append(mid)
        if not mentions_bot(it, target):
            continue
        for link in URL_RE.findall(message_text(it)):
            link = link.rstrip(").,]}>\"'")
            if url_filter and url_filter not in link:
                continue
            if link in fired:
                continue
            fired.add(link)
            state["fired_links"].append(link)
            triggers.append({
                "message_id": mid,
                "link": link,
                "chat_id": args.chat_id,
                "create_time": it.get("create_time", ""),
            })

    save_state(Path(args.state_file), state)
    print(json.dumps({"new_triggers": triggers}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
