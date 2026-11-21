# Changelog

## 0.2.0, 21 Nov 2026
- **Launcher `h`:** budget-aware routing (reads cycle spend from `state.db` and tells the classifier when budget is tight or credit is about to expire). Routing log and `--stats`. `--budget`. Dry run `-n`. `--eval`/`--score` for measuring routing accuracy. Model IDs, budget and cycle day configurable via env. Linux clipboard support. `H_FIRST_MESSAGE_FLAG` to skip the paste step. Decision held on screen for `H_PAUSE` seconds. 20 unit tests.
  *Impact:* routing can be measured and tuned, and adapts to remaining budget.
- **Guide:** full fix walkthrough with redacted screenshots, troubleshooting table, cost section.
- **Scripts:** `aux-to-haiku.sh` with backup and line-count safety check.

## 0.1.0, 21 Nov 2026
- First working setup: Hermes on monthly API credits. Cost policy in SOUL.md. Basic `h` launcher (classify → launch).
  *Impact:* $200/month credit went from unused to in use. A trivial question cost ~$0.02 instead of a ~$0.38 research loop.
