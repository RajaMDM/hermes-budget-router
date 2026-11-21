#!/usr/bin/env bash
# Move routine Hermes background tasks to a cheap model (default: Claude Haiku).
# Usage: aux-to-cheap.sh [provider] [model]   e.g.  aux-to-cheap.sh gemini gemini-3.5-flash
# Leaves approval, vision, mcp,
# skills_hub and triage_specifier on "auto" (your main model).
# Backs up config.yaml first. Restore with: cp ~/.hermes/config.yaml.bak ~/.hermes/config.yaml
set -euo pipefail

CONFIG="${HERMES_HOME:-$HOME/.hermes}/config.yaml"
PROVIDER="${1:-anthropic}"
MODEL="${2:-claude-haiku-5-5}"
TARGETS="compression title_generation session_search flush_memories curator web_extract"

[[ -f "$CONFIG" ]] || { echo "No config at $CONFIG" >&2; exit 1; }
grep -q '^auxiliary:' "$CONFIG" || { echo "No auxiliary: section in $CONFIG (older Hermes?)" >&2; exit 1; }

cp "$CONFIG" "$CONFIG.bak"
awk -v targets="$TARGETS" -v model="$MODEL" -v provider="$PROVIDER" '
BEGIN { n = split(targets, t, " "); for (i = 1; i <= n; i++) want[t[i]] = 1 }
/^auxiliary:/            { aux = 1; print; next }
aux && /^[a-z]/          { aux = 0 }
aux && /^  [a-z_]+:$/    { blk = $1; sub(":", "", blk) }
aux && (blk in want) && /^    provider:/ { print "    provider: " provider; next }
aux && (blk in want) && /^    model:/    { print "    model: " model; next }
{ print }
' "$CONFIG.bak" > "$CONFIG"

before=$(wc -l < "$CONFIG.bak"); after=$(wc -l < "$CONFIG")
[[ "$before" -eq "$after" ]] || { echo "Line count changed ($before → $after); restoring backup" >&2; cp "$CONFIG.bak" "$CONFIG"; exit 1; }

echo "Changed lines: $(diff "$CONFIG.bak" "$CONFIG" | grep -c '^>' || true)"
awk '/^auxiliary:/{f=1} f&&/^[a-z]/&&!/^auxiliary:/{exit} f' "$CONFIG" | grep -E '^  [a-z_]+:|provider:|model:'
echo "Start a new Hermes session to apply. Backup: $CONFIG.bak"
