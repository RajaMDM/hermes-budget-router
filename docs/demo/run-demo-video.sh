#!/usr/bin/env bash
# Real two-question demo for the narrated video: a simple question and a complex one, then the
# measured cost of both. Every command really runs; the "typing" is only a display effect.
#
#   cd ~/.local/share/hermes-budget-router
#   asciinema rec docs/demo/video.cast --overwrite -c "bash docs/demo/run-demo-video.sh"
#
# Your part: when Hermes finishes each answer, type /usage, press Enter, then type /exit.
# Cost: one quick-tier session (under a cent) plus one session on whatever tier the router picks
# for the complex question (typically $0.15-$0.50 on Opus).
set -u
export PATH="$HOME/bin:$PATH" H_PAUSE=2
mkdir -p /tmp/hermes-demo && cd /tmp/hermes-demo || exit 1

type_cmd() {
  printf '\033[1;32m$\033[0m '
  local s="$*" i
  for (( i=0; i<${#s}; i++ )); do printf '%s' "${s:i:1}"; sleep 0.03; done
  printf '\n'; sleep 0.4
  eval "$s"
}
pause() { sleep "${1:-2}"; }
note() { printf '\n\033[2m# %s\033[0m\n' "$*"; pause 1.2; }

clear
note "1. Health check"
type_cmd h --check; pause 3

clear
note "2. A simple question"
type_cmd h what is compound interest in one sentence

clear
note "3. A complex question"
type_cmd h my 12-person team keeps missing deadlines. diagnose the 3 most likely causes and give me a 30-day fix plan

clear
note "4. What each answer cost, from Hermes' own records"
type_cmd h --sessions 2; pause 6
