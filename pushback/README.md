# pushback

A skill that turns the agent into a courteous, graduated challenger: when a user request carries a concrete, verified risk, push back before complying - light first, stronger if the user insists tentatively, conceding and executing carefully once they insist firmly. Not a veto, and not a pest - most invocations correctly end in "no pushback needed."

## When it fires

On every user request that proposes work, changes direction, or makes a technical claim - code changes, features, refactors, pivots, "while you're in there" asks, choice of approach, statements about how the code works.

## What it does

Places the request into one of four buckets (wrong timing, wrong direction, wrong information, wrong cost/risk) backed by verified evidence - a real file, grep hit, git fact, or cost - then runs the tick-tock escalation across turns. A configurable safe word (default `override`) short-circuits the debate straight to "concede + plan."

The authoritative spec is [`SKILL.md`](SKILL.md).

**Repo:** <https://github.com/mtschoen/skills-pushback>
