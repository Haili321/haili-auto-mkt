# Xiaohongshu DM SOP

Step-by-step procedure the assistant follows inside the desktop Rednote app
for each target picked by `pick_today.py`.

## Preconditions

- Desktop Rednote app installed and logged in as the sender account.
- Claude has computer-use permission for Rednote.
- `queue.json` exists at the configured path and has at least one entry with
  `status == "pending"`.
- A DM message file exists at the configured path.

## Trigger

The user types a phrase such as `跑今日 DM`, `run today xhs dm`, or invokes
the skill via `/xhs-dm`.

## Per-target procedure

For each blogger in the picked list, run the following in order. If any
sub-step fails, jump to "Mark failed" at the end.

### 1. Locate and verify

1. Activate Rednote (`open_application "rednote"`).
2. Tap the Home tab in the bottom bar.
3. Tap the search field, type `blogger.name`.
4. Under the Users tab in results, locate the entry whose avatar and display
   name match the queue entry.
5. Tap the avatar to enter their profile.
6. Cross-check identity using name, avatar, genre, and (if available) the
   profile URL stored in the queue.
7. Confirm the follow button shows `Follow` (not `Following` or `Mutual`).
8. If verification fails (not found, name mismatch, already following, banned),
   stop and mark this blogger as failed with the reason.

### 2. Open top note and like

1. Tap the first item in the Notes list (typically pinned or most recent).
2. Once the note opens, tap the heart icon at the bottom.
3. Zoom-verify the heart turns red and the count increases by 1.
4. If liking fails, record the partial failure but continue with follow + DM.

### 3. Follow and DM

1. From the note view, tap the `Follow` button in the top-right. It should
   change to `Following`.
2. Zoom-verify the button text.
3. Tap the avatar or name to return to the profile.
4. Tap the chat bubble icon (to the right of the `Following` button) to open
   DM.
5. If a "Recently viewed note" suggestion card appears, dismiss it with the X.
6. Read the DM message from the configured `MESSAGE_PATH`, write it to the
   clipboard with `write_clipboard`.
7. Tap the message input to focus it.
8. Paste with Cmd+V.
9. Wait 3 seconds.
10. Zoom-verify the pasted text matches the source file end-to-end (cursor at
    the final character).
11. Wait 5 more seconds (total 8s) to mimic human pacing.
12. Press Return to send.
13. Screenshot the result for archival.

### 4. Mark result

- Success: run `scripts/mark_sent.py --queue $QUEUE_PATH <row>`. This sets
  `status = sent`, adds `sent_at`, and appends to `sent` history.
- Failure: open `queue.json` directly, set `status = failed`, add
  `failed_reason` describing the cause, and remove `picked_at`.

## End-of-run report

After all picked targets are processed, report to the user:

- Processed today: N
- Succeeded: X
- Failed: Y (list each with reason)
- Pending remaining: M

## Red lines (stop immediately)

Stop the run and notify the user if any of the following occurs:

- Rednote shows a risk-control warning, rate-limit notice, or unusual-login
  prompt.
- The DM send returns a red error icon (server rejected the message).
- Three consecutive search failures in a row (search behavior may have
  changed).
- The same blogger is picked twice in one session (queue state corrupted).
- The user issues a stop command.

## Pacing rules

- Default daily volume: 2 or 3 targets (configurable via `DAILY_COUNT_BIAS`).
- Always include 5 to 10 seconds of human-paced waiting between actions.
- Do not run more than once per day on the same sender account.
