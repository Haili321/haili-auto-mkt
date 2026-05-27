#!/usr/bin/env python3
"""Sync xhs-dm queue.json status into a Lark spreadsheet column.

Reads `queue.json`, filters entries by status (default `sent`), and writes
a per-row mark (default `✓`) into the configured column of the configured
sheet. Useful for keeping a shared Lark tracker in sync with the local
queue without making `mark_sent.py` itself dependent on Lark.

Depends on the `lark` skill being installed alongside this one (or set
LARK_CLIENT_PATH to its scripts directory).

Usage:
    sync_to_lark.py \\
        --queue ./queue.json \\
        --sheet-token UID8sF4mBhjqostQdaRjdBdYpof \\
        --range 'Sheet1!O' \\
        --status sent

    sync_to_lark.py --queue ./queue.json --sheet-token TOKEN --range 'Sheet1!O' --dry-run

The `--range` value is a column anchor (e.g. `Sheet1!O`). Each row's
target cell is computed from the entry's `row` field in `queue.json`:
`Sheet1!O{row}` for `row=8` becomes `Sheet1!O8`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _resolve_lark_client_dir() -> Path:
    override = os.environ.get("LARK_CLIENT_PATH")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent.parent / "lark" / "scripts",
        here.parent.parent.parent / "lark" / "scripts",
    ]
    for candidate in candidates:
        if (candidate / "lark_client.py").exists():
            return candidate
    raise SystemExit(
        "Could not find lark_client.py. Install the `lark` skill next to this "
        "one, or set LARK_CLIENT_PATH to its scripts directory."
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--queue", required=True, type=Path, help="Path to queue.json")
    p.add_argument("--sheet-token", required=True, help="Lark spreadsheet token")
    p.add_argument(
        "--range",
        required=True,
        dest="col_range",
        help="Column anchor, e.g. 'Sheet1!O'. Row numbers come from queue rows.",
    )
    p.add_argument(
        "--status",
        default="sent",
        help="Only sync entries whose status equals this. Default 'sent'.",
    )
    p.add_argument(
        "--mark",
        default="✓",
        help="Value to write into each matching cell. Default '✓'.",
    )
    p.add_argument(
        "--header",
        help="Optional header value for the column (written to row 1).",
    )
    p.add_argument(
        "--as-tenant",
        action="store_true",
        help="Use tenant token (default uses user token).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intended writes without calling the Lark API.",
    )
    return p.parse_args()


def split_range(col_range: str) -> tuple[str, str]:
    """Turn 'Sheet1!O' into ('Sheet1!', 'O'). Accepts trailing '!' too."""
    if "!" not in col_range:
        raise SystemExit(
            f"--range must include sheet name, e.g. 'Sheet1!O', got {col_range!r}."
        )
    sheet, col = col_range.rsplit("!", 1)
    if not col or any(c.isdigit() for c in col):
        raise SystemExit(
            f"--range must end in a column letter, no row number, got {col_range!r}."
        )
    return f"{sheet}!", col.upper()


def main() -> int:
    args = parse_args()
    sheet_prefix, col = split_range(args.col_range)

    try:
        q = json.loads(args.queue.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(json.dumps({"error": f"queue file not found: {args.queue}"}))
        return 1
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"queue file is not valid JSON: {exc}"}))
        return 1

    targets = q.get("targets", [])
    matches = [t for t in targets if t.get("status") == args.status and t.get("row")]

    plan: list[dict] = []
    if args.header:
        plan.append({"range": f"{sheet_prefix}{col}1:{col}1", "value": args.header})
    for t in matches:
        row = t["row"]
        plan.append(
            {
                "range": f"{sheet_prefix}{col}{row}:{col}{row}",
                "value": args.mark,
                "name": t.get("name"),
                "row": row,
            }
        )

    if args.dry_run:
        print(json.dumps(
            {
                "dry_run": True,
                "status_filter": args.status,
                "mark": args.mark,
                "writes_planned": len(plan),
                "plan": plan,
            },
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    sys.path.insert(0, str(_resolve_lark_client_dir()))
    from lark_client import LarkClient  # noqa: E402

    client = LarkClient()
    written = 0
    failed: list[dict] = []
    for item in plan:
        try:
            client.update_sheet_values(
                args.sheet_token,
                item["range"],
                [[item["value"]]],
                as_user=not args.as_tenant,
            )
            written += 1
        except Exception as exc:
            failed.append({"range": item["range"], "error": str(exc)[:200]})

    print(json.dumps(
        {
            "status_filter": args.status,
            "mark": args.mark,
            "written": written,
            "failed": failed,
            "queue_total_with_status": len(matches),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
