#!/usr/bin/env bash
# Generate the video narration with macOS's built-in text-to-speech (local, free, nothing uploaded).
# Usage (from the repo root):  bash docs/demo/voice/make-voice.sh  [voice name]
# Best quality: install a Premium voice first via System Settings → Accessibility → Spoken Content
#   → System Voice → Manage Voices… (e.g. "Ava (Premium)" or "Zoe (Premium)"), then re-run.
set -euo pipefail
cd "$(dirname "$0")"
command -v say >/dev/null || { echo "This script needs macOS 'say'." >&2; exit 1; }

pick_voice() {
  local available; available="$(say -v '?' | sed -E 's/ +[a-z]{2}_[A-Z]{2}.*//')"
  for v in "Ava (Premium)" "Zoe (Premium)" "Allison (Premium)" "Ava (Enhanced)" "Zoe (Enhanced)" \
           "Allison (Enhanced)" "Samantha (Enhanced)" "Susan (Enhanced)" "Samantha"; do
    if grep -Fxq "$v" <<<"$available"; then echo "$v"; return; fi
  done
  echo "Samantha"
}
VOICE="${1:-$(pick_voice)}"
RATE="${RATE:-172}"
echo "Voice: $VOICE  (rate $RATE wpm)"

while IFS='|' read -r key text; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  say -v "$VOICE" -r "$RATE" -o "vo_${key}.aiff" "$text"
  afconvert -f WAVE -d LEI16@44100 "vo_${key}.aiff" "vo_${key}.wav" && rm -f "vo_${key}.aiff"
  echo "  vo_${key}.wav"
done < narration.txt
echo "$VOICE" > voice-used.txt
echo "Done. Listen with:  afplay vo_title.wav"
