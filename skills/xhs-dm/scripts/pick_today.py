#!/usr/bin/env python3
"""Pick today's Xiaohongshu DM targets (2 or 3) from a queue file.

Outputs a minimal JSON of the selected rows so the calling assistant can act
on them with low context overhead. Marks the picked entries as `in_progress`
in the queue, with a `picked_at` timestamp. Auto-recovers any stale
`in_progress` entry whose `picked_at` is older than one hour.

Usage:
    python3 pick_today.py --queue /path/to/queue.json
    python3 pick_today.py --queue /path/to/queue.json --count 3
    python3 pick_today.py --queue /path/to/queue.json --bias 0.7

Exit codes:
    0  success (including "queue empty")
    1  bad arguments or unreadable queue
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

STALE_AFTER_SEC = 3600


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--queue", required=True, type=Path, help="Path to queue.json")
    p.add_argument(
        "--count",
        type=int,
        default=None,
        help="Fixed number of targets to pick. Overrides --bias.",
    )
    p.add_argument(
        "--bias",
        type=float,
        default=0.7,
        help="Probability of picking 2 (vs 3) when --count is not given. Default 0.7.",
    )
    return p.parse_args()


def recover_stale(targets: list[dict], now_dt: datetime) -> int:
    recovered = 0
    for t in targets:
        if t.get("status") != "in_progress":
            continue
        picked_at = t.get("picked_at")
        if not picked_at:
            continue
        try:
            age = (now_dt - datetime.fromisoformat(picked_at)).total_seconds()
        except ValueError:
            continue
        if age > STALE_AFTER_SEC:
            t["status"] = "pending"
            t.pop("picked_at", None)
            recovered += 1
    return recovered


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

    targets = q.get("targets", [])
    now_dt = datetime.now(timezone.utc)

    recovered = recover_stale(targets, now_dt)

    pending = [t for t in targets if t.get("status") == "pending"]
    if not pending:
        print(json.dumps({"error": "queue empty", "targets": []}, ensure_ascii=False))
        return 0

    if args.count is not None:
        n = max(1, args.count)
    else:
        n = 2 if random.random() < args.bias else 3
    n = min(n, len(pending))

    picked = pending[:n]
    picked_rows = {t["row"] for t in picked}

    now_iso = now_dt.isoformat()
    for t in targets:
        if t.get("row") in picked_rows:
            t["status"] = "in_progress"
            t["picked_at"] = now_iso

    args.queue.write_text(
        json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    out = {
        "count": n,
        "recovered_stale_in_progress": recovered,
        "pending_remaining_after_today": sum(
            1 for t in targets if t.get("status") == "pending"
        ),
        "targets": [
            {
                "row": t.get("row"),
                "name": t.get("name"),
                "tier": t.get("tier"),
                "top_work": (t.get("top_work") or "")[:40],
            }
            for t in picked
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
