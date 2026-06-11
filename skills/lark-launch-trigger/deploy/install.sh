#!/usr/bin/env bash
# Install the always-on @mention listener as a macOS launchd agent.
# Auto-starts on login, auto-restarts on crash, and keeps the Mac awake
# (caffeinate) so the Lark long connection stays alive 24/7.
#
# Usage:
#   bash deploy/install.sh [WORKDIR]
#
# WORKDIR (default: current dir) must hold lark_config.json and
# trigger_config.json. Logs land in WORKDIR/logs/.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$HERE/../scripts" && pwd)"
WORKDIR="$(cd "${1:-$PWD}" && pwd)"
PY="$(command -v python3)"
LABEL="com.lark-launch-trigger.listener"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOGDIR="$WORKDIR/logs"
mkdir -p "$LOGDIR"

[ -n "$PY" ] || { echo "python3 not found on PATH"; exit 1; }
[ -f "$WORKDIR/lark_config.json" ] || { echo "missing $WORKDIR/lark_config.json"; exit 1; }
[ -f "$WORKDIR/trigger_config.json" ] || { echo "missing $WORKDIR/trigger_config.json"; exit 1; }

# Dependency sanity check before installing.
( cd "$WORKDIR" && "$PY" -c "import lark_oapi" ) \
  || { echo "lark-oapi missing. Install it: $PY -m pip install lark-oapi"; exit 1; }

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-is</string>
    <string>$PY</string>
    <string>$SCRIPTS/lark_at_listener.py</string>
  </array>
  <key>WorkingDirectory</key><string>$WORKDIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOGDIR/listener.out.log</string>
  <key>StandardErrorPath</key><string>$LOGDIR/listener.err.log</string>
  <key>ProcessType</key><string>Background</string>
</dict>
</plist>
EOF

plutil -lint "$PLIST" >/dev/null \
  || { echo "generated plist failed validation (unusual characters in a path?): $PLIST"; exit 1; }

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed and started: $LABEL"
echo "  python:   $PY"
echo "  scripts:  $SCRIPTS"
echo "  workdir:  $WORKDIR"
echo "  logs:     $LOGDIR/listener.{out,err}.log"
echo
echo "Verify:   launchctl list | grep lark-launch"
echo "Tail log: tail -f \"$LOGDIR/listener.out.log\""
