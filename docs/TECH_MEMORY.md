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
- ~~Footer sqlite lookup tripled cost (~$0.02 → ~$0.06)~~: both numbers were model guesses. Measured: Opus 0-tool answer $0.11, 1-tool $0.08. Session setup dominates, not the lookup.

## Launcher (`bin/h`)
- Classifier: Haiku, JSON reply `{"tier","reason"}`. Heuristic fallback on any failure.
- Auth: tries `x-api-key`, then `Bearer`. Unconfirmed which one `sk-ant-usr` keys need.
- Budget: `state.db` → `sessions.estimated_cost_usd`. Timestamp column auto-detected (`started_at`, `created_at`, …). Epoch seconds/ms or ISO. Hermes' estimates, not the Console balance.
- Cycle anchored on `H_CYCLE_DAY` (default 10). Real expiry observed 3 days after the next grant (Nov 10 grant → Dec 13 expiry).

## v0.3 multi-provider design
- Config `~/.hermes/h.json` (or `$H_CONFIG`). Missing file → built-in claude-credits default, so existing installs keep working.
- `ENDPOINTS` maps Hermes provider IDs to `{api: anthropic|openai, base_url, key_env[]}`. Gemini uses its OpenAI-compatible base `…/v1beta/openai`. Model IDs listed there may carry a `models/` prefix, which is stripped.
- Classifier target = configured tier, else any tier whose provider has an endpoint and a key. Local `custom` needs no key, so it counts as reachable even if Ollama is down. The heuristic then catches it.
- Placeholders containing `REPLACE` are rejected at load time, so unfinished presets fail loudly instead of launching a bad model.
- Presets are found next to the script (`bin/../presets`), with symlinks resolved. A curl-only install of `bin/h` won't see presets. Use git clone plus a symlink.
- Python 3.9+ (`str.removeprefix`).

- Hermes v0.23 `hermes chat -q QUERY`: on a real TTY it seeds an interactive session (the first turn, submitted literally). With `--oneshot`/`-Q` or on a non-TTY it answers and exits. `--query-file` exists for text that mustn't be shell-interpreted, but h uses `execvp`, so there's no shell and `-q` is safe.
- `hermes chat --reasoning LEVEL` (none…ultra) overrides `agent.reasoning_effort` per run.

## Field results (21 Nov 2026, macOS, Hermes v0.23.3)
- `h --check`: key + haiku/sonnet/opus 5.5 all listed via GET /v1/models. The `sk-ant-usr` key works for /models.
- `read_budget` works on the real state.db: cycle ~$0.90, pace ~$2.
- `-q` launch confirmed: question sent as the first turn, session stays interactive.
- Quality caveat: Haiku took "survivorship" literally (survivorship bias). Opus had inferred MDM from context. Domain words matter more on cheap tiers.
- SOUL footer bug: with the old wording the model dropped the task cost when printing "cycle: ask". Reworded.

## Hermes state.db `sessions` (v0.23, 72 columns)
- Useful: started_at, model, message_count, api_call_count, tool_call_count, input/output/cache_read/cache_write/reasoning_tokens, estimated_cost_usd, actual_cost_usd (empty), cost_status ('estimated'), cost_source ('provider_models_api').
- Never print: model_config / prompt_cache_clock (JSON), system_prompt, user_id, chat_id, cwd, git_*, title (opt-in only).
- `h --sessions` uses an exact whitelist. The first version matched substrings ("id" matched "hidden"), which dumped JSON and a text `cost_*` column, and crashed the total.
- Finding: each new session writes ~21.7K tokens to the cache before the first answer. On Haiku 5.5, 21,693 × $0.125/M + 4 × $0.10/M + 131 × $0.50/M = $0.0028, matching Hermes' estimate exactly.
- The SOUL footer's "task ~$X.XX" was the model guessing. On camera it said ~$0.01 when state.db (and the recomputation) said $0.0028. The model can't see its own cost without a tool call. Footer v3 drops unmeasured dollar figures. Cost comes from `h --sessions` or an on-request state.db query.
- Hermes `/usage` shows tokens but not cost for API-key sessions, and reports "Anthropic account limits are only available for OAuth-backed Claude accounts". That confirms the session uses the API key, not OAuth.

## Routing calibration (21 Nov 2026)
- Same question ("12-person team missing deadlines, 30-day plan"): Opus $0.1389, Sonnet $0.0682. Sonnet was ~90% as useful. Opus's edge was judgement (realistic 4–6-week horizon, escalate when the problem is scope/staffing). Rubric v2 moves general-knowledge plans to standard.
- Model self-assessment is biased downward: Opus → "h -s", Sonnet → "h -q" on the same task. Never tune routing from footers. Use `h --eval` labels.
- The video still shows the v1 rubric picking Opus for that question. That's accurate for when it was recorded, and the narration says Opus judged a cheaper model enough, which the Sonnet test confirmed.
