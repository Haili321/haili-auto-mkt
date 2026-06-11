---
name: lark-launch-trigger
description: |
  Turn a Lark group @mention into an instant launch-email pipeline. An
  always-on listener receives "@bot + product link" over a long-connection
  WebSocket (about 1 second, no public server), test-sends a prepared Brevo
  email for known models, queues new models for a compose agent, and posts
  status back into the group. Trigger phrases: "lark trigger", "@bot launch",
  "launch listener", "/lark-launch-trigger".
metadata:
  requires:
    bins:
      - python3
    pip:
      - lark-oapi
    skills:
      - brevo (sibling skill, used for the actual email build + send)
---

# Lark Launch Trigger

Use this skill to let a teammate kick off the brevo launch-email pipeline by
@mentioning a bot in a Lark group with a product link. The listener receives
the mention in about a second over a persistent WebSocket (the process dials
out to Lark; no public server, no polling), and either test-sends a prepared
email or queues the link for a compose agent.

## Boundary

- Never commit `lark_config.json`, `trigger_config.json`, or the queue dir.
  All three are gitignored at the repo root.
- The handler only ever sends ONE TEST email, to `reviewer_email`. Mass
  sending to a contact list stays a human action inside Brevo.
- @mentions of anything other than this app's own bot are ignored by design;
  so are messages without a link matching `url_filter`.

## Setup

1. One-time console setup for the Lark app (persistent connection, the
   `im.message.receive_v1` event, version release) and the webhook-bot trap:
   read `references/event-subscription.md`. Add the app's bot to the group.
2. In a working directory, create the two configs (both stay local):

   ```bash
   cp skills/lark/templates/lark_config.example.json ./lark_config.json
   cp skills/lark-launch-trigger/templates/trigger_config.example.json ./trigger_config.json
   # fill in app_id/app_secret, reviewer_email, url_filter, link_map
   ```

3. The brevo skill must be installed alongside (same `skills/` parent) or
   point `brevo_script` in trigger_config.json at `run_brevo_email.py`.
   `BREVO_API_KEY` comes from the working dir's `.env.local`, as in the
   brevo skill.
4. `python3 -m pip install lark-oapi`

## Run

Foreground (first test):

    python3 skills/lark-launch-trigger/scripts/lark_at_listener.py

Always-on (macOS launchd: starts at login, restarts on crash, keeps the
machine awake):

    bash skills/lark-launch-trigger/deploy/install.sh "$PWD"
    launchctl list | grep lark-launch        # verify
    bash skills/lark-launch-trigger/deploy/uninstall.sh   # stop + remove

Then, in the Lark group: `@YourBot https://your-platform.example.com/models/your-model`

## How a trigger is handled

1. Event arrives; text is flattened (plain text and rich-text posts both
   work, pasted links arrive as `a` elements in posts).
2. Fires only if the app bot is @mentioned AND a link passes `url_filter`.
   Dedup by `message_id`.
3. `handle_launch.run_launch(link, chat_id)`:
   - slug in `link_map` -> run brevo's `run_brevo_email.py --send --test-to
     <reviewer_email>` with the prepared request; post subject + messageId
     back to the group.
   - unknown link -> write `{link, chat_id, queued_at, status}` to
     `<queue_dir>/pending/` and ack in the group. A timer-driven compose
     agent drains the queue: `references/watcher-agent.md`.

## Files

- `scripts/lark_at_listener.py` - the always-on WebSocket listener
- `scripts/handle_launch.py` - known-model send / new-model enqueue + post-back
- `scripts/poll_trigger.py` - polling fallback when the listener cannot run
- `scripts/_lark_api.py` - stdlib-only tenant-token helpers (send, bot info)
- `deploy/install.sh`, `deploy/uninstall.sh` - launchd always-on install
- `references/event-subscription.md` - console setup + the traps that cost hours
- `references/watcher-agent.md` - the compose agent for queued new models
- `templates/trigger_config.example.json`
