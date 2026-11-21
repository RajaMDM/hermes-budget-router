#!/usr/bin/env bash
# Real demo of h + Hermes for recording with asciinema. Every command below really runs;
# the "typing" is only a display effect so viewers can follow. Nothing is mocked.
#
#   brew install asciinema agg
#   cd ~/.local/share/hermes-budget-router
#   asciinema rec docs/demo/demo.cast --overwrite -c "bash docs/demo/run-demo.sh"
#   agg docs/demo/demo.cast docs/demo/demo.gif
#
# When Hermes has answered in step 4, type /usage (Hermes' own token + cost breakdown for the
# session), then /exit. The script then continues and shows the session in Hermes' database.
set -u
export PATH="$HOME/bin:$PATH" H_PAUSE=2
mkdir -p /tmp/hermes-demo && cd /tmp/hermes-demo || exit 1

type_cmd() {  # print "$ <command>" one character at a time, then run it
  printf '\033[1;32m$\033[0m '
  local s="$*" i
  for (( i=0; i<${#s}; i++ )); do printf '%s' "${s:i:1}"; sleep 0.035; done
  printf '\n'; sleep 0.4
  eval "$s"
}
pause() { sleep "${1:-2}"; }
note() { printf '\n\033[2m# %s\033[0m\n' "$*"; pause 1.2; }

clear
note "1. Health check: key present, models exist at the provider"
type_cmd h --check; pause 3

note "2. Routing decisions (dry run)"
type_cmd h -n what is MDM survivorship in one sentence; pause 2
type_cmd h -n design the target-state architecture for multi-region customer MDM; pause 3

note "3. This credit cycle's budget"
type_cmd h --budget; pause 3

clear
note "4. The real thing: route, then Hermes opens with the question already sent (then /usage, /exit)"
type_cmd h what is MDM survivorship in one sentence

clear
note "5. Proof: tokens, tool calls and estimated cost of the sessions just run (from Hermes' own database)"
type_cmd h --sessions 3; pause 5

note "6. Routing history"
type_cmd h --stats; pause 4
