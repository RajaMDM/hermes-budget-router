# Recording the demo

The demo is a **real run**: real classifier calls and a real Hermes session. The script only adds a typing effect so viewers can follow along.

## Recommended: asciinema + agg

Records your actual terminal. No browser or local server involved.

```bash
brew install asciinema agg
cd ~/.local/share/hermes-budget-router
asciinema rec docs/demo/demo.cast --overwrite -c "bash docs/demo/run-demo.sh"
#  → when Hermes answers in step 4, type /exit and press Enter; the script finishes on its own
agg docs/demo/demo.cast docs/demo/demo.gif
open docs/demo/demo.gif
```

Make the terminal window **wide** (the Hermes banner is about 210 columns) before recording. The recording keeps the window size.

## Alternative: VHS (`demo.tape`)

Fully scripted, but it needs `ttyd` to accept IPv6 connections on `localhost`. Homebrew's ttyd 1.7.7 on macOS may be built with `IPV6-off`, which makes VHS fail with `could not open ttyd: … ERR_CONNECTION_REFUSED`. Check it with `curl -sI "http://[::1]:7681"` while `ttyd --port 7681 bash` runs: no output means IPv6 is off, so use asciinema instead.

## Before committing

Watch the GIF and check it for anything you don't want public. The demo runs in `/tmp/hermes-demo`, so your home path doesn't appear. But the Hermes banner lists your installed skills, and an answer can draw on your Hermes memory.

**Cost:** one quick-tier Hermes session plus four tiny classifier calls, a few cents at most.
