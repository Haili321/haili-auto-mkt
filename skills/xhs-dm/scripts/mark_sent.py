#!/usr/bin/env python3
"""Mark queue rows as sent and append to the `sent` history list.

Usage:
    python3 mark_sent.py --queue /path/to/queue.json <row> [<row> ...]

Reads the queue, sets each given row's status to `sent`, stamps `sent_at`,
and appends a compact audit entry to `queue.json#/sent`. Prints a JSON
summary of what was marked.

If you want to mirror the result into an external system (Lark sheet, Notion,
Airtable), do not edit this script. Instead wrap it in your own driver script
that calls `mark_sent.py` first, then writes wherever you like. Keeping this
script side-effect-free over `queue.json` makes it safe to reuse.

Exit codes:
    0  success
    1  bad arguments or unreadable queue
    2  one or more requested rows not found in queue
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--queue", required=True, type=Path, help="Path to queue.json")
    p.add_argument("rows", nargs="+", type=int, help="Row numbers to mark as sent")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    try:
        q = json.loads(args.queue.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(json.dumps({"error": f"queue file not found: {args.queue}"}))
        return 1
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"queue file is not valid JSON: {exc}"}))
        return 1

    rows = sorted(set(args.rows))
    targets = q.get("targets", [])
    sent_log = q.setdefault("sent", [])

    now_iso = datetime.now(timezone.utc).isoformat()
    marked: list[dict] = []
    found_rows: set[int] = set()

    for t in targets:
        if t.get("row") in rows:
            t["status"] = "sent"
            t["sent_at"] = now_iso
            t.pop("picked_at", None)
            sent_log.append(
                {
                    "row": t.get("row"),
                    "name": t.get("name"),
                    "sent_at": now_iso,
                    "tier": t.get("tier"),
                }
            )
            marked.append({"row": t.get("row"), "name": t.get("name")})
            found_rows.add(t.get("row"))

    args.queue.write_text(
        json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    missing = [r for r in rows if r not in found_rows]
    pending = sum(1 for t in targets if t.get("status") == "pending")
    sent_total = sum(1 for t in targets if t.get("status") == "sent")

    out = {
        "marked": marked,
        "missing_rows": missing,
        "queue_pending": pending,
        "queue_sent_total": sent_total,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
