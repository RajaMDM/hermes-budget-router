# Changelog

## 0.3.2, 21 Nov 2026
- **Offline fallback errs towards adequate, not cheapest.** When the classifier call fails, plan, diagnose, strategy, draft, steps and similar requests now go to the standard tier, where before any request under 25 words went to the quick tier. Found when a classifier hiccup sent a "30-day fix plan" request to Haiku.

## 0.3.1, 21 Nov 2026
- **Router rubric tuned:** plans and advice drawn from general knowledge now go to the **standard** tier. **Strong** is for real stakes, the user's specific context, architecture, hard debugging and novel problems. Evidence: the "team missing deadlines" question cost $0.1389 on Opus and $0.0682 on Sonnet with comparable usefulness ([EVIDENCE](EVIDENCE.md) #18).
- **Cost policy:** the footer no longer suggests a cheaper tier. Opus suggested Sonnet and Sonnet suggested Haiku on the same question, so the signal is biased (#19).

## 0.3.0 (launch assets), 21 Nov 2026
- **Narrated demo video** (1:42): simple vs complex question, real recording, Kokoro voice "Isabella", captions burned in plus a toggleable track and `.srt`, © trykarkedekho.com watermark. Reproducible pipeline in `docs/demo/video/`.
- **About Hermes Agent** section with attribution to Nous Research. Credits for Kokoro, HyperFrames, asciinema. `NOTICE` keeps the videos all-rights-reserved while the code stays MIT.

## 0.3.0 (evidence update), 21 Nov 2026
- `h --sessions [N] [--csv] [--schema]`: per-session tokens, cache use, tool calls, Hermes' estimate, and an **independent recomputation from published prices**. Exact column whitelist, so prompts, IDs and JSON never print.
- `docs/EVIDENCE.md`: every public number mapped to its proof.
- **Corrections:** "direct Opus answer ≈ $0.02" → measured **$0.11**; "20 tool calls ≈ $0.38" → **12 tool calls, $0.36**; "$0.06" withdrawn. All three were the model guessing its own cost in the footer. The cost policy no longer prints unmeasured figures.
- Real demo recording (asciinema) with `/usage` and the sessions table as on-screen proof.

## 0.3.0, 21 Nov 2026
- **Any provider:** each tier is a `(provider, model)` pair in `~/.hermes/h.json`. Classifier adapters for the Anthropic Messages API and any OpenAI-compatible API (OpenAI, Gemini, xAI, OpenRouter, DeepSeek, local Ollama). Subscription sign-ins (ChatGPT, SuperGrok, Copilot) are supported launch-only.
- **10 presets:** claude-credits (tested), claude-paygo, openai-api, gemini-api, gemini-free, xai, openrouter, local-ollama, mixed-budget, chatgpt-plan.
- **`h --init` / `--presets` / `--check`.** `--check` verifies each key and asks the provider whether the model ID exists, because model line-ups change monthly.
- **Docs restructured:** overview README, Claude guide, and an "other setups" guide for Pro/Free/ChatGPT/Grok/free/local users. Repo renamed from hermes-claude-credits to hermes-budget-router.
- `aux-to-haiku.sh` → `aux-to-cheap.sh [provider] [model]`.
- **One-step launch:** the task is passed with `hermes chat -q`, which seeds an interactive session on Hermes v0.23+. No more pasting. `H_FIRST_MESSAGE_FLAG=clipboard` keeps the old behaviour for older builds.
- **Per-tier `reasoning`** (`none`…`ultra`) → `hermes chat --reasoning`.
- 32 unit tests, including HTTP adapters with mocks.
  *Impact:* useful to anyone running Hermes, not only Claude Max subscribers. Zero-budget and local paths are documented.

## 0.2.0, 21 Nov 2026
- **Launcher `h`:** budget-aware routing (reads cycle spend from `state.db` and tells the classifier when budget is tight or credit is about to expire). Routing log and `--stats`. `--budget`. Dry run `-n`. `--eval`/`--score` for measuring routing accuracy. Model IDs, budget and cycle day configurable via env. Linux clipboard support. `H_FIRST_MESSAGE_FLAG` to skip the paste step. Decision held on screen for `H_PAUSE` seconds. 20 unit tests.
  *Impact:* routing can be measured and tuned, and adapts to remaining budget.
- **Guide:** full fix walkthrough with redacted screenshots, troubleshooting table, cost section.
- **Scripts:** `aux-to-haiku.sh` with backup and line-count safety check.

## 0.1.0, 21 Nov 2026
- First working setup: Hermes on monthly API credits. Cost policy in SOUL.md. Basic `h` launcher (classify → launch).
  *Impact:* $200/month credit went from unused to in use.
