# Defence brief

**Why an API key instead of signing in with the Claude account?**
The included monthly API credit is only reachable with an API key. Signing in bills a separate pay-as-you-go balance, and Anthropic's guidance is not to use subscription sign-in in third-party tools. Alternatives rejected: buying usage credits (pays twice for capacity already included); routing through `claude -p` (policy grey zone).

**Why route per session rather than per message?**
Each model keeps its own prompt cache, so switching models mid-conversation re-pays the full context. Per-message routing through a proxy would often cost more than it saves. Rejected: a request-level proxy router.

**Why a small Haiku classifier rather than rules only?**
Rules can't tell "explain X" (cheap) from "explain the trade-offs of X for our architecture" (expensive). A one-call Haiku judgment costs a fraction of a cent. Rules stay as the offline fallback, so routing never blocks.

**Why tell the classifier about budget instead of forcing downgrades?**
Silent downgrades degrade quality without the user knowing. The budget signal shifts borderline calls only, and the user can always force a tier with `-q/-s/-o`.

**Why a prompt-level cost policy (SOUL.md) and not hard enforcement?**
Hermes has no per-call spend controls. The prompt shapes behaviour (fewer tool calls, priced upgrade offers). The hard limit is billing: no card on the Console org, so spend stops at the credit.

**Why Haiku for background tasks but not for `approval`?**
Compression, titles, memory filing and search are mechanical. Approving shell commands is a safety judgment, so it stays on the strong model.

**Why the budget figures are labelled "estimate".**
They come from Hermes' own price table. The authoritative balance needs an admin key, which we deliberately don't give to an agent.
