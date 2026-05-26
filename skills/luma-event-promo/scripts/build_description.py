#!/usr/bin/env python3
"""
Build a Luma description_mirror (ProseMirror) document from a simpler Python
representation, without writing the nested JSON by hand.

There are two ways to use this:

1. As a library — import the helpers and assemble a doc programmatically:

    from build_description import P, H, doc
    body = doc([
        P(("📅 Wednesday 3 June", True), "  ·  ", ("🕕 18:30 – 21:30 BST", True)),
        P(),
        P("Hook paragraph in normal weight."),
        H("Who should come"),
        P("• Bullet one"),
        P("• Bullet two"),
    ])
    # body is the dict to send as description_mirror

2. As a CLI — give it a markdown-ish source file and get JSON out:

    python build_description.py < input.txt > description.json

   Source syntax:
   - Lines starting with `### ` become heading level 3
   - Empty lines become empty paragraphs
   - `**bold**` runs become bold text marks
   - Everything else is a paragraph

   Bullets are just paragraphs starting with `• ` — no special handling.

A paragraph builder accepts either:
- a plain string → single text node, no marks
- a tuple `(text, True)` → text node with bold mark
- multiple positional args, each a string or tuple → interleaved runs
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any, Union

Run = Union[str, tuple[str, bool]]


def _text_node(text: str, bold: bool = False) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": text}
    if bold:
        node["marks"] = [{"type": "bold"}]
    return node


def P(*runs: Run) -> dict[str, Any]:
    """
    Paragraph node. Pass zero or more runs:
        P()                                     -> empty paragraph (blank line)
        P("Hello world")                        -> plain paragraph
        P(("Bold thing", True), " and rest")    -> mixed runs
        P("Plain ", ("bold", True), " more")    -> three runs
    """
    if not runs:
        return {"type": "paragraph"}
    content: list[dict[str, Any]] = []
    for r in runs:
        if isinstance(r, tuple):
            text, bold = r
            content.append(_text_node(text, bold))
        else:
            content.append(_text_node(r, False))
    return {"type": "paragraph", "content": content}


def H(text: str, level: int = 3) -> dict[str, Any]:
    """Heading node. Default level 3 (Luma renders heading like a section title)."""
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [_text_node(text)],
    }


def doc(children: list[dict[str, Any]]) -> dict[str, Any]:
    """Top-level doc node. Pass an ordered list of P() / H() nodes."""
    return {"type": "doc", "content": children}


# ---------------------------------------------------------------------------
# CLI mode: parse a markdown-ish source from stdin
# ---------------------------------------------------------------------------

BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def parse_runs(line: str) -> list[Run]:
    """Split a line into alternating plain/bold runs based on **text** markers."""
    out: list[Run] = []
    pos = 0
    for m in BOLD_RE.finditer(line):
        if m.start() > pos:
            out.append(line[pos:m.start()])
        out.append((m.group(1), True))
        pos = m.end()
    if pos < len(line):
        out.append(line[pos:])
    return out or [""]


def parse_source(text: str) -> dict[str, Any]:
    children: list[dict[str, Any]] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            children.append(P())
            continue
        if line.startswith("### "):
            children.append(H(line[4:].strip(), level=3))
            continue
        if line.startswith("## "):
            children.append(H(line[3:].strip(), level=2))
            continue
        runs = parse_runs(line)
        children.append(P(*runs))
    return doc(children)


def _cli() -> None:
    src = sys.stdin.read()
    if not src.strip():
        sys.exit(
            "No input. Pipe markdown-ish text in. Example:\n"
            "  echo '### Title\\n\\nHello **bold** world' | python build_description.py"
        )
    print(json.dumps(parse_source(src), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
