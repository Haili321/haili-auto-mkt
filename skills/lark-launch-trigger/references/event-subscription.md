# Event subscription setup (and the traps)

How to make a Lark app receive @mentions in real time over a long connection.
Every step here was learned the hard way; skipping one produces the same
symptom (a healthy WebSocket that never receives an event), so check all of
them in order.

## Console setup, in order

In the Lark developer console (open.larksuite.com, or open.feishu.cn for the
CN tenant), open your app:

1. Permissions and Scopes: make sure the app has the message read scopes
   (reading messages in group chats; "Receive users' mentions" appears as a
   required scope when you add the event below). Adding scopes requires a
   version release later.

2. Events and Callbacks -> Event Configuration -> Subscription mode: choose
   "Receive events through persistent connection". Click Verify while a
   listener process is running (start `scripts/lark_at_listener.py` first);
   the console should show "Connected". Save.

3. Add Events: search "message" and add "Message received"
   (`im.message.receive_v1`). Tip: the search box matches event names, so
   "receive message" finds nothing; "message" does.

4. Publish a version. Version Management and Release -> create version ->
   submit. Apps inside one org are usually exempt from review and go live
   instantly. THE SUBSCRIPTION DOES NOT DELIVER EVENTS UNTIL THE VERSION IS
   RELEASED. The console banner "changes will take effect after the current
   version is published" means exactly what it says.

5. Reconnect. Connections established before the release may not carry the
   new subscription. Restart the listener once after publishing.

## The webhook-bot trap (read this twice)

A Lark group can contain two completely different kinds of "bot":

- The APP's bot: the bot of your developer-console app. @mentioning IT is
  what fires `im.message.receive_v1` to your subscription.
- A custom/webhook bot: added from the group's settings ("Add bot" with an
  incoming-webhook URL). It can only POST INTO the group. It receives
  nothing, and @mentioning it fires nothing, ever.

If your WebSocket is connected (pings fine) and events never arrive, check
which bot is being @mentioned. Compare ids:

- Your app bot's id: `GET /open-apis/bot/v3/info` -> `bot.open_id`.
- The id being mentioned: read the message; `mentions[].id.open_id`.

If they differ, add the app's bot to the group (group settings -> add the
app, or via API `POST /im/v1/chats/{chat_id}/members?member_id_type=app_id`)
and @ THAT bot. The scripts in this skill resolve the app bot's open_id
automatically so the comparison is always against the right id.

## Reading message history (for the polling fallback)

- `GET /im/v1/messages?container_id_type=chat&container_id=oc_...` returns
  OLDEST FIRST by default. Pass `sort_type=ByCreateTimeDesc` for newest
  first, or a small page of "recent" messages will actually be the oldest.
- `msg_type=text`: content is `{"text": "..."}`; mentions appear inline as
  `@_user_1` placeholders, with the real ids in the `mentions` array.
- `msg_type=post` (rich text): content is a nested structure of lines and
  tagged elements; collect `tag=text` text and `tag=a` hrefs. A URL pasted
  into a rich-text message arrives as an `a` element, not in the text.

## Testing without a teammate

You can @mention a bot via the API (useful for self-testing the pipeline):
send a `post` message whose content includes an `at` element with the BOT's
open_id. With the app bot's id, the message registers as a real mention
(`mentions[].mentioned_type=bot`) and fires the event; with a webhook bot's
id it silently degrades (mentions stays null), which is also how you can
detect the trap above.

## Event payload, the parts that matter

```json
{
  "header": {"event_type": "im.message.receive_v1", "app_id": "cli_..."},
  "event": {"message": {
      "chat_id": "oc_...",
      "message_id": "om_...",
      "message_type": "post",
      "content": "{...}",
      "mentions": [{"id": {"open_id": "ou_..."}, "mentioned_type": "bot"}]
  }}
}
```

Dedup on `message_id`: long connections can redeliver, and teammates can
@ the bot twice with the same link.
