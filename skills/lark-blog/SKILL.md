---
name: lark-blog
description: |
  Convert a Markdown blog draft into a new Lark docx with inline images
  and bind each image to its placeholder. Output is the doc reviewers
  open; the final publish step to your company's official website blog
  stays manual.
  Trigger phrases: "push blog to lark", "blog to lark doc", "/lark-blog".
version: 0.1.0
metadata:
  requires:
    bins:
      - python3
    pip:
      - requests
    skills:
      - lark
---

# Markdown blog -> Lark docx

Use this skill to turn a Markdown blog draft (with inline image placeholders)
into a reviewable Lark doc. It posts the parsed blocks, then uploads each
referenced PNG and binds it to the corresponding image block. The doc you
get back is the review handoff; final publish to your company's official
website blog is not in scope.

## Boundary

- This skill writes a new Lark doc; it never edits the company's official
  website blog.
- Image uploads use the user OAuth token (from the `lark` skill). It will
  not work with a tenant-only token. Run `lark_auth.py` once first.
- The script does not delete or overwrite anything; failed blocks are
  reported but the rest of the doc still goes through.

## Markdown conventions

| Markdown | Becomes |
|---|---|
| `# Heading` | docx heading1 (block_type 3) |
| `## Heading` | docx heading2 (block_type 4) |
| `### Heading` | docx heading3 (block_type 5) |
| `- bullet` | bullet item (block_type 12) |
| ` ```lang `...` ``` ` | code block (block_type 14). Recognised langs: `python`, `bash`, `json`. |
| `> quote` | italic paragraph (block_type 2 + italic style) |
| `---` | divider (block_type 22) |
| Markdown table | bullets `**header**: value`. Lark API tables are awkward; this keeps the doc readable. |
| `*[image: foo.png \| "Caption text"]*` | empty image block (block_type 27) + italic caption paragraph. The image is uploaded and bound after the doc is created. |

Inline: `**bold**`, `*italic*`, `` `code` ``, `[label](https://url)`.

## Entry point

```bash
python3 skills/lark-blog/scripts/push_blog_to_lark.py \
  --md ./post.md \
  --images-dir ./images \
  --title 'Post Draft v1'
```

Optional flags:

- `--folder-token TOKEN`: create the doc inside a specific Lark drive folder
  instead of at the root.
- `--batch-size N`: blocks per create-block API call. Default 40 (Lark's
  limit is around 50).

## Setup

1. Install the `lark` skill alongside this one and run its `lark_auth.py`
   once to grant a user token. The script auto-finds `lark_client.py` in
   the sibling skill's `scripts/` dir.
2. Override the discovery path with `LARK_CLIENT_PATH=/path/to/lark_scripts`
   if your install layout differs.
3. Place your blog Markdown anywhere; pass its path with `--md`.
4. Put referenced PNGs in any folder; pass it with `--images-dir`.

## Workflow for the assistant

1. Read the user's Markdown draft. Verify all `*[image: foo.png | "..."]*`
   lines have a real file in `--images-dir`.
2. Confirm the title with the user before creating the doc; Lark titles
   are not easily renamed once shared.
3. Run the script. Surface the new `document_id` and the count of
   appended blocks + uploaded images.
4. Report any rejected blocks (`block_type` + first 160 chars of the
   error). Common culprits: malformed table rows, oversized code blocks.

## Files

| File | Purpose |
|---|---|
| `scripts/push_blog_to_lark.py` | Markdown parser, block builder, image uploader. |
| `examples/sample-blog.md` | A fictional blog showing every supported Markdown construct. |
| `examples/images/` | (User adds real PNGs here matching the sample placeholders.) |

## Safety rules

- Never paste a `lark_config.json` or refresh token into the Markdown
  draft. The script reads them from the `lark` skill's config.
- If the script reports image upload failures, the doc still has empty
  image blocks. Fix the PNG path and re-run (the doc is fresh each run;
  pass a new `--title` to avoid confusion).
- Blog drafts can contain sensitive embargo / launch dates. Keep
  `*.md` files out of the repo until you are ready; `.gitignore` blocks
  `*_draft.md` by default.
