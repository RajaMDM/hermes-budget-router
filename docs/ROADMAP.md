# Roadmap

## Next
- **Field-test non-Claude presets.** Collect `h --check` results from users on OpenAI, Gemini, xAI and local setups. Promote each preset from UNTESTED once confirmed.
- **Measure routing accuracy.** Label 30+ real tasks with `--eval`/`--score` and publish the number in the README.
- **Confirm auth style** for `sk-ant-usr` keys and drop the unused fallback.
- **Validate budget estimates** against the Console for a full cycle.

## Later
- Map tiers to sensible default `reasoning` levels once costs are measured per level.
- Optional escalation: if a Haiku/Sonnet session's footer says "next time: h -o", offer to relaunch with the same task.
- Read the expiry date from config instead of editing SOUL.md monthly.
- Package as a Hermes plugin if Hermes adds a pre-session hook.

## Triggers
- A preset's models fail `h --check` → update the preset and bump the patch version.
- Budget regularly over pace → make Sonnet the default tier for unclear tasks.
- Hermes adds native model routing → retire the classifier and keep budget tracking.
