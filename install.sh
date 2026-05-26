#!/usr/bin/env bash
#
# Install haili-auto-mkt skills into the current agent's global skills dir.
#
# Behaviour:
#   - Claude Code: copies skills/* into ~/.claude/skills/
#   - Codex:       copies skills/* into ${CODEX_HOME:-$HOME/.codex}/skills/
#   - Auto-detect: prefers Claude Code if both dirs are detectable.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Haili321/haili-auto-mkt/main/install.sh | bash
#   bash install.sh            # from a local clone
#   bash install.sh --agent claude
#   bash install.sh --agent codex
#   bash install.sh --dest /custom/path
#

set -euo pipefail

REPO_URL="https://github.com/Haili321/haili-auto-mkt"
RAW_TARBALL="https://github.com/Haili321/haili-auto-mkt/archive/refs/heads/main.tar.gz"

AGENT=""
DEST=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT="$2"
      shift 2
      ;;
    --dest)
      DEST="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

detect_agent() {
  if [[ -d "$HOME/.claude" ]]; then
    echo "claude"
  elif [[ -d "${CODEX_HOME:-$HOME/.codex}" ]]; then
    echo "codex"
  else
    echo "claude"
  fi
}

resolve_dest() {
  if [[ -n "$DEST" ]]; then
    echo "$DEST"
    return
  fi
  case "$AGENT" in
    claude) echo "$HOME/.claude/skills" ;;
    codex)  echo "${CODEX_HOME:-$HOME/.codex}/skills" ;;
    *) echo "unknown agent: $AGENT" >&2; exit 1 ;;
  esac
}

ensure_source() {
  if [[ -d "skills" ]]; then
    echo "$(pwd)"
    return
  fi

  local tmp
  tmp="$(mktemp -d)"
  echo "fetching $REPO_URL ..." >&2
  curl -fsSL "$RAW_TARBALL" | tar -xz -C "$tmp"
  echo "$tmp"/haili-auto-mkt-*
}

main() {
  if [[ -z "$AGENT" ]]; then
    AGENT="$(detect_agent)"
  fi

  local dest
  dest="$(resolve_dest)"
  mkdir -p "$dest"

  local src
  src="$(ensure_source)"

  echo "agent: $AGENT"
  echo "source: $src/skills"
  echo "destination: $dest"

  for skill_dir in "$src"/skills/*/; do
    local name
    name="$(basename "$skill_dir")"
    if [[ -d "$dest/$name" ]]; then
      echo "skipping $name (already installed at $dest/$name)"
      continue
    fi
    cp -R "$skill_dir" "$dest/$name"
    echo "installed $name -> $dest/$name"
  done

  echo
  echo "done. restart your agent to pick up the new skills."
}

main "$@"
