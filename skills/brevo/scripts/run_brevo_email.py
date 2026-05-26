#!/usr/bin/env python3
"""Dry-run, test, or send a single Brevo transactional email.

Usage:
    run_brevo_email.py --check-account
    run_brevo_email.py --request-file email_request.json
    run_brevo_email.py --request-file email_request.json --test-to you@example.com --send
    run_brevo_email.py --request-file email_request.json --send

Reads BREVO_API_KEY from the environment or a local ./.env.local file. Writes
artifacts under ./brevo-output/<UTC timestamp>/ (overridable with
--output-root).
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_URL = "https://api.brevo.com/v3"
DEFAULT_OUTPUT_ROOT = "brevo-output"
USER_AGENT = "haili-auto-mkt-brevo/0.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run, test, or send a single Brevo transactional email."
    )
    parser.add_argument("--request-file", help="Path to email request JSON.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--send", action="store_true", help="Actually call Brevo.")
    parser.add_argument(
        "--test-to",
        help="Override all recipients with this test address; auto-prefixes subject.",
    )
    parser.add_argument("--test-subject-prefix", default="TEST - ")
    parser.add_argument(
        "--check-account",
        action="store_true",
        help="Verify Brevo API access without sending email.",
    )
    return parser.parse_args()


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Request JSON must be an object.")
    return data


def normalize_recipient(value: Any) -> dict[str, str]:
    if isinstance(value, str):
        return {"email": value}
    if isinstance(value, dict) and isinstance(value.get("email"), str):
        out = {"email": value["email"].strip()}
        if isinstance(value.get("name"), str) and value["name"].strip():
            out["name"] = value["name"].strip()
        return out
    raise SystemExit(f"Invalid recipient: {value!r}")


def normalize_recipient_list(value: Any, field: str) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise SystemExit(f"`{field}` must be a list.")
    return [normalize_recipient(item) for item in value]


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    chunks: list[str] = []
    in_ul = False
    para_lines: list[str] = []

    def flush_para() -> None:
        nonlocal para_lines
        if para_lines:
            joined = "<br>\n".join(inline_markdown(l) for l in para_lines)
            chunks.append(f"<p>{joined}</p>")
            para_lines = []

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            chunks.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            close_ul()
            continue
        if line.startswith("### "):
            flush_para()
            close_ul()
            chunks.append(f"<h3>{inline_markdown(line[4:].strip())}</h3>")
        elif line.startswith("## "):
            flush_para()
            close_ul()
            chunks.append(f"<h2>{inline_markdown(line[3:].strip())}</h2>")
        elif line.startswith("- "):
            flush_para()
            if not in_ul:
                chunks.append("<ul>")
                in_ul = True
            chunks.append(f"<li>{inline_markdown(line[2:].strip())}</li>")
        else:
            para_lines.append(line.strip())
    flush_para()
    close_ul()
    return "\n".join(chunks)


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
    return pattern.sub(r'<a href="\2">\1</a>', escaped)


def html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</(p|div|h[1-6]|li)>", "\n", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s*\n\s*\n+", "\n\n", value)
    return value.strip()


def wrap_html_fragment(fragment: str) -> str:
    return f"""<!doctype html>
<html>
  <body style="margin:0; padding:0; background:#f8fafc; font-family: Arial, Helvetica, sans-serif; color:#111827;">
    <div style="max-width:680px; margin:0 auto; padding:28px 18px;">
      <div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:8px; padding:28px; font-size:15px; line-height:1.6;">
        {fragment}
      </div>
    </div>
  </body>
</html>"""


def render_request(request: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    sender = request.get("sender")
    if not isinstance(sender, dict) or not sender.get("email"):
        raise SystemExit("`sender.email` is required.")
    subject = request.get("subject")
    if not isinstance(subject, str) or not subject.strip():
        raise SystemExit("`subject` is required.")

    to = normalize_recipient_list(request.get("to"), "to")
    cc = normalize_recipient_list(request.get("cc"), "cc")
    bcc = normalize_recipient_list(request.get("bcc"), "bcc")
    if not to:
        raise SystemExit("At least one `to` recipient is required.")

    if args.test_to:
        to = [{"email": args.test_to}]
        cc = []
        bcc = []
        if not subject.startswith(args.test_subject_prefix):
            subject = f"{args.test_subject_prefix}{subject}"

    html_content = request.get("htmlContent")
    text_content = request.get("textContent")
    markdown = request.get("markdown")

    if not any(
        isinstance(v, str) and v.strip() for v in (html_content, text_content, markdown)
    ):
        raise SystemExit(
            "One of `htmlContent`, `markdown`, or `textContent` is required."
        )

    if not isinstance(html_content, str) or not html_content.strip():
        if isinstance(markdown, str) and markdown.strip():
            html_content = wrap_html_fragment(markdown_to_html(markdown))
        else:
            escaped_text = html.escape(str(text_content)).replace("\n", "<br>\n")
            html_content = wrap_html_fragment(f"<p>{escaped_text}</p>")

    if not isinstance(text_content, str) or not text_content.strip():
        if isinstance(markdown, str) and markdown.strip():
            text_content = markdown
        else:
            text_content = html_to_text(html_content)

    payload: dict[str, Any] = {
        "sender": {"email": sender["email"].strip()},
        "to": to,
        "subject": subject.strip(),
        "htmlContent": html_content,
        "textContent": text_content,
    }
    if isinstance(sender.get("name"), str) and sender["name"].strip():
        payload["sender"]["name"] = sender["name"].strip()
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc
    if isinstance(request.get("replyTo"), str) and request["replyTo"].strip():
        payload["replyTo"] = {"email": request["replyTo"].strip()}
    if isinstance(request.get("tags"), list):
        payload["tags"] = [str(tag) for tag in request["tags"] if str(tag).strip()]
    return payload


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def send_email(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": api_key,
            "user-agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return {"ok": True, "status": response.status, "response": json.loads(body)}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed: Any = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return {"ok": False, "status": exc.code, "error": parsed}


def check_account(api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}/account",
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "user-agent": USER_AGENT,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            return {"ok": True, "status": response.status, "endpoint": "/account"}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed: Any = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return {"ok": False, "status": exc.code, "endpoint": "/account", "error": parsed}


def require_api_key() -> str:
    api_key = os.environ.get("BREVO_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing BREVO_API_KEY in environment or .env.local.")
    return api_key


def main() -> int:
    args = parse_args()
    load_dotenv(Path.cwd() / ".env.local")

    if args.check_account:
        result = check_account(require_api_key())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    if not args.request_file:
        raise SystemExit("Missing --request-file unless --check-account is used.")

    request_path = Path(args.request_file)
    original = read_json(request_path)
    payload = render_request(original, args)

    run_dir = Path(args.output_root) / timestamp()
    write_json(run_dir / "input" / "request.json", original)
    write_json(run_dir / "rendered" / "email.json", payload)
    (run_dir / "rendered").mkdir(parents=True, exist_ok=True)
    (run_dir / "rendered" / "email.html").write_text(
        payload["htmlContent"], encoding="utf-8"
    )

    result = {
        "mode": "send" if args.send else "dry-run",
        "test_to": args.test_to,
        "output_dir": str(run_dir),
        "to": payload["to"],
        "cc": payload.get("cc", []),
        "subject": payload["subject"],
    }

    if args.send:
        send_result = send_email(payload, require_api_key())
        write_json(run_dir / "send" / "result.json", send_result)
        result["send_result"] = send_result
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if send_result.get("ok") else 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
