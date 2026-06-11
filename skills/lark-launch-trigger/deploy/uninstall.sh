#!/usr/bin/env bash
# Stop and remove the always-on listener launchd agent.
set -uo pipefail
LABEL="com.lark-launch-trigger.listener"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "Stopped and removed $LABEL"
