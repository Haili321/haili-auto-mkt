# haili-auto-mkt

Reusable Claude Code / Codex skills for marketing outreach workflows.

[中文版 README](./README.zh.md)

## What's in this repo

| Skill | What it does | Surfaces |
|---|---|---|
| `brevo` | Draft, dry-run, test-send, and officially send transactional outreach emails through Brevo's API. One email per recipient, audit logs per run. | Brevo HTTP API |
| `lark` | Read and write Lark (Feishu international) docs, sheets, drive files, and messages. Ships a `LarkClient` library + one-time OAuth helper + JSON-to-sheet pusher. | Lark Open Platform API |
| `ph` | Daily Product Hunt account-warming: pull the leaderboard, group by topic, surface cross-topic upvote suggestions so the account looks like a curious user rather than a single-vertical voter. | Product Hunt GraphQL API |
| `xhs-dm` | Drive the desktop Rednote (Xiaohongshu) app through a daily DM cadence: pick N targets from a queue, search, like, follow, send a DM, mark the result. | macOS desktop app via computer-use |

Each skill is self-contained: an `SKILL.md` Claude or Codex can read,
scripts in `scripts/`, references in `references/`, and copy templates
or examples for the user to fill in.

## How the three skills fit together

The skills are independent at the Python level (no cross-skill imports),
but they're designed to compose under an agent that orchestrates them.
Typical chains:

| Chain | Flow |
|---|---|
| `lark` → `brevo` | Read finalised outreach copy and recipients from a Lark doc or sheet; the agent assembles a Brevo request JSON per recipient; `brevo` dry-runs, test-sends, then officially sends. |
| `xhs-dm` → `lark` | After `pick_today.py` and a DM run, the agent calls `LarkClient.update_sheet_values` to tick a status column on the source sheet, keeping the Lark tracker in sync with `queue.json`. |
| `lark` → `xhs-dm` | The agent reads a blogger list from a Lark sheet via `LarkClient.get_sheet_values`, transforms rows into the `queue.json` schema, and hands off to `xhs-dm`. |
| `brevo` + `xhs-dm` | Run `brevo` outreach first; after a follow-up window, the agent moves no-reply recipients into the `xhs-dm` queue for a second channel. |

These chains are orchestrated by the agent reading each skill's `SKILL.md`
and the references; no glue scripts ship in this repo yet. If a chain
becomes routine, the natural next step is to add a small driver script
under the skill that owns the destination side.

## One-line install

Paste this sentence to Claude Code or Codex:

```text
Install haili-auto-mkt from https://raw.githubusercontent.com/Haili321/haili-auto-mkt/main/install.sh into the default skills dir for the current agent, then run a health check.
```

Or run the installer yourself:

```bash
curl -fsSL https://raw.githubusercontent.com/Haili321/haili-auto-mkt/main/install.sh | bash
```

The installer copies each subdirectory of `skills/` into
`~/.claude/skills/` (or `${CODEX_HOME:-~/.codex}/skills/` for Codex) and
skips skills that are already installed. Pass `--agent claude` or
`--agent codex` to force a target, or `--dest /custom/path` to install
elsewhere.

## Direct shell usage

You can also call the scripts without going through an agent. From a local
clone:

```bash
cp skills/xhs-dm/templates/queue.example.json ./queue.json
cp skills/xhs-dm/templates/dm-message.example.md ./dm-message.md
# Edit both files with your real targets and copy.

python3 skills/xhs-dm/scripts/pick_today.py --queue ./queue.json --count 2
# (run the SOP in Rednote by hand or via an agent)
python3 skills/xhs-dm/scripts/mark_sent.py --queue ./queue.json 2 3
```

## Layout

```
haili-auto-mkt/
├── install.sh              # one-shot installer for Claude Code / Codex
├── skills/
│   ├── brevo/              # Brevo transactional email
│   │   ├── SKILL.md
│   │   ├── scripts/        # run_brevo_email.py + bootstrap wrapper
│   │   ├── references/     # request schema
│   │   ├── examples/       # minimal + outreach request templates
│   │   └── .env.example
│   ├── lark/               # Lark / Feishu international API
│   │   ├── SKILL.md
│   │   ├── scripts/        # lark_client.py + lark_auth.py + push_to_sheet.py
│   │   ├── references/     # auth-flow + sheet-recipes
│   │   └── templates/      # lark_config.example.json
│   ├── ph/                 # Product Hunt daily warming
│   │   ├── SKILL.md
│   │   ├── scripts/        # ph_daily.py
│   │   └── templates/      # ph_tokens.example.json
│   └── xhs-dm/             # Xiaohongshu desktop DM workflow
│       ├── SKILL.md
│       ├── scripts/        # pick_today.py + mark_sent.py
│       ├── references/     # sop + queue-schema
│       └── templates/      # queue + dm-message examples
├── LICENSE
└── README.md
```

## Design notes

- Skills are read-mostly. The agent reads `SKILL.md`, then chooses scripts
  to invoke. State lives in the user's own `queue.json` and DM message file,
  never inside this repo.
- Scripts are dependency-free: standard library Python 3 only. No virtualenv
  needed.
- Privacy first. The `.gitignore` blocks `queue.json` and `dm-message.md` so
  real target lists and outreach copy do not leak into commits.
- External integrations such as Lark, Notion, Airtable are deliberately not
  built in. Wrap `mark_sent.py` in your own driver if you want to mirror
  results to an external sheet.

## License

MIT. See [LICENSE](./LICENSE).
