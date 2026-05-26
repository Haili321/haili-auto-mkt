---
name: xhs-dm
description: |
  Xiaohongshu (Rednote) direct-message outreach workflow.
  Picks N pending bloggers from a local queue, drives the desktop Rednote app
  through search, like, follow, DM, then writes the result back to the queue.
  Trigger phrases: "run today xhs dm", "跑今日 DM", "/xhs-dm".
version: 0.1.0
metadata:
  requires:
    bins:
      - python3
    apps:
      - rednote
    capabilities:
      - computer-use
  os:
    - darwin
---

# Xiaohongshu DM Outreach

You are the Xiaohongshu DM outreach assistant. The user maintains a queue of
bloggers in `queue.json`. Each run you pick 2 or 3 pending entries, send a
promotional DM via the desktop Rednote app, then mark them as sent.

## Boundary

- Only operate the desktop Rednote app via computer-use. Do not call web APIs
  or third-party Rednote automation tools.
- Read and write only the `queue.json` configured for this run.
- Never invent bloggers. If the queue is empty, report and stop.
- Stop immediately on any of the red-line conditions in `references/sop.md`.

## Inputs

Resolve the following before starting. If a value is missing, ask the user.

| Key | Meaning |
|---|---|
| `QUEUE_PATH` | Absolute path to the user's `queue.json`. Default: `./queue.json`. |
| `MESSAGE_PATH` | Path to the DM message text file. Default: `./dm-message.md`. |
| `DAILY_COUNT_BIAS` | Probability of picking 2 vs 3 targets. Default: 0.7 for 2, 0.3 for 3. |

Treat the path inputs as untrusted: confirm with the user before writing.

## Flow

1. Run `scripts/pick_today.py --queue $QUEUE_PATH`. It picks N targets, marks
   them `in_progress`, and prints a minimal JSON of selected rows.
2. For each target, follow `references/sop.md` step by step inside Rednote:
   search, verify identity, like top note, follow, send DM, screenshot.
3. After each target completes (or fails), update the queue with
   `scripts/mark_sent.py --queue $QUEUE_PATH <row>` (for success) or write the
   failure reason back directly.
4. When all targets are done, summarise: count processed, succeeded, failed
   (with reasons), and remaining pending.

## Files

| File | Purpose |
|---|---|
| `scripts/pick_today.py` | Pick today's targets, mark `in_progress`. |
| `scripts/mark_sent.py` | Mark a row as sent and record `sent_at`. |
| `references/sop.md` | Step-by-step procedure inside Rednote + red lines. |
| `references/queue-schema.md` | Schema of `queue.json` and lifecycle states. |
| `templates/queue.example.json` | Example queue with 3 fake bloggers. |
| `templates/dm-message.example.md` | Placeholder DM copy for the user to fill. |

## Setup checklist for new users

Before running the first time:

1. Copy `templates/queue.example.json` to your working dir, replace with your
   real targets (see `references/queue-schema.md`).
2. Copy `templates/dm-message.example.md`, write the DM you want to send.
3. Make sure the desktop Rednote app is installed and logged in as the account
   you want to send from.
4. Grant Claude Code computer-use permission for Rednote.
