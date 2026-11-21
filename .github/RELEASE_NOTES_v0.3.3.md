## hermes-budget-router v0.3.3: first public release

Pick the right AI model **before** each Hermes session, track your monthly budget, and prove what every answer cost.

### What you get
- **`h` launcher.** A tiny classifier call routes each task to a quick, standard or strong tier, then opens Hermes with your task already sent. If the classifier fails, it falls back to keyword rules.
- **Budget-aware.** Reads your cycle spend from Hermes' own database. It tightens when you're on pace to overspend, and leans stronger when unused credit is about to expire.
- **Any provider, mixed tiers.** Claude, OpenAI, Gemini, Grok, OpenRouter, DeepSeek or local Ollama, plus launch-only support for ChatGPT, SuperGrok and Copilot sign-ins. 10 presets, including a **$0 setup**.
- **Proof, not promises.** `h --sessions` shows each session's tokens and Hermes' cost estimate next to an **independent recalculation from published prices**. `h --check` asks each provider whether your model IDs exist.
- **Guides.** Fix "You're out of extra usage" and run Hermes on Claude Max/Ultra API credits (with screenshots), setups for everyone else, and a quickstart for people new to Hermes.
- **Narrated demo (1:38)** with captions: the same agent answered a simple question on Haiku for $0.0027 and a complex one on Opus for $0.1389.

### Measured, then fixed (v0.3.1 to v0.3.3)
- The demo's "team missing deadlines" question cost $0.14 on Opus. On Sonnet it cost $0.07 and was about as useful, so general-knowledge plans now route to the standard tier. Verified: 3 of 3 runs to Sonnet, while a high-stakes migration decision still goes to Opus.
- Models' "use a cheaper tier next time" remarks proved biased (each suggested the tier below itself), so they're no longer requested.
- The classifier's reply budget was raised (60 → 400 tokens) after harder tasks returned empty replies. The offline fallback now errs towards adequate rather than cheapest.

Every number is sourced in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

### Status
The Claude-credits path is tested end to end. Other presets are **untested**: please file a *Setup report* issue.

### Install
```bash
git clone https://github.com/RajaMDM/hermes-budget-router ~/.local/share/hermes-budget-router
mkdir -p ~/bin && ln -sf ~/.local/share/hermes-budget-router/bin/h ~/bin/h
h --presets && h --init <preset> && h --check
```

Add-on for [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research (MIT). Not affiliated with Nous Research or Anthropic.
