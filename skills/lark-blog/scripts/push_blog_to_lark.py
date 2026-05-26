#!/usr/bin/env python3
"""Push a Markdown blog draft to a new Lark docx with inline images.

The script parses Markdown into Lark docx blocks, creates a new doc, posts
the blocks in batches, then uploads each inline image to its placeholder
block. The resulting doc is what you share with reviewers; the final
publish step (to your company site or CMS) stays manual.

Markdown conventions this skill recognises:

  # / ## / ###     headings
  - bullet         bullet list item
  ```lang ... ```  code fence (lang: python | bash | json | plain)
  > quote          rendered as italic paragraph
  ---              horizontal rule -> divider
  | a | b |        table (rendered as bullets "A: b")
  *[image: foo.png | "Caption goes here"]*   inline image placeholder

Inline: **bold**, *italic*, `code`, [text](url).

Usage:
    push_blog_to_lark.py \\
        --md ./post.md \\
        --images-dir ./images \\
        --title 'My Blog Draft v1'

Requires the `lark` skill to be installed alongside this skill (same
parent skills dir) for the LarkClient library, or set LARK_CLIENT_PATH
to the directory containing lark_client.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests


def _resolve_lark_client_dir() -> Path:
    override = os.environ.get("LARK_CLIENT_PATH")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent.parent / "lark" / "scripts",  # installed sibling skill
        here.parent.parent.parent / "lark" / "scripts",
    ]
    for candidate in candidates:
        if (candidate / "lark_client.py").exists():
            return candidate
    raise SystemExit(
        "Could not find lark_client.py. Install the `lark` skill next to this "
        "one, or set LARK_CLIENT_PATH to its scripts directory."
    )


sys.path.insert(0, str(_resolve_lark_client_dir()))

from lark_client import LarkClient, BASE_URL  # noqa: E402


# ── Inline parsing ────────────────────────────────────────────────

INLINE_PATTERN = re.compile(
    r"(\*\*([^*]+)\*\*)"             # **bold**
    r"|(\[([^\]]+)\]\(([^)]+)\))"     # [text](url)
    r"|(`([^`]+)`)"                   # `code`
    r"|(\*([^*]+)\*)"                 # *italic*
)


def parse_inline(text: str) -> list:
    elements: list = []
    pos = 0
    for m in INLINE_PATTERN.finditer(text):
        if m.start() > pos:
            elements.append({"text_run": {"content": text[pos:m.start()]}})
        if m.group(1):
            elements.append({
                "text_run": {
                    "content": m.group(2),
                    "text_element_style": {"bold": True},
                }
            })
        elif m.group(3):
            elements.append({
                "text_run": {
                    "content": m.group(4),
                    "text_element_style": {
                        "link": {"url": m.group(5)},
                        "bold": True,
                    },
                }
            })
        elif m.group(6):
            elements.append({
                "text_run": {
                    "content": m.group(7),
                    "text_element_style": {"inline_code": True},
                }
            })
        elif m.group(8):
            elements.append({
                "text_run": {
                    "content": m.group(9),
                    "text_element_style": {"italic": True},
                }
            })
        pos = m.end()
    if pos < len(text):
        elements.append({"text_run": {"content": text[pos:]}})
    if not elements:
        elements = [{"text_run": {"content": text}}]
    return elements


# ── Block builders ────────────────────────────────────────────────

def text_block(text: str) -> dict:
    return {"block_type": 2, "text": {"elements": parse_inline(text)}}


def heading_block(level: int, text: str) -> dict:
    block_type = {1: 3, 2: 4, 3: 5}[level]
    key = {1: "heading1", 2: "heading2", 3: "heading3"}[level]
    return {"block_type": block_type, key: {"elements": parse_inline(text)}}


def bullet_block(text: str) -> dict:
    return {"block_type": 12, "bullet": {"elements": parse_inline(text)}}


def italic_text_block(text: str) -> dict:
    return {
        "block_type": 2,
        "text": {
            "elements": [{
                "text_run": {
                    "content": text,
                    "text_element_style": {"italic": True},
                }
            }]
        },
    }


def code_block(code: str, language: str = "") -> dict:
    lang_map = {"python": 49, "py": 49, "bash": 28, "sh": 28, "json": 31, "": 1}
    lang_code = lang_map.get(language.lower(), 1)
    return {
        "block_type": 14,
        "code": {
            "elements": [{"text_run": {"content": code}}],
            "style": {"language": lang_code, "wrap": True},
        },
    }


def divider_block() -> dict:
    return {"block_type": 22, "divider": {}}


def image_block() -> dict:
    return {"block_type": 27, "image": {}}


# ── Markdown -> blocks (image-aware) ──────────────────────────────

IMAGE_LINE_RE = re.compile(r'^\*\[image:\s*(\S+)\s*\|\s*"([^"]+)"\]\*$')


def is_table_row(s: str) -> bool:
    return s.strip().startswith("|") and s.strip().endswith("|")


def md_to_blocks(md: str) -> tuple[list, list]:
    """Parse markdown. Returns (blocks, image_order)
    where image_order is [(filename, index_into_blocks), ...].
    """
    lines = md.split("\n")
    blocks: list = []
    image_order: list = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            lang = stripped[3:].strip() or ""
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            blocks.append(code_block("\n".join(body), lang))
            continue

        if stripped.startswith("# "):
            blocks.append(heading_block(1, stripped[2:]))
            i += 1
            continue
        if stripped.startswith("## "):
            blocks.append(heading_block(2, stripped[3:]))
            i += 1
            continue
        if stripped.startswith("### "):
            blocks.append(heading_block(3, stripped[4:]))
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            blocks.append(divider_block())
            i += 1
            continue

        if (
            is_table_row(line)
            and i + 1 < len(lines)
            and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1])
        ):
            i += 2
            while i < len(lines) and is_table_row(lines[i]):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if len(row) >= 2:
                    blocks.append(bullet_block(f"**{row[0]}**: {row[1]}"))
                i += 1
            continue

        if stripped.startswith("> "):
            blocks.append(italic_text_block(stripped[2:]))
            i += 1
            continue

        m = IMAGE_LINE_RE.match(stripped)
        if m:
            filename, caption = m.group(1), m.group(2)
            image_order.append((filename, len(blocks)))
            blocks.append(image_block())
            blocks.append(italic_text_block(caption))
            i += 1
            continue

        if stripped.startswith("- "):
            blocks.append(bullet_block(stripped[2:]))
            i += 1
            continue

        para = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            ns = nxt.strip()
            if not ns:
                break
            if ns.startswith(("#", "```", "- ", "> ", "*[image:")) or is_table_row(nxt) or ns in ("---",):
                break
            para.append(nxt)
            i += 1
        blocks.append(text_block(" ".join(l.strip() for l in para)))

    return blocks, image_order


# ── Push helpers ──────────────────────────────────────────────────

def chunk(seq: list, n: int):
    for j in range(0, len(seq), n):
        yield seq[j:j + n]


def upload_image_to_block(
    client: LarkClient, png_path: Path, block_id: str, doc_id: str
) -> str:
    """Upload a PNG, bind it to an image block."""
    size = png_path.stat().st_size
    token = client.get_user_token()

    with open(png_path, "rb") as fh:
        files = {"file": (png_path.name, fh, "image/png")}
        data = {
            "file_name": png_path.name,
            "parent_type": "docx_image",
            "parent_node": block_id,
            "size": str(size),
            "extra": json.dumps({"drive_route_token": doc_id}),
        }
        up = requests.post(
            f"{BASE_URL}/drive/v1/medias/upload_all",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            files=files,
            timeout=60,
        )
    up.raise_for_status()
    body = up.json()
    if body.get("code") != 0:
        raise Exception(f"upload failed: {body}")
    file_token = body["data"]["file_token"]

    patch = requests.patch(
        f"{BASE_URL}/docx/v1/documents/{doc_id}/blocks/{block_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        params={"document_revision_id": "-1"},
        json={"replace_image": {"token": file_token}},
        timeout=30,
    )
    patch.raise_for_status()
    pb = patch.json()
    if pb.get("code") != 0:
        raise Exception(f"patch failed: {pb}")

    return file_token


# ── CLI ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--md", required=True, type=Path, help="Path to Markdown file.")
    p.add_argument(
        "--images-dir",
        type=Path,
        default=None,
        help="Directory containing referenced PNGs. Required if the md has *[image:...]* lines.",
    )
    p.add_argument("--title", required=True, help="Title for the new Lark doc.")
    p.add_argument(
        "--folder-token",
        default=None,
        help="Optional Lark drive folder token to create the doc inside.",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=40,
        help="Blocks per create-block call. Default 40 (Lark caps near 50).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    md = args.md.read_text(encoding="utf-8")
    blocks, image_order = md_to_blocks(md)
    print(f"Parsed {len(blocks)} blocks; {len(image_order)} image placeholder(s).")

    if image_order and not args.images_dir:
        raise SystemExit(
            "Markdown references images but --images-dir was not given."
        )
    for fn, idx in image_order:
        path = args.images_dir / fn
        if not path.exists():
            print(f"  warning: {fn} referenced but not found at {path}")

    client = LarkClient()
    doc = client.create_doc(args.title, folder_token=args.folder_token, as_user=True)
    doc_id = doc["document"]["document_id"]
    print(f"Created doc: document_id = {doc_id}")

    created_ids: list = []
    total = 0
    failed: list = []
    for batch in chunk(blocks, args.batch_size):
        try:
            res = client.create_block(doc_id, doc_id, batch, as_user=True)
            ids = [c["block_id"] for c in res.get("children", [])]
            created_ids.extend(ids)
            total += len(batch)
            print(f"  appended {total}/{len(blocks)} blocks")
        except Exception as e:
            print(f"  batch failed ({e}); retrying per-block")
            for b in batch:
                try:
                    res = client.create_block(doc_id, doc_id, [b], as_user=True)
                    ids = [c["block_id"] for c in res.get("children", [])]
                    created_ids.extend(ids)
                    total += 1
                except Exception as e2:
                    print(f"    skip block_type={b.get('block_type')}: {e2}")
                    created_ids.append(None)
                    failed.append((b.get("block_type"), str(e2)))
            print(f"  appended {total}/{len(blocks)} blocks (retried)")

    if image_order:
        print("\nUploading images...")
        for filename, idx in image_order:
            block_id = created_ids[idx]
            if not block_id:
                print(f"  {filename}: no block id (create failed); skipping")
                continue
            png_path = args.images_dir / filename
            if not png_path.exists():
                print(f"  {filename}: file not found; skipping")
                continue
            try:
                token = upload_image_to_block(client, png_path, block_id, doc_id)
                print(
                    f"  {filename}  -> bound to block {block_id[:12]}...  "
                    f"file_token={token[:12]}..."
                )
            except Exception as e:
                print(f"  {filename}: upload failed - {e}")

    if failed:
        print(f"\n{len(failed)} block(s) rejected:")
        for bt, err in failed[:5]:
            print(f"  - block_type={bt}  err={err[:160]}")

    print(f"\nDone. document_id = {doc_id}")
    print(
        "Open this doc in your Lark workspace via the docx URL pattern, e.g.\n"
        "  https://<your-tenant>.larksuite.com/docx/{doc_id}\n"
        "Share with reviewers, then publish to your CMS manually once approved."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
