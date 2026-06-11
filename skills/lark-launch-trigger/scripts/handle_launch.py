#!/usr/bin/env python3
"""Launch-trigger handler: one product link in, one reviewer TEST email out.

Called by lark_at_listener.py when the app bot is @mentioned with a link
(also runnable by hand: python3 handle_launch.py <link> <chat_id>).

  KNOWN model (its slug appears in trigger_config.json "link_map"): build and
  send the prepared Brevo request as a TEST to the reviewer, then post the
  result back to the group.

  NEW model (no prepared request yet): write the trigger to the queue dir for
  a compose agent to pick up (see references/watcher-agent.md), and post an
  ack so the teammate knows it is in progress.

This handler only ever sends the single TEST email to the reviewer address.
The mass send to a contact list stays a human action in Brevo.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from _lark_api import send_text, trigger_config

HERE = Path(__file__).resolve().parent


def _brevo_script(cfg: dict) -> Path:
    """The brevo skill's sender. Default: the sibling skill in the same skills dir."""
    if cfg.get("brevo_script"):
        return Path(cfg["brevo_script"]).expanduser()
    return HERE.parents[1] / "brevo" / "scripts" / "run_brevo_email.py"


def _queue_dir(cfg: dict) -> Path:
    return Path(cfg.get("queue_dir", "launch-queue")) / "pending"


def link_to_request(cfg: dict, link: str) -> Path | None:
    for slug, req in (cfg.get("link_map") or {}).items():
        if slug in link:
            return Path(req).expanduser()
    return None


def enqueue(cfg: dict, link: str, chat_id: str) -> Path:
    pending = _queue_dir(cfg)
    pending.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", link).strip("-")[-48:]
    path = pending / f"{int(time.time())}-{slug}.json"
    path.write_text(json.dumps(
        {"link": link, "chat_id": chat_id, "queued_at": int(time.time()),
         "status": "pending"}, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_launch(link: str, chat_id: str) -> None:
    cfg = trigger_config()
    reviewer = cfg.get("reviewer_email", "")

    def say(text: str) -> None:
        try:
            send_text(chat_id, text)
        except Exception as e:  # posting back is best-effort
            print("post-back failed:", e, file=sys.stderr)

    req = link_to_request(cfg, link)

    # New model: hand off to the compose agent via the queue.
    if not req or not req.exists():
        enqueue(cfg, link, chat_id)
        say(f"Got it. {link} has no prepared email yet, so I queued it for the "
            f"compose agent to draft from the official pages. A test will follow.")
        return

    if not reviewer:
        say("trigger_config.json has no reviewer_email; not sending.")
        return

    # Known model: send the prepared TEST email right now.
    say(f"Got it. Sending the prepared launch test email for {link} ...")
    proc = subprocess.run(
        [sys.executable, str(_brevo_script(cfg)),
         "--request-file", str(req), "--send", "--test-to", reviewer],
        capture_output=True, text=True,
    )
    message_id, subject = "", ""
    try:
        out = json.loads(proc.stdout)
        subject = out.get("subject", "")
        message_id = ((out.get("send_result") or {}).get("response") or {}).get("messageId", "")
    except Exception:
        pass

    if proc.returncode == 0:
        say(f"Done. Sent the launch TEST email to {reviewer}."
            + (f" Subject: {subject}" if subject else "")
            + (f" id={message_id}" if message_id else ""))
    else:
        tail = (proc.stdout or proc.stderr or "")[-200:]
        say(f"Send FAILED for {link}. {tail}")
    print("run_launch done rc=", proc.returncode, "messageId=", message_id)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: handle_launch.py <link> <chat_id>")
    run_launch(sys.argv[1], sys.argv[2])
