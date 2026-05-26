---
name: brevo
description: |
  Send transactional outreach emails through Brevo's API one at a time.
  Supports dry-run, test-send (override recipients), and official send.
  Trigger phrases: "send brevo email", "test brevo", "/brevo".
version: 0.1.0
metadata:
  requires:
    bins:
      - python3
    env:
      - BREVO_API_KEY
---

# Brevo Email

Use this skill to draft, dry-run, test, and officially send transactional
emails through Brevo, one recipient at a time. The skill is designed for
outreach: every send is intentional, audited, and reviewable.

## Boundary

- Never commit API keys. Load `BREVO_API_KEY` from the shell environment or
  a local `.env.local` (already in `.gitignore`).
- Default to dry-run. Sending requires the `--send` flag.
- One email per society / organisation / recipient. Do not batch unrelated
  recipients into a single message.
- Each official send must be approved by the user.

## Inputs

The skill drives off a single request JSON file per email. See
[references/request-schema.md](references/request-schema.md) for the full
shape. Minimal example:

```json
{
  "sender":  { "email": "you@example.com", "name": "Your Name" },
  "to":      [{ "email": "recipient@example.com", "name": "Recipient" }],
  "subject": "Your subject here",
  "markdown": "Hi there,\n\nYour email body in Markdown.\n\nBest,\nYou"
}
```

## Entry points

Check API access (no email sent):

```bash
skills/brevo/scripts/bootstrap_runtime.sh --check-account
```

Dry run (renders email, no API call):

```bash
skills/brevo/scripts/bootstrap_runtime.sh --request-file ./email_request.json
```

Test send (rewrites recipients to a single test address, prefixes subject):

```bash
skills/brevo/scripts/bootstrap_runtime.sh \
  --request-file ./email_request.json \
  --test-to you@example.com \
  --send
```

Official send (uses the recipients in the request file as-is):

```bash
skills/brevo/scripts/bootstrap_runtime.sh \
  --request-file ./email_request.json \
  --send
```

## Workflow for the assistant

1. Collect or draft the email copy. If the user has finalised copy in a
   document or sheet, ask for it; do not invent recipients or subjects.
2. Create a request JSON matching the schema. Validate locally by reading
   the file.
3. Run a dry run. Show the rendered subject, recipients, text, and HTML to
   the user.
4. If the user wants a test, run with `--test-to <their address> --send` so
   they can see the real email in their inbox.
5. Send officially only after the user explicitly says "send it" (or
   equivalent). Confirm the recipient list once more before sending.
6. After each send, surface the Brevo `messageId` and the path to the run's
   output directory.

## Output

Each invocation writes to `./brevo-output/<UTC timestamp>/`:

| Path | Contents |
|---|---|
| `input/request.json` | Original request, copied verbatim. |
| `rendered/email.json` | Final Brevo payload (sender, subject, to, html, text). |
| `rendered/email.html` | The HTML body that will be sent. |
| `send/result.json` | Brevo API response (only when `--send` is used). |

Customise the root with `--output-root`.

## Files

| File | Purpose |
|---|---|
| `scripts/run_brevo_email.py` | Renderer + sender. Zero-dependency Python 3. |
| `scripts/bootstrap_runtime.sh` | Thin wrapper that resolves the script path. |
| `references/request-schema.md` | Full request JSON schema with field rules. |
| `examples/minimal_request.example.json` | Smallest working request. |
| `examples/outreach_request.example.json` | Multi-section outreach request. |
| `.env.example` | Template env file. Copy to `.env.local` and fill in. |

## Safety rules

- `TEST -` is auto-prefixed when `--test-to` is set; do not strip it
  manually until you're ready to send officially.
- Brevo errors abort the run and surface HTTP status + Brevo error body.
- The script does not store secrets in any output artifact.
