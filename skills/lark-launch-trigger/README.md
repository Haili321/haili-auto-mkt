# Lark Launch Trigger

[中文](README.zh.md)

@ the bot with a link. Get a reviewed launch email two seconds later.

This skill is the missing trigger for the [brevo launch pipeline](../brevo/):
instead of you starting an agent by hand, a teammate @mentions a bot in a
Lark group with a product link, and the pipeline starts itself. The listener
holds a long-connection WebSocket to Lark (the process dials out; no public
server, no inbound firewall hole, no polling), so the event lands in about
one second.

## The flow

```mermaid
sequenceDiagram
    autonumber
    participant T as Teammate in Lark group
    participant L as Listener (always-on, WebSocket)
    participant H as Handler
    participant B as Brevo
    participant R as Reviewer inbox

    T->>L: @bot + product link
    Note over T,L: about 1 second, event push
    L->>H: link + chat_id (dedup by message_id)
    alt prepared model (slug in link_map)
        H->>B: send prepared request as TEST
        B-->>R: test email lands
        H-->>T: "Done. Sent the TEST. Subject ... id ..."
    else new model
        H->>H: queue for the compose agent
        H-->>T: "Queued; drafting from the official pages"
        Note over H: a timer-driven agent composes,<br/>test-sends, then registers the model
    end
    R-->>B: human approves, mass send (manual, always)
```

Measured on a real run: @mention to "test email in the reviewer's inbox plus
status posted back in the group" took about 2 seconds end to end.

## Why a long connection

| | Polling history | Webhook callback | Long connection (this skill) |
|---|---|---|---|
| Latency | minutes (cron gap) | ~1s | ~1s |
| Needs a public server | no | yes | no |
| Misses messages | can, between polls | no | no |
| Setup | message read scope | URL + signature verify | one console toggle |

The polling variant still ships (`scripts/poll_trigger.py`) for environments
where an always-on process is impossible.

## Quick start

```bash
# 1. configs (both gitignored)
cp skills/lark/templates/lark_config.example.json ./lark_config.json
cp skills/lark-launch-trigger/templates/trigger_config.example.json ./trigger_config.json
# fill in: app credentials, reviewer_email, url_filter, link_map

# 2. one-time console setup (persistent connection + Message received event + release)
#    -> references/event-subscription.md  (read the webhook-bot trap!)

# 3. run
python3 -m pip install lark-oapi
python3 skills/lark-launch-trigger/scripts/lark_at_listener.py   # foreground
bash skills/lark-launch-trigger/deploy/install.sh "$PWD"         # or 24/7 launchd
```

Then in the group:

```
@YourBot https://your-platform.example.com/models/your-model
```

## The one trap worth knowing upfront

A group can contain the APP's bot and a custom webhook bot, and they look
identical in the member list. Only @mentions of the APP's bot fire events;
the webhook bot can only post, never receive. If the WebSocket is connected
and nothing ever arrives, you are probably @ing the wrong bot. Details and
the id check: [references/event-subscription.md](references/event-subscription.md).

## Safety model

The trigger can only ever cause one TEST email to the configured reviewer.
Unknown links are queued, not sent. The mass send to a real contact list is
a human decision inside Brevo, every time.
