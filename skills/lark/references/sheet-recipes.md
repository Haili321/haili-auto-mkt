# Sheet recipes

Common patterns for working with Lark spreadsheets via `LarkClient`. All
examples assume:

```python
from lark_client import LarkClient
client = LarkClient()
```

The `spreadsheet_token` comes from the URL:
`https://example.larksuite.com/sheets/<SPREADSHEET_TOKEN>?sheet=<TAB_ID>`.

The `range` format is `<sheet name or tab id>!<A1 notation>`, e.g.
`Sheet1!A1:D10` or `2zKVUc!O1:O100`.

## Read a range

```python
data = client.get_sheet_values(
    "SHEET_TOKEN",
    "Sheet1!A1:D10",
    as_user=True,
)
for row in data["valueRange"]["values"]:
    print(row)
```

## Write a single cell

```python
client.update_sheet_values(
    "SHEET_TOKEN",
    "Sheet1!B2:B2",
    [["new value"]],
    as_user=True,
)
```

## Write a header row + data

```python
header = ["name", "score", "tier"]
rows = [
    ["Alice", 95, "S"],
    ["Bob",   82, "A"],
    ["Carol", 71, "B"],
]
client.update_sheet_values(
    "SHEET_TOKEN",
    "Sheet1!A1:C4",
    [header, *rows],
    as_user=True,
)
```

## Mark a status column row-by-row

When you want to flip individual cells without overwriting neighbouring
data, write one cell at a time:

```python
rows_to_mark = [5, 8, 13]
for r in rows_to_mark:
    client.update_sheet_values(
        "SHEET_TOKEN",
        f"Sheet1!O{r}:O{r}",
        [["done"]],
        as_user=True,
    )
```

## Push a JSON file via CLI

```bash
python3 scripts/push_to_sheet.py \
  --sheet-token SHEET_TOKEN \
  --range 'Sheet1!A1' \
  --json-file ./rows.json \
  --columns name,score \
  --header
```

Input `rows.json`:

```json
[
  {"name": "Alice", "score": 95},
  {"name": "Bob",   "score": 82}
]
```

This becomes a write to `Sheet1!A1:B3` (header + two rows). The CLI prints
the final range and Lark's response.

## Pitfalls

- The API accepts a 2D array. A flat array like `["Alice", 95]` is one
  cell, not one row. Wrap rows in another list.
- `update_sheet_values` overwrites cells in the target range. If you want
  to insert without overwriting neighbours, write smaller ranges.
- Bool / None values are stringified by Lark. Convert to explicit strings
  if you care about display.
- The tab name in the range must match exactly. Hidden or renamed tabs
  silently fail with "range not found".
