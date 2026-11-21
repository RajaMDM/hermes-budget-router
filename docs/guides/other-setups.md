# Guide: Hermes without a Claude Max plan

Claude Max/Ultra/Team users get a monthly API credit ([guide](claude-api-credits.md)). Everyone else has other routes. Here's what each one costs, what it needs, and what to watch out for.

> **Status:** these paths use Hermes' documented providers (Nov 2026) but **haven't been tested end to end** like the Claude path. Run `h --check` after setting one up, and please open an issue with what worked.

## Quick comparison

| Route | Hermes provider | Auth | Cost | Watch out for |
|---|---|---|---|---|
| Claude pay-as-you-go | `anthropic` | `ANTHROPIC_API_KEY` | Per token | Set a spend limit in the Claude Console |
| OpenAI API | `openai-api` | `OPENAI_API_KEY` | Per token | Model names change often |
| ChatGPT plan | `openai-codex` | ChatGPT sign-in | Inside your plan | Hermes doesn't document plan limits |
| Gemini API (paid) | `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Per token | Some prices double from Dec 1, 2026 |
| Gemini API (free tier) | `gemini` | same key | $0 | Rate limits. Only some models. Content may be used to improve Google's products |
| xAI Grok API | `xai` | `XAI_API_KEY` | Per token | Models retired frequently |
| SuperGrok / X Premium+ | `xai-oauth` | Browser sign-in | Inside your plan | HTTP 403 if your tier isn't entitled |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | Per token, one bill for many vendors | You choose model slugs yourself |
| GitHub Copilot | `copilot` | Labs plugin sign-in | Inside your plan | Plugin is labs-grade |
| Local (Ollama) | `custom` | none | $0 (your hardware) | Quality depends on your machine |

Provider IDs and auth come from Hermes' [providers page](https://hermes-agent.nousresearch.com/docs/integrations/providers).

---

## Claude Pro or Free

Hermes' docs say Claude **Pro can't use the subscription sign-in path**. Even where sign-in works, third-party apps bill pay-as-you-go "extra usage" rather than your plan. The clean route is an API key:

1. Create a key at platform.claude.com → API keys → **Somewhere else** → Scope: **Default workspace** (screenshots in the [Claude guide](claude-api-credits.md#step-2-create-an-api-key-in-the-linked-org)).
2. Add prepaid credit and **set a monthly spend limit** in the Console. That limit is your real safety net.
3. Steps 3–7 of the [Claude guide](claude-api-credits.md#step-3-give-the-key-to-hermes) apply unchanged: add the key, remove OAuth credentials, update Hermes.
4. `h --init claude-paygo`, then set `budget_usd` in `~/.hermes/h.json` to your own monthly target.

**Cost tip:** with pay-as-you-go, `h` matters most. Haiku-class models cost a small fraction of Opus-class ones, and most day-to-day questions don't need the strong tier.

## ChatGPT plan

```bash
hermes model               # choose OpenAI Codex, sign in with ChatGPT
h --init chatgpt-plan      # then set the model IDs in ~/.hermes/h.json
```

- Usage comes out of your ChatGPT plan, not a per-token bill. Hermes doesn't document how plan limits apply, so watch your plan's usage page during the first week.
- h can't run its classifier through a subscription sign-in, so it falls back to keyword rules. For smarter routing, make one tier an API-key provider (e.g. Gemini free tier as `classifier_tier`).

## SuperGrok or X Premium+

```bash
hermes auth add xai-oauth  # browser sign-in
```

Then use `provider: "xai-oauth"` in your h config. Hermes warns that requests can return HTTP 403 if your tier isn't entitled. That's a plan restriction, not a bug. Classification works the same way as for the ChatGPT plan above.

## Pay-as-you-go API keys

```bash
# pick one; the key goes in ~/.hermes/.env
OPENAI_API_KEY=...    →  h --init openai-api
GEMINI_API_KEY=...    →  h --init gemini-api
XAI_API_KEY=...       →  h --init xai
OPENROUTER_API_KEY=...→  h --init openrouter   (fill in model slugs)
h --check
```

For every provider: **set a hard spend limit in its own billing console.** h's budget is an early-warning system based on Hermes' estimates. It isn't a cap.

## Zero budget

**Option A: Gemini API free tier.** Create a key in Google AI Studio, add `GEMINI_API_KEY` to `~/.hermes/.env`, then `h --init gemini-free`. Limits: rate-limited, only some models are free, and Google's pricing page says free-tier content is used to improve its products. **Don't send confidential or work data.**

**Option B: fully local with Ollama.** Install Ollama, pull a few models of different sizes, point Hermes at the custom endpoint (`hermes model` → custom, base URL `http://localhost:11434/v1`), then `h --init local-ollama` and fill in the model tags from `ollama list`. It's private and free, but quality and speed depend on your hardware.

**Option C: both.** `h --init mixed-budget` sends quick tasks to local models, routine tasks to free Gemini, and only hard tasks to a paid model with a small budget, e.g. $20 a month.

Other free or credit-based options listed by Hermes: Hugging Face (`huggingface`, free tier with monthly credit) and NVIDIA Build (`nvidia`, free API key). Point a tier at them using their provider ID.

## Make background tasks cheap too

Whatever your provider, move Hermes' routine background work to your cheapest model:

```bash
bash scripts/aux-to-cheap.sh gemini gemini-3.5-flash
bash scripts/aux-to-cheap.sh anthropic claude-haiku-5-5
```

And add the [cost policy](../../soul/cost-policy.md) to `SOUL.md`. Change the `$200` and dates to match your budget.
