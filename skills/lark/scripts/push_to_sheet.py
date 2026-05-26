#!/usr/bin/env python3
"""Push JSON data into a Lark spreadsheet range.

Supports two input shapes:

1. A 2D array of values (rows of cells):
       [["name", "score"], ["Alice", 95], ["Bob", 82]]

2. A list of dicts. Provide --columns to project keys into a 2D array:
       [{"name": "Alice", "score": 95}, {"name": "Bob", "score": 82}]
       --columns name,score

The target range is anchored at --range and grows to fit the data. The
script overwrites cells in the resulting range; it does not insert rows.

Usage:
    push_to_sheet.py --sheet-token SHEET_TOKEN --range 'Sheet1!A1' \
        --json-file ./rows.json --columns name,score

    push_to_sheet.py --sheet-token SHEET_TOKEN --range 'Sheet1!A1' \
        --json-file ./grid.json

    push_to_sheet.py --sheet-token SHEET_TOKEN --range 'Sheet1!A1' \
        --header --json-file ./rows.json --columns name,score
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from lark_client import LarkClient

RANGE_PREFIX_RE = re.compile(r"^(.+!)([A-Z]+)(\d+)$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--sheet-token", required=True, help="Spreadsheet token (from URL).")
    p.add_argument(
        "--range",
        required=True,
        help="Anchor cell, e.g. 'Sheet1!A1'. Range expands to fit data.",
    )
    p.add_argument("--json-file", required=True, type=Path, help="Path to input JSON.")
    p.add_argument(
        "--columns",
        help="Comma-separated keys to project from a list of dicts.",
    )
    p.add_argument(
        "--header",
        action="store_true",
        help="When projecting dicts, prepend the column names as the first row.",
    )
    p.add_argument(
        "--as-tenant",
        action="store_true",
        help="Use tenant token (default uses user token).",
    )
    return p.parse_args()


def load_grid(args: argparse.Namespace) -> list[list[Any]]:
    raw = json.loads(args.json_file.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit("Input JSON must be a list.")
    if not raw:
        raise SystemExit("Input JSON is empty.")

    if isinstance(raw[0], list):
        return raw

    if isinstance(raw[0], dict):
        if not args.columns:
            raise SystemExit(
                "Input is a list of dicts; pass --columns to project keys."
            )
        cols = [c.strip() for c in args.columns.split(",") if c.strip()]
        grid = [[row.get(c, "") for c in cols] for row in raw]
        if args.header:
            grid.insert(0, cols)
        return grid

    raise SystemExit(f"Unsupported input element type: {type(raw[0]).__name__}.")


def expand_range(anchor: str, rows: int, cols: int) -> str:
    """Turn 'Sheet1!A1' into 'Sheet1!A1:C5' for a 5x3 grid."""
    match = RANGE_PREFIX_RE.match(anchor)
    if not match:
        return anchor
    prefix, col, row = match.groups()
    end_col = _shift_col(col, cols - 1)
    end_row = int(row) + rows - 1
    return f"{prefix}{col}{row}:{end_col}{end_row}"


def _shift_col(col: str, by: int) -> str:
    """A + 0 -> A. A + 1 -> B. Z + 1 -> AA."""
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    n += by
    out = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(ord("A") + r) + out
    return out


def main() -> int:
    args = parse_args()
    grid = load_grid(args)
    rows = len(grid)
    cols = max(len(r) for r in grid)
    full_range = expand_range(args.range, rows, cols)

    client = LarkClient()
    result = client.update_sheet_values(
        args.sheet_token,
        full_range,
        grid,
        as_user=not args.as_tenant,
    )
    print(json.dumps({
        "range": full_range,
        "rows": rows,
        "cols": cols,
        "lark_response": result,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
