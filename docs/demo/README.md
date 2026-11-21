# Recording the demo

The demo is a **real run**, scripted with [VHS](https://github.com/charmbracelet/vhs) so anyone can reproduce it. Nothing is mocked: it calls the real classifier and opens a real Hermes session.

```bash
brew install vhs                     # also installs ttyd and ffmpeg
cd ~/.local/share/hermes-budget-router
vhs docs/demo/demo.tape              # about 1 minute; writes demo.gif, demo.mp4 and 4 screenshots here
open docs/demo/demo.gif              # watch it before committing
```

**Before committing, check the screenshots** for anything you don't want public. The script uses a neutral prompt and `/tmp/hermes-demo` so your username and home path don't appear, but the Hermes banner lists your installed skills, and an answer can mention things from your Hermes memory.

**Timing:** if Hermes hasn't finished answering when `03-hermes-answer.png` is captured, raise the `Sleep 25s` before it.

**Cost:** one Haiku-tier Hermes session plus four tiny classifier calls, a few cents at most.
