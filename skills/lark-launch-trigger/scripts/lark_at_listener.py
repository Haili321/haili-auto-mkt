#!/usr/bin/env python3
"""Instant @mention listener for Lark, via long connection (WebSocket).

No public server and no polling: this process dials OUT to Lark and receives
im.message.receive_v1 events in real time (about one second from a teammate
pressing send to the event arriving here). When the app's bot is @mentioned
together with a product link, the link goes to handle_launch.run_launch:
prepared models get a reviewer TEST email immediately, new models are queued
for a compose agent.

One-time console setup (details + traps: references/event-subscription.md):
  1. Events & Callbacks: subscription mode = persistent connection.
  2. Add the event "Message received" (im.message.receive_v1).
  3. Publish an app version. Events only flow after release.
  4. @ the APP's own bot in the group, not a custom webhook bot.

Run from a working dir holding lark_config.json and trigger_config.json:

  python3 scripts/lark_at_listener.py            # foreground
  bash deploy/install.sh "$PWD"                  # 24/7 via launchd (macOS)

Requires: pip install lark-oapi
"""
from __future__ import annotations

import datetime
import json
import re
import threading

import lark_oapi as lark

from _lark_api import bot_open_id, lark_config, trigger_config
from handle_launch import run_launch

URL_RE = re.compile(r"https?://\S+")
_SEEN: set = set()  # message_ids already handled (dedup redelivery / double @)

CFG = trigger_config()
LC = lark_config()
BOT_OPEN_ID = CFG.get("bot_open_id") or bot_open_id()
URL_FILTER = CFG.get("url_filter", "")


def _now() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def _extract_text(mtype: str, content: str) -> str:
    """Flatten a message into searchable text (covers text + rich-text post)."""
    try:
        data = json.loads(content)
    except Exception:
        return content
    if mtype == "text":
        return data.get("text", content)
    if mtype == "post":
        parts = []
        for line in data.get("content", []):
            for el in line:
                if el.get("tag") == "text":
                    parts.append(el.get("text", ""))
                elif el.get("tag") == "a":
                    parts.append(el.get("href", ""))
        return " ".join(parts)
    return content


def on_message(data: "lark.im.v1.P2ImMessageReceiveV1") -> None:
    try:
        msg = data.event.message
        text = _extract_text(msg.message_type, msg.content or "{}")
        mentions = msg.mentions or []
        at_bot = any(getattr(m.id, "open_id", None) == BOT_OPEN_ID for m in mentions)
        urls = [u.rstrip(").,]}>\"'") for u in URL_RE.findall(text)]
        if URL_FILTER:
            urls = [u for u in urls if URL_FILTER in u]
        print(f"[{_now()}] EVENT chat={msg.chat_id} type={msg.message_type} "
              f"@bot={at_bot} urls={urls[:1]} text={text[:100]!r}", flush=True)
        if at_bot and urls:
            mid = getattr(msg, "message_id", "") or ""
            if mid and mid in _SEEN:
                return
            _SEEN.add(mid)
            print(f"[{_now()}]   -> TRIGGER: launching on {urls[0]}", flush=True)
            threading.Thread(target=run_launch, args=(urls[0], msg.chat_id),
                             daemon=True).start()
        elif at_bot:
            print(f"[{_now()}]   -> @bot but no matching link (not a trigger)", flush=True)
    except Exception as e:
        print(f"[{_now()}] handler error: {e}", flush=True)


def main() -> None:
    handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(on_message)
        .build()
    )
    domain = lark.FEISHU_DOMAIN if CFG.get("feishu") else lark.LARK_DOMAIN
    print(f"[{_now()}] listener for bot {BOT_OPEN_ID}; connecting to {domain} ...",
          flush=True)
    client = lark.ws.Client(
        LC["app_id"], LC["app_secret"],
        event_handler=handler, log_level=lark.LogLevel.INFO,
        domain=domain, auto_reconnect=True,
    )
    client.start()  # blocks, maintains the connection, dispatches events


if __name__ == "__main__":
    main()
