# Evidence

Every number this project states publicly (README, guides, demo, launch post) is listed here with its source. **Pending** means the proof hasn't been captured yet: treat that number as unverified until it's filled in.

Two levels of proof:
- **Provider records** (Anthropic Console billing and usage): the bill itself. Strongest.
- **Hermes' own records** (`state.db` via `h --sessions`, Hermes `/usage`): Hermes' estimates from its built-in price table. Good for comparing sessions with each other. Not a bill.

| # | Claim | Where it's used | Proof | Status |
|---|---|---|---|---|
| 1 | Hermes failed with "You're out of extra usage" (HTTP 400) | Guide §1, post | Error transcript in the guide (request ID kept) | ✓ |
| 2 | claude.ai usage-credit balance was **$0** | Guide §2, post | [`img/01-claude-usage-page-usage-credits-zero.png`](img/01-claude-usage-page-usage-credits-zero.png) | ✓ |
| 3 | Plan includes **$200/month** API credit, linked | Guide §2, post | [`img/02-claude-billing-api-credits-linked.png`](img/02-claude-billing-api-credits-linked.png) | ✓ |
| 4 | The $200 was **untouched** before the fix ($200.00 of $200.00) | Guide §2, post | [`img/04-console-promotional-credits-200.png`](img/04-console-promotional-credits-200.png) | ✓ |
| 5 | After the fix, Hermes spends the **$200 credit** (balance below $200.00) | Guide §3 step 7, post | Console → Billing → Promotional credits, screenshot after use → `evidence/console-credits-after.png` | **Pending** |
| 6 | Per-model usage: routine work ran on **Haiku**, not Opus | README, post | Console → Usage, grouped by model, filtered to the `hermes-local` key → `evidence/console-usage-by-model.png` | **Pending** |
| 7 | 2 questions + **20 tool calls ≈ $0.38** | README, guide §5, post | `h --sessions --csv` row for that session → `evidence/sessions-2026-11-21.csv` | **Pending** (Hermes estimate, quoted from the session footer) |
| 8 | Direct answer, **0 tool calls ≈ $0.02** | README, guide §5, post | Same CSV | **Pending** (Hermes estimate) |
| 9 | Per-task cost lookup raised a trivial answer to **≈ $0.06** | Guide §5, post | Same CSV | **Pending** (Hermes estimate) |
| 10 | Opus 5.5 = 2× Sonnet 5.5; Haiku 5.5 ≈ 40× cheaper than Opus (≤100K tokens) | README, guide §5, post | [Anthropic pricing page](https://platform.claude.com/docs/en/about-claude/pricing), Nov 2026: $4/$20, $2/$10, $0.10/$0.50 per M tokens | ✓ (re-check on price changes) |
| 11 | `h` routed a definition to Haiku; cycle ~$0.90 of $200 | README, post | Terminal transcript in the guide; demo recording | ✓ (budget figure = Hermes estimate) |
| 12 | `h --check`: key valid, all three models listed by the provider | Guide §7 | Terminal transcript; demo step 1 | ✓ |

## How to capture the pending items

```bash
# 7–9: export today's sessions (titles hidden by default; add --titles only if they're safe to publish)
h --sessions 30 --csv > ~/.local/share/hermes-budget-router/docs/evidence/sessions-2026-11-21.csv
```

5: Console → **Billing** → Promotional credits → screenshot the "API credit" row.
6: Console → **Usage** (or Cost) → today, group by model, filter API key `hermes-local` → screenshot.

Then check both screenshots for card numbers, emails and other keys' names, and redact them before committing. The ones in `img/` show how.

**If Console and Hermes disagree:** the Console wins. Update the numbers in the README and post, and note the gap here. It's a finding about Hermes' price table, not a failure.
