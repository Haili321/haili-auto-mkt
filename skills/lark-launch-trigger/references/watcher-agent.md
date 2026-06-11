# Watcher agent: composing emails for queued (new) models

The listener answers instantly for models that already have a prepared Brevo
request. Links it has never seen go to a queue instead. A second, timer-driven
agent (the "watcher") drains that queue by composing the email from official
sources and sending the reviewer test. This file is the prompt/playbook for
that agent.

## Wiring

Schedule a tick every few minutes (cron shown; a launchd timer works too):

```
*/5 * * * * cd /path/to/workdir && /path/to/agent-cli -p "$(cat /path/to/this/watcher-agent.md)"
```

Any agent CLI that can read files, browse the web, and run shell commands
works. The tick is cheap when the queue is empty: check, exit.

## Instructions to the agent

You are the supervising agent for the launch-email workflow. Work from the
current directory (it holds `trigger_config.json` and the queue). Be concise.

On each run:

1. Health check. Confirm the listener launchd job is loaded
   (`launchctl list | grep lark-launch`); skim the tail of
   `logs/listener.err.log` for crash loops. Report problems, do not fix
   silently.

2. Process the queue. For each `<queue_dir>/pending/*.json`
   (`{"link", "chat_id", "queued_at", "status"}`):
   - Compose and test-send by the playbook below.
   - On success move the file to `<queue_dir>/done/`; on failure leave it
     and log why.

3. Stop. Never mass-send anything. Only the single TEST email goes out.

## Compose playbook (per queued link)

This is the urgent-launch flow from the sibling brevo skill; the full version
lives at `skills/brevo/references/urgent-launch.md`. Condensed:

1. Open the model's official vendor page and the product page from the link.
   Pull benchmarks, capabilities, and pricing from official sources only.
2. Write the copy in house style: front-load and `**bold**` the strongest
   "beats Competitor X" comparison, no em dashes, short human sentences,
   conservative claims with a source for every number.
3. Get a clean PUBLIC header image (vendor CDN or official page). If it is
   not directly hostable, import it with the brevo skill's
   `brevo_image_import.py` to get a permanent Brevo URL.
4. Fill a spec JSON (start from the brevo skill's
   `templates/model_launch_spec.example.json`) and build:
   `build_model_email.py --spec ... --out-html ... --out-request ...`.
5. Test-send to the reviewer only:
   `run_brevo_email.py --request-file <request> --send --test-to <reviewer_email>`
   (reviewer_email comes from trigger_config.json).
6. Post a status line back to the trigger's `chat_id` (the handler's
   `send_text` helper in `scripts/_lark_api.py` does this): subject, Brevo
   messageId, and that the draft is staged for human approval.
7. Register the model so the NEXT @mention of the same link sends instantly:
   add its slug to `link_map` in `trigger_config.json` pointing at the built
   request JSON.

## Guardrails

- TEST send only, to the reviewer address. The mass send is a human action
  in Brevo.
- If official pages are unclear or pricing cannot be verified, do NOT send.
  Post a question to the group and leave the trigger pending.
- Never invent benchmarks, prices, or links.
