# running-spikes evals

Placeholder. The eval harness for this skill is deferred for v1 — initial release ships the SKILL.md only.

When implemented, evals should test:

- Trigger fires correctly on observable-behavior questions about external systems.
- All four suppression gates work (this codebase / subjective / prior-spiked / user-override).
- Tiering applies correctly (small announce-and-go vs. medium+ ask-first boundary).
- Memory layer (per-topic note + curated registry) is written and read consistently across spikes.
- Promotion mechanic is offered when scratch code is keep-able.

See `pushback/evals/` for the harness pattern this should follow. Behavioral skills sometimes don't apply to the agent that authored them (see `feedback_skill_self_application.md` in cross-project memory) — qualitative real-session testing matters more than n=1 eval runs (see `feedback_no_iteration_on_n1.md`).
