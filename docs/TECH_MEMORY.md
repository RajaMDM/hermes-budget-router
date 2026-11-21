# Tech memory

## Root cause
- `You're out of extra usage` (400) = Hermes authenticating with **subscription OAuth**, which bills claude.ai usage credits (balance $0). Monthly API credits for Max/Ultra/Team are only reachable with a Console **API key** from the org linked on claude.ai → Settings → Billing.
- Hermes picks the first usable credential in its pool. Ours had `ANTHROPIC_TOKEN` (env, OAuth) and a borrowed `claude_code` login ahead of `ANTHROPIC_API_KEY`.

## Fixes that worked (Hermes v0.23.3, macOS)
- Comment out `ANTHROPIC_TOKEN` in `~/.hermes/.env`. `hermes auth remove anthropic <index>` for `claude_code` (provider argument is required). `auth.adopt_external_logins: false`.
- `"thinking.type.enabled" not supported` → Hermes too old (v0.14). `hermes update`. Its "Up to date" message was wrong.
- `service_identity_unverified` after update → `hermes gateway uninstall && install && start`.

## Gotchas
- `~/.hermes/.env` had an empty `ANTHROPIC_API_KEY=` placeholder. Two entries = ambiguous. Delete the empty one.
- macOS `nano` may be `pico`, with different shortcuts. Use `cat >>` to append secrets without shell history.
- macOS `sed -i` needs `''`.
- Console key **Scope: Organization** requires an `anthropic-workspace-id` header. Use the Default workspace.
- `sk-ant-usr…` keys show as type `oauth` in `hermes auth list`, yet worked.
- `uv` warning on `exclude-newer = "3 days"`: old uv. Non-fatal for us.
- Web UI npm install failed (likely Node version). CLI unaffected.
- Changing model mid-session discards the prompt cache. Route per session, not per message.
- SOUL.md is sent on every call. Keep the cost policy short.
- A per-task sqlite lookup in the footer tripled the cost of a trivial question (~$0.02 → ~$0.06). Now it runs every 5th task.

## Launcher (`bin/h`)
- Classifier: Haiku, JSON reply `{"tier","reason"}`. Heuristic fallback on any failure.
- Auth: tries `x-api-key`, then `Bearer`. Unconfirmed which one `sk-ant-usr` keys need.
- Budget: `state.db` → `sessions.estimated_cost_usd`. Timestamp column auto-detected (`started_at`, `created_at`, …). Epoch seconds/ms or ISO. Hermes' estimates, not the Console balance.
- Cycle anchored on `H_CYCLE_DAY` (default 10). Real expiry observed 3 days after the next grant (Nov 10 grant → Dec 13 expiry).
