# Luma admin API cheatsheet

All endpoints are at `https://api.lu.ma`. Auth is via cookies. JSON in,
JSON out.

## Authentication

The browser sends two cookies that matter:

```
luma.did=<random-device-id>
luma.auth-session-key=usr-<user-id>.<session-secret>
```

Both come out of Chrome DevTools -> Application -> Cookies ->
`https://luma.com`. The `did` is a device ID; the `auth-session-key` is
the actual session credential. The `__cf_bm` cookie is Cloudflare bot
management and rotates every 30 minutes, it does not gate auth.

Sessions are long-lived (weeks or months) until the user logs out,
changes password, or terminates sessions explicitly.

## Endpoints

### GET /event/admin/get

Fetch the full admin-view JSON for an event.

```
GET https://api.lu.ma/event/admin/get?event_api_id=evt-XXXXXXXXXXXXX
Cookie: luma.did=...; luma.auth-session-key=...
```

Top-level keys returned:

```
access_level, event, luma_plus_active, luma_plan, stripe_account_id,
sessions, calendar, has_membership_tier, stripe_account, creator,
hosts, check_in_staff_count, ticket_types, guest_status_to_count,
payment_summary, emails_blocked, featured_info, featured_infos,
categories, membership_tiers
```

The interesting payload is under `event`. Fields actually used:

| field | type | notes |
|---|---|---|
| `api_id` | string | the immutable event ID (`evt-...`) |
| `url` | string | the 8-char public slug (luma.com/{url}) |
| `name` | string | title |
| `start_at` | ISO8601 in UTC | event start |
| `end_at` | ISO8601 in UTC | computed from start + duration |
| `duration_interval` | ISO8601 duration | `P0Y0M0DT3H0M0S` = 3h |
| `timezone` | string | e.g. `Europe/London`, `America/New_York` |
| `visibility` | string | `public` or `private` |
| `max_capacity` | int or null | null = unlimited |
| `waitlist_enabled` | bool | |
| `waitlist_status` | string | `disabled`, `enabled`, etc. |
| `cover_url` | string | must point to `images.lumacdn.com` |
| `social_image_url` | string | auto-generated OG card |
| `tint_color` | hex string | e.g. `#4ab2ea` |
| `font_title` | string or null | e.g. `ivy-mode`, null = default sans-serif |
| `theme_meta` | object | `{"theme": "legacy"}` etc. |
| `description_mirror` | object | ProseMirror JSON doc |
| `geo_address_info` | object | structured address, see below |
| `location_type` | string | `offline`, `online`, `tbd` |
| `event_type` | string | `independent`, `series_member`, etc. |
| `hide_rsvp` | bool | |
| `show_guest_list` | bool | |
| `recurrence_id` | string or null | for recurring series |
| `zoom_meeting_url` | string or null | |
| `virtual_info` | object | |
| `created_at` | ISO datetime | |
| `updated_at` | ISO datetime | |

`geo_address_info` shape:

```json
{
  "city": "London",
  "region": "England",
  "address": "{STREET ADDRESS}",
  "country": "United Kingdom",
  "country_code": "GB",
  "place_id": "ChIJ...",
  "full_address": "{STREET ADDRESS}, London EC4N 7BE, UK",
  "short_address": "{STREET ADDRESS}, London",
  "city_state": "London, United Kingdom",
  "region_short": "England",
  "sublocality": null,
  "apple_maps_place_id": "...",
  "type": "google",
  "mode": "shown",
  "description": "6th Floor, {Building or Host}",
  "localized": { "en-GB": { ... same shape ... } }
}
```

Note that `description` inside `geo_address_info` is the "further
instructions" text (floor, entry directions). Confusing because the
event also has its own `description_mirror`.

### POST /event/admin/update

Update any field on an existing event. Send only the fields you want to
change.

```
POST https://api.lu.ma/event/admin/update
Content-Type: application/json
Origin: https://luma.com
Referer: https://luma.com/event/manage/evt-XXX
Cookie: luma.did=...; luma.auth-session-key=...

{
  "event_api_id": "evt-XXXXXXXXXXXXX",
  "start_at": "2026-06-03T17:30:00.000Z",
  "duration_interval": "P0Y0M0DT3H0M0S"
}
```

Returns the updated event JSON.

Common update payloads:

Move event time (both fields required, see SKILL.md gotcha about
`end_at`):

```json
{"event_api_id": "...", "start_at": "...", "duration_interval": "P0Y0M0DT3H0M0S", "timezone": "Europe/London"}
```

