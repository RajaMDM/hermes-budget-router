# Roadmap

## Next
- **Remove the paste step.** Confirm whether `hermes chat` accepts an initial message (`hermes chat --help`). If it does, set `H_FIRST_MESSAGE_FLAG` as the documented default.
- **Measure routing accuracy.** Label 30+ real tasks with `--eval`/`--score` and publish the number in the README.
- **Confirm auth style** for `sk-ant-usr` keys and drop the unused fallback.
- **Validate budget estimates** against the Console for a full cycle.

## Later
- Optional escalation: if a Haiku/Sonnet session's footer says "next time: h -o", offer to relaunch with the same task.
- Read the expiry date from config instead of editing SOUL.md monthly.
- Package as a Hermes plugin if Hermes adds a pre-session hook.

## Triggers
- Budget regularly over pace → make Sonnet the default tier for unclear tasks.
- Hermes adds native model routing → retire the classifier and keep budget tracking.
