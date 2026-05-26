---
name: ph
description: |
  Product Hunt account-warming workflow. Pull the daily leaderboard,
  group by topic, and surface cross-topic upvote suggestions so a PH
  account looks like a real curious user rather than a single-vertical
  voter. Trigger phrases: "ph daily", "product hunt today", "/ph".
version: 0.1.0
metadata:
  requires:
    bins:
      - python3
    pip:
      - requests
    env:
      - PH_ACCESS_TOKEN (or .ph_tokens.json in cwd)
---

# Product Hunt Daily

Use this skill once a day to keep a Product Hunt account active without
looking spammy. The script reads the day's leaderboard via the PH GraphQL
API, groups posts by primary topic, and suggests upvote targets spread
across topics.

The goal is account warming, not vote manipulation: a real human still
opens the suggested links, reads, and chooses what to actually upvote or
comment. The script does not call any write endpoints.

## Boundary

- Never commit `.ph_tokens.json`. It's gitignored.
- The script only reads. Upvoting and commenting stay manual.
- One PH account, one cadence. Do not run this on multiple accounts in a
  single day from the same IP; PH treats coordinated voting harshly.

## Daily cadence (the actual warming routine)

The "warming" part isn't the script; it's the habit. The script just makes
the habit cheap to run.

1. Run `python3 scripts/ph_daily.py` in the morning. Read the digest.
2. Pick 5 to 8 products across different topics. Cross-topic matters more
   than vote count; voting only on AI products every day flags the account.
3. Open each product page on producthunt.com. Spend 20+ seconds reading
   the tagline and first comment. PH tracks dwell time per session.
4. Upvote the ones you'd actually try. Skip the ones you wouldn't; an
   account that upvotes everything looks fake.
5. Optionally leave one short, substantive comment on the product you find
   most interesting that day. Two sentences. No links. No promotion.
6. Close the tab. Do not loop.

Skip days are fine; long streaks of activity look more bot-like than an
honest weekly rhythm.

## Entry points

Today's leaderboard, human-readable digest:

```bash
python3 skills/ph/scripts/ph_daily.py
```

Specific date (UTC; PH closes boards on Pacific time, so very recent dates
may be empty):

```bash
python3 skills/ph/scripts/ph_daily.py 2026-05-18
```

Machine-readable JSON for piping into other tools:

```bash
python3 skills/ph/scripts/ph_daily.py --json
```

Suggest a different number of cross-topic picks:

```bash
python3 skills/ph/scripts/ph_daily.py --picks 5
```

## Setup

1. Create a developer access token at
   `https://www.producthunt.com/v2/oauth/applications`.
2. Either export `PH_ACCESS_TOKEN=...` in your shell, or copy
   `templates/ph_tokens.example.json` to `.ph_tokens.json` in your working
   directory and fill in `access_token`.

## Files

| File | Purpose |
|---|---|
| `scripts/ph_daily.py` | Fetcher + grouping + cross-topic picker. |
| `templates/ph_tokens.example.json` | Token file template. |

## What this skill is not

- It is not an upvote bot. PH's terms forbid that and the API endpoint for
  voting requires user OAuth, not the developer token.
- It is not a hunt-launching tool. For launching your own product, the
  hunting flow stays on PH's web UI.
- It is not a watchlist (no per-product tracking, no alerts on new posts
  from a maker). Add that as a separate script if you need it.
