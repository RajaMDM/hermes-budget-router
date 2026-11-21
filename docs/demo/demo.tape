# Real, scripted demo of h + Hermes. Records actual output; nothing is mocked.
# Run from the repo root:  vhs docs/demo/demo.tape
# Needs: brew install vhs   (pulls in ttyd + ffmpeg), h on PATH, a working ~/.hermes setup.
# Cost: one real Haiku-tier Hermes session (a few cents at most) plus four tiny classifier calls.

Output docs/demo/demo.gif
Output docs/demo/demo.mp4

Set Shell "bash"
Set FontSize 15
Set Width 1920
Set Height 1080
Set Padding 24
Set Theme "GitHub Dark"
Set TypingSpeed 45ms

# Neutral prompt and folder so no username or home path appears on screen.
Hide
Type `export PATH="$HOME/bin:$PATH" BASH_SILENCE_DEPRECATION_WARNING=1 PS1='$ ' H_PAUSE=2` Enter
Type "mkdir -p /tmp/hermes-demo && cd /tmp/hermes-demo && clear" Enter
Sleep 500ms
Show

# 1. Health check: key present, models exist at the provider.
Type "h --check" Sleep 300ms Enter
Sleep 6s
Screenshot docs/demo/01-check.png
Sleep 1s

# 2. Routing decisions (dry run): quick vs strong.
Type "h -n what is MDM survivorship in one sentence" Sleep 300ms Enter
Sleep 4s
Type "h -n design the target-state architecture for multi-region customer MDM" Sleep 300ms Enter
Sleep 4s
Screenshot docs/demo/02-routing.png
Sleep 1s

# 3. Budget for this credit cycle.
Type "h --budget" Sleep 300ms Enter
Sleep 2s
Type "clear" Enter

# 4. The real thing: route, then Hermes opens with the question already sent.
Type "h what is MDM survivorship in one sentence" Sleep 300ms Enter
Sleep 25s
Screenshot docs/demo/03-hermes-answer.png
Sleep 2s
Type "/exit" Enter
Sleep 4s
Type "clear" Enter

# 5. Routing history.
Type "h --stats" Sleep 300ms Enter
Sleep 3s
Screenshot docs/demo/04-stats.png
Sleep 3s
