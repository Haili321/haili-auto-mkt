# haili-auto-mkt

Reusable Claude Code / Codex skills for marketing outreach workflows.

[中文版 README](./README.zh.md)

## What's in this repo

| Skill | What it does | Surfaces |
|---|---|---|
| `xhs-dm` | Drive the desktop Rednote (Xiaohongshu) app through a daily DM cadence: pick N targets from a queue, search, like, follow, send a DM, mark the result. | macOS desktop app via computer-use |

More skills will land here over time. Each skill is self-contained: an
`SKILL.md` Claude or Codex can read, scripts in `scripts/`, references in
`references/`, and copy templates in `templates/`.

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
│   └── xhs-dm/
│       ├── SKILL.md        # skill front-matter + procedure for the agent
│       ├── scripts/
│       │   ├── pick_today.py
│       │   └── mark_sent.py
│       ├── references/
│       │   ├── sop.md
│       │   └── queue-schema.md
│       └── templates/
│           ├── queue.example.json
│           └── dm-message.example.md
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
