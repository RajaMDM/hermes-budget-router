## hermes-budget-router v0.3.0: first public release

Pick the right AI model **before** each Hermes session, keep an eye on your monthly budget, and stop paying for capacity you already own.

### Highlights
- **`h` launcher.** One tiny classifier call routes each task to a quick, standard or strong tier, then launches Hermes on it. It falls back to keyword rules offline.
- **Budget-aware.** Reads your cycle spend from Hermes' own database, tightens up when you're on pace to overspend, and leans stronger when unused credit is about to expire.
- **Any provider, mixed tiers.** Claude, OpenAI, Gemini, Grok, OpenRouter, DeepSeek, local Ollama, plus launch-only support for ChatGPT, SuperGrok and Copilot sign-ins.
- **10 presets** including a **$0 setup** (Gemini free tier and/or local models).
- **`h --check`** asks each provider whether your model IDs actually exist.
- **`h --eval` / `--score`** measure routing accuracy against your own labels.
- **Guides:** fix "You're out of extra usage" and run Hermes on Claude Max/Ultra API credits (with screenshots), plus setups for everyone else.

### Status
Claude-credits path tested end to end. Other presets are **UNTESTED**: please file a *Setup report* issue.

### Install
```bash
git clone https://github.com/RajaMDM/hermes-budget-router ~/.local/share/hermes-budget-router
mkdir -p ~/bin && ln -sf ~/.local/share/hermes-budget-router/bin/h ~/bin/h
h --presets && h --init <preset> && h --check
```
