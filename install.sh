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
#   bash install.sh                  # from a local clone
#   bash install.sh --agent claude
#   bash install.sh --agent codex
#   bash install.sh --dest /custom/path
#   bash install.sh --check          # report agent + dest + install status, no changes
#

set -euo pipefail

REPO_URL="https://github.com/Haili321/haili-auto-mkt"
RAW_TARBALL="https://github.com/Haili321/haili-auto-mkt/archive/refs/heads/main.tar.gz"

AGENT=""
DEST=""
CHECK=0

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
    --check)
      CHECK=1
      shift
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

health_check() {
  if [[ -z "$AGENT" ]]; then
    AGENT="$(detect_agent)"
  fi
  local dest
  dest="$(resolve_dest)"

  echo "haili-auto-mkt health check"
  echo "  agent:       $AGENT"
  echo "  destination: $dest"

  if command -v python3 >/dev/null 2>&1; then
    echo "  python3:     $(command -v python3) ($(python3 --version 2>&1))"
  else
    echo "  python3:     MISSING (skills will not run)"
  fi

  if [[ ! -d "$dest" ]]; then
    echo "  status:      destination dir not yet created"
    echo "  installed:   0"
    return 0
  fi

  if [[ ! -w "$dest" ]]; then
    echo "  status:      destination dir NOT WRITABLE"
  else
    echo "  status:      ok (writable)"
  fi

  echo "  installed skills:"
  local count=0
  for skill_dir in "$dest"/*/; do
    [[ -d "$skill_dir" ]] || continue
    local name
    name="$(basename "$skill_dir")"
    if [[ -f "$skill_dir/SKILL.md" ]]; then
      printf "    - %s\n" "$name"
      count=$((count + 1))
    else
      printf "    - %s (no SKILL.md; broken install?)\n" "$name"
    fi
  done
  if [[ $count -eq 0 ]]; then
    echo "    (none)"
  fi

  if [[ -d "skills" ]]; then
    echo "  this repo provides:"
    for skill_dir in skills/*/; do
      [[ -d "$skill_dir" ]] || continue
      local name
      name="$(basename "$skill_dir")"
      if [[ -d "$dest/$name" ]]; then
        printf "    - %s (installed)\n" "$name"
      else
        printf "    - %s (not installed)\n" "$name"
      fi
    done
  fi
}

install_skills() {
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
  echo
  echo "(tip: run 'bash install.sh --check' to verify the install at any time.)"
}

main() {
  if [[ $CHECK -eq 1 ]]; then
    health_check
  else
    install_skills
  fi
}

main "$@"
