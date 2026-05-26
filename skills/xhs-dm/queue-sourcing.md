# How we build the queue

The `xhs-dm` skill consumes a `queue.json`. This note explains how we build
and maintain the upstream blogger list it pulls from, so a new teammate or
agent can extend the list the same way.

## Single source of truth

We keep the master list in one spreadsheet, not scattered across notebooks
and exports. Each row is one blogger. Required columns per row:

| Column | Purpose |
|---|---|
| `name` | Display name on the platform. |
| `profile_url` | Canonical profile URL. |
| `genre` | One or two keywords describing what they post about. |
| `followers` | Latest follower count. |
| `top_work` | Title or excerpt of one notable note. Used to verify identity at send-time. |
| `tier` | `S` / `A` / `B` / unrated. See "Tiering" below. |
| `contact_hint` | Email if disclosed on the profile, otherwise `-`. |
| `notes` | Free-form: language, time zone, anything that affects when to reach out. |

`row` numbers in `queue.json` map directly to row numbers in this sheet, so
everyone is looking at the same record when discussing a target.

## Tiering

Bloggers get a tier based on relevance to our pitch + reach. We use four
buckets:

- `S`: high relevance, high reach, hand-curated. Worth direct human DM.
- `A`: high relevance, mid reach. Good for batch outreach by email or DM.
- `B`: relevant but smaller. Good for low-cost touchpoints like a public
  comment.
- unrated: discovered but not yet reviewed.

Tier is a judgement call. Write it down once and stop second-guessing it on
each send; re-tier in batches when you have new information.

## Growing the list

When the list needs more bloggers, we expand it from a keyword, not by
following follow-graphs at random. The flow is:

1. Pick a keyword that matches the pitch (a genre word, a competitor's
   product, a use case).
2. Pull the top results for that keyword from the platform's own search.
3. Deduplicate against the master sheet by `profile_url`.
4. For each new author, record `followers`, `top_work`, `genre`. Tag the row
   `unrated` to be triaged later.
5. Append to the master sheet.

A new keyword usually adds dozens of authors before duplicates dominate, at
which point switch to the next keyword.

## Building `queue.json`

`queue.json` is a filtered, ordered slice of the master sheet, not the sheet
itself. The pipeline:

1. Filter the master list by the criterion that matches the outreach channel
   (e.g. "no email on file" for DM-first channels; "has email" for the
   `brevo` skill).
2. Sort by tier (S, A, B, unrated), then by followers descending within each
   tier. This makes `pick_today.py`'s "top of pending" selection
   deterministic.
3. Emit rows into `targets` with `status = "pending"` and the original
   master-sheet `row` preserved.

When the master sheet grows, regenerate `queue.json` rather than editing in
place. Keep the old `queue.json` around as a snapshot.

## Hygiene rules

- Treat the master sheet as private. It contains personal data about real
  people; do not paste raw rows into chats or public docs.
- Maintain a blocklist of accounts to skip (official media, brands you
  already work with, anyone who asked to be left alone). Apply it both at
  list-growth time and at queue-build time.
- When a blogger replies, moves channels, or asks to be removed, update the
  master sheet first; let `queue.json` follow on the next regenerate.
