---
name: lark
description: |
  Read and write Lark (Feishu international) docs, spreadsheets, drive files,
  and messages from Python. Supports both tenant access tokens (app-only,
  no login) and OAuth user tokens with auto-refresh. Trigger phrases:
  "lark sheet", "lark doc", "push to lark", "/lark".
metadata:
  requires:
    bins:
      - python3
    pip:
      - requests
    env:
      - LARK_CONFIG (optional, path to your lark_config.json)
---

# Lark (Feishu International) Client

Use this skill when you need to read or write Lark docs, sheets, drive files,
or messages programmatically. The skill ships a `LarkClient` Python library
plus a one-time OAuth helper and a generic spreadsheet pusher.

## Boundary

- Never commit `lark_config.json` (contains your app secret) or
  `.lark_tokens.json` (contains a user refresh token). Both are gitignored.
- All API calls go through `LarkClient` so token refresh and error handling
  stay consistent.
- For org-internal automation prefer tenant tokens (`as_user=False`); use
  user tokens (`as_user=True`) only when the API endpoint requires it.

## Setup

1. Create an app in the Lark Open Platform, give it the scopes you need.
2. Copy `templates/lark_config.example.json` to `lark_config.json` in your
   working directory (or set `LARK_CONFIG=/path/to/config.json`). Fill in
   `app_id` and `app_secret`.
3. For user-token endpoints, run a one-time OAuth dance:

   ```bash
   python3 skills/lark/scripts/lark_auth.py
   ```

   Browser opens, you approve. The script caches `refresh_token` in
   `.lark_tokens.json` (also gitignored). After this, `LarkClient` will
   auto-refresh.

## Quick recipes

Read a doc (raw text):

```python
from lark_client import LarkClient
client = LarkClient()
text = client.get_doc_raw_content("DOC_TOKEN", as_user=True)
```

Read a sheet range:

```python
data = client.get_sheet_values("SHEET_TOKEN", "Sheet1!A1:D10", as_user=True)
for row in data["valueRange"]["values"]:
    print(row)
```

Write to a sheet range:

```python
client.update_sheet_values(
    "SHEET_TOKEN",
    "Sheet1!A1:B2",
    [["name", "score"], ["Alice", 95]],
    as_user=True,
)
```

Send a chat message by email:

```python
client.send_to_email("teammate@example.com", "Hi there!", as_user=True)
```

Push a JSON file straight into a sheet range:

```bash
python3 skills/lark/scripts/push_to_sheet.py \
  --sheet-token SHEET_TOKEN \
  --range "Sheet1!A1" \
  --json-file ./rows.json
```

See [references/sheet-recipes.md](references/sheet-recipes.md) for more
patterns.

## Files

| File | Purpose |
|---|---|
| `scripts/lark_client.py` | Core `LarkClient` library. Token management + API surface. |
| `scripts/lark_auth.py` | One-time OAuth helper. Run once per machine. |
| `scripts/push_to_sheet.py` | Generic JSON-to-spreadsheet pusher. |
| `templates/lark_config.example.json` | Config template. Copy and fill in. |
| `references/auth-flow.md` | When to use tenant vs user tokens; how the cache works. |
| `references/sheet-recipes.md` | Common sheet operations (append row, write cell, read range). |

## Safety rules

- Confirm `spreadsheet_token` and `range` with the user before any
  destructive write. `update_sheet_values` overwrites cells in-range
  without warning.
- Don't paste a real `app_secret` into chat. Treat it like a database
  password.
- The token cache file holds a long-lived refresh token. Do not move it
  off-machine; revoke it via the Lark admin console if compromised.
