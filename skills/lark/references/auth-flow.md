# Auth flow: tenant vs user tokens

Lark exposes two token types. Picking the right one matters because they
unlock different API surfaces and have different setup costs.

## Tenant access token (app-only)

What it is: a token that proves "this app, acting on its own behalf."

When to use:

- Reading docs / sheets the app has been granted access to.
- Writing to documents the app owns (e.g. bot output).
- Sending bot messages to chats the app has joined.
- Anything where you do not need to impersonate a specific user.

How to get it: nothing. `LarkClient.get_tenant_token()` calls the
`tenant_access_token/internal` endpoint with your `app_id` + `app_secret`
and caches the result for 2 hours. Just call `as_user=False` (the default)
on any client method.

## User access token (OAuth)

What it is: a token that proves "this app, acting on behalf of a specific
human user." Required for endpoints that read or write user-owned data
(personal drive files, sending as a user, calendar, etc).

When to use:

- Reading a doc / sheet that the app does not have direct access to but
  the user does.
- Sending a message as a user (not as a bot).
- Creating files in the user's personal drive.
- Anything in the Lark docs that says "User access token required."

How to get it: a one-time OAuth dance.

1. Run `python3 skills/lark/scripts/lark_auth.py`.
2. Browser opens, you approve the app.
3. The script catches the redirect, exchanges the code for an
   `access_token` + `refresh_token`, and writes them to
   `./.lark_tokens.json`.
4. After this, set `as_user=True` on client calls. `LarkClient` refreshes
   the access token automatically when it expires (~2h) using the
   refresh token.

The refresh token itself does not expire unless you revoke it from the
Lark admin console or the user changes their password.

## Token cache

| Path | Contents | Lifetime |
|---|---|---|
| In-memory `_tenant_token` | App tenant token | ~2h |
| `./.lark_tokens.json` | `refresh_token` + cached `user_access_token` + expiry | Refresh token: long-lived. Access token: ~2h, refreshed on demand. |

Override the cache location with `LARK_TOKEN_CACHE=/path/to/file.json`.
Override the config location with `LARK_CONFIG=/path/to/config.json`.

## Scopes

Scopes are configured per-app in the Lark Open Platform admin UI, not in
code. The `lark_auth.py` script does not pass a `scope` param, so the
OAuth consent screen shows whatever scopes you've already enabled for
the app.

If you call an endpoint and get an error like `99991663` (`permission
denied`), add the missing scope to your app, then re-run `lark_auth.py`
so the user re-grants with the wider scope set.
