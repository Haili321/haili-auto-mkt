# `queue.json` Schema

The queue file is a single JSON document with two top-level lists: `targets`
(everything past, present, and future) and `sent` (an append-only history for
quick auditing).

## Top-level shape

```json
{
  "created_at": "ISO8601 timestamp, when the queue was first built",
  "queue_size": 481,
  "description": "Free-form note about how the queue was assembled",
  "targets": [ ... ],
  "sent": [ ... ]
}
```

## Target entry

Each item in `targets` describes one blogger:

```json
{
  "row": 8,
  "name": "blogger display name",
  "profile_url": "https://www.xiaohongshu.com/user/profile/...",
  "genre": "freeform tag, e.g. AI/lifestyle",
  "followers": 12345,
  "top_work": "title or excerpt of the note you intend to like",
  "tier": "S | A | B | unrated",
  "tier_score": "10 (S)",
  "contact_hint": "email or '-' if none",
  "status": "pending | in_progress | sent | failed",
  "picked_at": "ISO8601, set when status moves to in_progress",
  "sent_at":   "ISO8601, set when status moves to sent",
  "failed_reason": "set only when status == failed",
  "actions": {
    "liked_post": true,
    "followed": true,
    "dm_sent": true,
    "dm_status": "success (no error indicator)"
  }
}
```

Only `row`, `name`, and `status` are strictly required. The other fields are
helpful for identity verification, pacing, and post-hoc analysis.

## Sent entry

Each item in `sent` is a compact audit trail:

```json
{ "row": 8, "name": "...", "sent_at": "ISO8601", "tier": "S" }
```

## Lifecycle

```
pending  --(picked by pick_today.py)-->  in_progress
in_progress --(success)-->               sent
in_progress --(failure)-->               failed
in_progress --(>1h stale, recovered)-->  pending
```

`pick_today.py` automatically recovers any `in_progress` entry whose
`picked_at` is older than 1 hour, treating it as a leftover from a crashed
run.

## Ordering convention

`pick_today.py` selects from the top of the pending list. Order your queue
however you like: by tier, by follower count, by hand-curated priority. Do
not shuffle randomly: once you settle on an order, the deterministic top-of-
list selection makes the daily cadence predictable.

Recommended ordering: tier S, then A, then B, then unrated. Within each tier,
sort by followers descending.

## Privacy and PII

`queue.json` contains personal data about other people. Keep it out of git
(see `.gitignore`), do not paste raw entries into public chats, and treat
exports as you would any contact list.
