#!/usr/bin/env python3
"""Build a model-launch email from a JSON spec and the tokenized template.

Fills templates/model_launch.template.html and writes:
  - an email HTML file
  - a Brevo request JSON (ready for run_brevo_email.py)

Enforces house style: strips em/en dashes (user preference), keeps the Brevo
merge tag {{ contact.EMAIL }} in the footer intact.

Usage:
  scripts/build_model_email.py --spec spec.json \
      --out-html out.html --out-request request.json
"""
from __future__ import annotations
import argparse, html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "templates" / "model_launch.template.html"

P_OPEN = '<p class="default" style="margin: 0;">'
SPACER = '<p class="default" style="margin: 0;"><br></p>'


def no_dash(text: str) -> str:
    """Remove em/en dashes per house style; collapse leftover double spaces."""
    text = text.replace(" — ", ", ").replace("—", " ")
    text = text.replace(" – ", ", ").replace("–", " ")
    return re.sub(r"  +", " ", text).strip()


def esc(text: str) -> str:
    out = html.escape(no_dash(str(text)), quote=False)
    # lightweight bold: **text** -> <strong>text</strong> (after escaping, so it is safe)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return out


def paras(items: list[str]) -> str:
    out = []
    for i, p in enumerate(items):
        if i:
            out.append(SPACER)
        out.append(f"{P_OPEN}{esc(p)}</p>")
    return "".join(out)


def bullets(items: list[str]) -> str:
    lis = "".join(
        f'<li class="default" style="margin: 0;">{esc(b)}</li>' for b in items
    )
    return f'<ul style="margin: 0;">{lis}</ul>'


def build_body(spec: dict) -> str:
    greeting = esc(spec.get("greeting", "Hi there,"))
    heading = esc(spec.get("highlights_heading", "What stands out"))
    parts = [
        '<p class="default" style="margin: 0; font-style: normal; font-weight: 400;'
        f' text-decoration: none;">{greeting}</p>',
        SPACER,
        paras(spec["intro"]),
        f'<h1 class="default-heading1" style="margin: 0; color: #1f2d3d;'
        ' font-family: arial,helvetica,sans-serif; font-size: 36px; font-weight: 400;'
        f' word-break: break-word;"><strong>{heading}</strong></h1>',
        bullets(spec["highlights"]),
    ]
    if spec.get("pricing"):
        parts += [
            SPACER,
            f'{P_OPEN}<strong>{esc(spec["pricing_heading"])}</strong></p>',
            bullets(spec["pricing"]),
        ]
    if spec.get("closing_line"):
        parts += [SPACER, f'{P_OPEN}{esc(spec["closing_line"])}</p>']
    return "".join(parts)


def fill(template: str, spec: dict) -> str:
    body = build_body(spec)
    out = template
    att = lambda u: html.escape(str(u), quote=True)  # URL tokens land in src/href attributes
    repl = {
        "[[SUBJECT]]": html.escape(no_dash(spec["subject"]), quote=False),
        "[[HEADER_IMAGE_URL]]": att(spec["header_image_url"]),
        "[[BODY_HTML]]": body,
        "[[CTA_URL]]": att(spec["cta_url"]),
        "[[CTA_TEXT]]": esc(spec["cta_text"]),
        "[[SIGN_NAME]]": esc(spec.get("sign_name", "Your Name")),
        "[[SIGN_TITLE]]": esc(spec.get("sign_title", "Your Title")),
        "[[SIGN_ADDRESS]]": esc(spec.get("sign_address", "Your address")),
        "[[SIGN_PHOTO_URL]]": att(spec.get("sign_photo_url", "https://placehold.co/170x170?text=Logo")),
        "[[FOOTER_IMAGE_URL]]": att(spec.get("footer_image_url", "https://placehold.co/200x80?text=Footer")),
    }
    for k, v in repl.items():
        if k not in out:
            raise SystemExit(f"token {k} missing from template")
        out = out.replace(k, v)
    leftover = re.findall(r"\[\[[A-Z_]+\]\]", out)
    if leftover:
        raise SystemExit(f"unfilled tokens: {leftover}")
    if "—" in out or "&mdash;" in out:
        raise SystemExit("em dash leaked into output")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--out-html", required=True)
    ap.add_argument("--out-request", required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8")
    htmlout = fill(template, spec)
    Path(args.out_html).write_text(htmlout, encoding="utf-8")

    request = {
        "sender": spec.get("sender", {"email": "marketing@example.com", "name": "Your Brand"}),
        "to": spec["to"],
        "subject": no_dash(spec["subject"]),
        "htmlContent": htmlout,
        "tags": spec.get("tags", ["model-launch"]),
        "metadata": spec.get("metadata", {}),
    }
    if spec.get("cc"):
        request["cc"] = spec["cc"]
    Path(args.out_request).write_text(
        json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.out_html} and {args.out_request}")
    print(f"subject: {request['subject']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
