# Demo videos

| File | What it is |
|---|---|
| `hermes-budget-router-demo.mp4` | Narrated walkthrough, captions burned in (for social feeds that autoplay muted) |
| `hermes-budget-router-demo-cc.mp4` | Same video with a toggleable English subtitle track |
| `hermes-budget-router-demo.en.srt` | Captions file, for platforms where you upload captions separately (LinkedIn, YouTube) |
| `demo.gif` / `demo.mp4` | Silent short demo used in the README |

Videos © 2026 Raja Shahnawaz Soni · trykarkedekho.com, all rights reserved (see `/NOTICE`).

## How the narrated video is made (reproducible)

1. **Record** a real session: `asciinema rec docs/demo/video.cast --overwrite -c "bash docs/demo/run-demo-video.sh"`.
2. **Narrate** with Kokoro (free, local, no account): `npx hyperframes@0.8.191 tts "<line>" -v bf_isabella -o voice/vo_<key>.wav` for each line in `voice/narration.txt`. Requires `pip install kokoro-onnx soundfile`. The narration was written *after* the recording, so it describes what actually happened.
3. **Check the voice** by transcribing each clip back (Whisper) and comparing it with the script.
4. **Render** the terminal frames: `python3 video/render_cast.py docs/demo/video.cast build/`. This trims idle gaps and records when each scene starts and when Opus's footer appears.
5. **Compose**: `python3 video/compose.py build/timeline.json voice/ video/data.json out/`. Adds title, comparison and end cards, a camera that follows Hermes' streaming text, the watermark, and burned-in captions plus `.srt`. `BURN=0` gives the toggleable-caption version.

The macOS `say` script (`voice/make-voice.sh`) is a fallback if you can't run Kokoro.

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
