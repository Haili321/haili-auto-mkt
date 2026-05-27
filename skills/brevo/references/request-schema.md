# Brevo Email Request Schema

Each invocation of the skill consumes one JSON file describing one email.
Schema below; see `templates/` for working samples.

## Minimal request

```json
{
  "sender":  { "email": "you@example.com", "name": "Your Name" },
  "to":      [{ "email": "recipient@example.com", "name": "Recipient" }],
  "subject": "Your subject here",
  "markdown": "Hi there,\n\nYour email body in Markdown.\n\nBest,\nYou"
}
```

## Fields

| Field | Required | Notes |
|---|---:|---|
| `sender.email` | yes | Must be a verified Brevo sender in your account. |
| `sender.name` | no | Display name shown in inbox. |
| `to` | yes | Array. Each entry is either a string `"x@y.com"` or `{ "email": "...", "name": "..." }`. |
| `cc` / `bcc` | no | Same format as `to`. Avoid CC during test sends unless intentional. |
| `replyTo` | no | Single email string. |
| `subject` | yes | Subject line. Auto-prefixed with `TEST - ` when `--test-to` is used. |
| `htmlContent` | conditional | Final HTML body. If omitted, generated from `markdown` or `textContent`. |
| `markdown` | conditional | Markdown body. Converted to simple HTML if `htmlContent` is absent. |
| `textContent` | conditional | Plain text. Generated from `markdown` or HTML if absent. |
| `tags` | no | Array of Brevo message tags for filtering. |
| `metadata` | no | Local audit context. Not sent to Brevo. |

At least one of `htmlContent`, `markdown`, or `textContent` must be present.

## Markdown subset

When the script converts `markdown` to HTML, it recognises:

- Paragraphs (separated by blank lines)
- `## Heading` and `### Subheading`
- `- bullet` lists
- Inline links: `[label](https://...)`

Anything else (bold, italic, code blocks, tables, images) is passed through
escaped. If you need richer formatting, hand-author `htmlContent` directly.

## Metadata patterns

`metadata` is for your own audit trail. The script copies it into the input
record but does not send it to Brevo. Common patterns:

```json
{
  "metadata": {
    "campaign": "spring-outreach",
    "target_org": "Recipient Org",
    "status": "approved",
    "source": "lark",
    "source_doc_url": "https://your-lark-doc-url"
  }
}
```

## Test vs official send

- `--test-to addr@example.com`: rewrites recipients to that single address,
  drops cc/bcc, prefixes the subject. Use to validate rendering in a real
  inbox before going official.
- `--send` without `--test-to`: uses recipients from the request file as-is.
- No `--send` flag: dry run only; nothing leaves your machine.