Update description:

```json
{"event_api_id": "...", "description_mirror": {"type": "doc", "content": [...]}}
```

Change cover (URL must already be on `images.lumacdn.com`):

```json
{"event_api_id": "...", "cover_url": "https://images.lumacdn.com/uploads/.../..."}
```

Change appearance:

```json
{"event_api_id": "...", "tint_color": "#4ab2ea", "font_title": "ivy-mode"}
```

Set capacity:

```json
{"event_api_id": "...", "max_capacity": 20}
```

Toggle visibility:

```json
{"event_api_id": "...", "visibility": "private"}
```

### POST /event/create

Creates an event. Schema not fully reverse-engineered because the
browser UI for create + API for everything after is more reliable. If
you do try:

- `GET /event/create` returns 405 (method not allowed), confirms the
  endpoint exists.
- Must POST with a body.
- Required fields probably include `name`, `start_at`, plus calendar
  context.

If you reverse-engineer this, write down the schema in this file.

### Endpoints that do not exist

These return 404 or 405 and were checked while reverse-engineering:

- `/user/get-self`: 404
- `/user/get-managed-calendars`: 404
- `/event/admin/get-event`: 404 (note: `/event/admin/get` works)
- `/event/admin/update-event`: 404 (note: `/event/admin/update` works)
- `/image/upload`, `/upload/image`, etc.: all 404
- `/event/admin/upload-cover`: 404

The image upload endpoint is gated behind the SPA's internal logic. No
public REST entry has been found. Use UI upload.

### Endpoints that exist

- `/event/admin/get?event_api_id=...`: 200
- `/event/admin/update`: POST, 200
- `/event/create`: POST only (GET = 405)
- `/event/update`: POST only (GET = 405)
- `/home/get-events`: GET, returns the calling user's events list

## Time conversion

Luma stores everything in UTC. To convert local time to UTC for
`start_at`:

```python
# London 18:30 BST = 17:30 UTC (BST = UTC+1)
# London 18:30 GMT = 18:30 UTC (winter)
# New York 18:30 EDT = 22:30 UTC (EDT = UTC-4)
# New York 18:30 EST = 23:30 UTC (winter)
```

The `timezone` field is the display timezone, not the storage timezone.
Luma renders `start_at` using `timezone` to figure out what wall-clock
time to show.

For BST (March to October), subtract 1 hour from local to get UTC. For
GMT (November to February), local == UTC.

## Duration formats

ISO 8601 duration: `P[n]Y[n]M[n]DT[n]H[n]M[n]S`. Luma always uses the
full template even if values are zero.

| Length | `duration_interval` |
|---|---|
| 1 hour | `P0Y0M0DT1H0M0S` |
| 90 minutes | `P0Y0M0DT1H30M0S` |
| 2 hours | `P0Y0M0DT2H0M0S` |
| 2.5 hours | `P0Y0M0DT2H30M0S` |
| 3 hours | `P0Y0M0DT3H0M0S` |
| 4 hours | `P0Y0M0DT4H0M0S` |
| 6 hours | `P0Y0M0DT6H0M0S` |
| All day (24h) | `P0Y0M1DT0H0M0S` (1 day) |

## ProseMirror node shapes

The `description_mirror` field is a ProseMirror document. Supported
nodes observed in practice:

```json
{"type": "doc", "content": [
  {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]},
  {"type": "paragraph"},
  {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Who should come"}]},
  {"type": "paragraph", "content": [
    {"type": "text", "text": "We are "},
    {"type": "text", "text": "modular", "marks": [{"type": "bold"}]},
    {"type": "text", "text": " by design."}
  ]}
]}
```

Bullets are represented as `paragraph` nodes that begin with `• ` text.
Luma does not use ProseMirror's `bulletList` node type as far as
observed. The render still looks like bullets.

Untested but probably supported: `italic` marks, `link` marks,
ProseMirror's standard `bulletList` / `orderedList` nodes. If you try
and they fail, add notes here.

## Headers you should send

When calling the API from a server (not the browser), include these
headers so it behaves like a normal SPA request:

```
Cookie: luma.did=...; luma.auth-session-key=...
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0 Safari/537.36
Content-Type: application/json
Origin: https://luma.com
Referer: https://luma.com/event/manage/evt-XXX
```

The `User-Agent` and `Referer` are not strictly required but missing
them sometimes triggers Cloudflare's bot challenge.
