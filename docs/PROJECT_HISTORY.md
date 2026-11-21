# Project history

## 21 Nov 2026: from a broken agent to a published fix

**Starting point.** Hermes Agent, a self-hosted AI assistant, failed on every request with "You're out of extra usage", even though the Claude plan behind it includes $200 a month of API credit.

**What we found.** Claude plans keep two separate balances. Tools that sign in with a Claude account draw from a pay-as-you-go balance, which was empty. The included monthly credit is only reachable with an API key from a linked developer organization. Hermes was signing in with the account, so the $200 sat unused.

**What we did.**
1. Created an API key in the organization that receives the monthly credit.
2. Removed two older sign-in credentials that Hermes was choosing ahead of the key.
3. Updated Hermes, six months out of date, so it could talk to current models, and repaired its background service.
4. Confirmed the fix: Hermes answered, and the cost appeared against the $200 credit.

**Then we made it economical.** Background housekeeping moved to the cheapest model. Hermes was given a written cost policy: answer directly, ask before expensive work, offer upgrades with a price, report the cost. A small launcher (`h`) now picks the right model for each task before the session starts and keeps an eye on the monthly budget.

**Why publish.** Many Hermes users hit the same error with no clear explanation. This repo is the fix, with evidence, plus the tooling built on top of it.

## 21 Nov 2026 (later): opened up to everyone

The first version only helped Claude Max subscribers. But the underlying lessons apply to anyone running an AI agent: pick the model before the conversation, keep the agent from researching things it already knows, and put limits on background work. So the launcher now works with any provider Hermes supports. Each tier can come from a different company, or run locally on your own computer for free. There are ready-made setups for ChatGPT plans, Grok plans, Gemini's free tier, pay-as-you-go keys and fully local models. The project was renamed **hermes-budget-router** to match.
