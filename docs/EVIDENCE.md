# Evidence

Every number this project states publicly (README, guides, demo, launch post) is listed here with its source. **Pending** means the proof hasn't been captured yet: treat that number as unverified until it's filled in.

Three levels of proof:
- **Provider records** (Anthropic Console billing and usage): the bill itself. Strongest.
- **Independent recomputation** (`h --sessions`, `recomputed_usd` column): token counts from Hermes × Anthropic's published prices. Checks Hermes' arithmetic. Not a bill.
- **Hermes' own records** (`state.db`, Hermes `/usage`): Hermes' estimates from its built-in price table (`cost_status: estimated`; `actual_cost_usd` stays empty). Good for comparing sessions with each other.

| # | Claim | Where it's used | Proof | Status |
|---|---|---|---|---|
| 1 | Hermes failed with "You're out of extra usage" (HTTP 400) | Guide §1, post | Error transcript in the guide (request ID kept) | ✓ |
| 2 | claude.ai usage-credit balance was **$0** | Guide §2, post | [`img/01-claude-usage-page-usage-credits-zero.png`](img/01-claude-usage-page-usage-credits-zero.png) | ✓ |
| 3 | Plan includes **$200/month** API credit, linked | Guide §2, post | [`img/02-claude-billing-api-credits-linked.png`](img/02-claude-billing-api-credits-linked.png) | ✓ |
| 4 | The $200 was **untouched** before the fix ($200.00 of $200.00) | Guide §2, post | [`img/04-console-promotional-credits-200.png`](img/04-console-promotional-credits-200.png) | ✓ |
| 5 | After the fix, Hermes spends the **$200 credit** (balance below $200.00) | Guide §3 step 7, post | Console → Billing → Promotional credits, screenshot after use → `evidence/console-credits-after.png` | **Pending** |
| 6 | Per-model usage: routine work ran on **Haiku**, not Opus | README, post | Console → Usage, grouped by model, filtered to the `hermes-local` key → `evidence/console-usage-by-model.png` | **Pending** |
| 7 | Opus research session: **10 API calls, 12 tool calls → $0.36** | README, guide §5, post | [`evidence/sessions-2026-11-21.csv`](evidence/sessions-2026-11-21.csv), row started 12:30. Recomputed = Hermes estimate | ✓ (corrected from "20 tool calls ≈ $0.38", a footer guess) |
| 8 | One-line answer, no tools: **$0.11 on Opus vs $0.0028 on Haiku** | README, guide §5, post | Same CSV: Opus rows 12:26 / 12:37, Haiku rows 13:09–15:01 | ✓ (corrected from "≈ $0.02", a footer guess) |
| 9 | ~~Per-task cost lookup raised a trivial answer to ≈ $0.06~~ | — | Footer guess. The measured Opus answer with 1 tool call was $0.08 | **Withdrawn** |
| 10 | Opus 5.5 = 2× Sonnet 5.5; Haiku 5.5 ≈ 40× cheaper than Opus (≤100K tokens) | README, guide §5, post | [Anthropic pricing page](https://platform.claude.com/docs/en/about-claude/pricing), Nov 2026: $4/$20, $2/$10, $0.10/$0.50 per M tokens | ✓ (re-check on price changes) |
| 11 | `h` routed a definition to Haiku; cycle ~$0.90 of $200 | README, post | Terminal transcript in the guide; demo recording | ✓ (budget figure = Hermes estimate) |
| 11b | Hermes is using the API key, not subscription OAuth | Guide, post | Hermes `/usage` in the demo: "Anthropic account limits are only available for OAuth-backed Claude accounts" ([still](demo/02-hermes-answer-and-usage.png)) | ✓ |
| 12 | `h --check`: key valid, all three models listed by the provider | Guide §7 | Terminal transcript; demo step 1 | ✓ |
| 13 | Hermes' cost estimate matches published prices | README, post | [Still](demo/03-sessions-proof.png); `h --sessions` shows Hermes' `estimated_cost_usd` next to an independent recomputation (tokens × [published prices](https://platform.claude.com/docs/en/about-claude/pricing)). Three real Haiku sessions on 21 Nov 2026: 4 input + ~130 output + 21,693 cache-write tokens → $0.0028 both ways | ✓ (recomputation, not a bill) |
| 14 | Starting a fresh Hermes session costs ~$0.003 on Haiku vs ~$0.11 on Opus, before any real work | README, post | The same rows: each new session writes ~21.7K tokens of setup (system prompt, tools, skills, SOUL.md) to the prompt cache. 21,693 × $0.125/M (Haiku 5-min cache write) ≈ $0.0027; × $5/M (Opus) ≈ $0.108 | ✓ Opus row 12:26: 20,993 cache-write tokens × $5/M = $0.105 |
| 15 | A session started within 5 minutes of the previous one cost 54% less ($0.0013 vs $0.0028) | README, guide, post | CSV row 15:04: 12,352 cache-read + 9,282 cache-write tokens, against 21,693 cache-write tokens cold | ✓ |

## How to capture the pending items

```bash
# 7–9: export today's sessions (titles hidden by default; add --titles only if they're safe to publish)
h --sessions 30 --csv > ~/.local/share/hermes-budget-router/docs/evidence/sessions-2026-11-21.csv
```

5: Console → **Billing** → Promotional credits → screenshot the "API credit" row.
6: Console → **Usage** (or Cost) → today, group by model, filter API key `hermes-local` → screenshot.

Then check both screenshots for card numbers, emails and other keys' names, and redact them before committing. The ones in `img/` show how.

**If Console and Hermes disagree:** the Console wins. Update the numbers in the README and post, and note the gap here. It's a finding about Hermes' price table, not a failure.

## Known non-evidence

- **The cost line in Hermes' footer is not evidence.** Earlier versions of `soul/cost-policy.md` had the model print `task ~$X.XX`. It guessed: one demo take showed ~$0.01 against a measured $0.0028. The policy no longer prints unmeasured figures. Don't quote footer dollars anywhere.
