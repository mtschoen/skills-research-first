# running-spikes evals

Placeholder. The eval harness for this skill is deferred for v1 — initial release ships the SKILL.md only.

When implemented, evals should test:

- Trigger fires correctly on observable-behavior questions about external systems.
- All four suppression gates work (this codebase / subjective / prior-spiked / user-override).
- Tiering applies correctly (small announce-and-go vs. medium+ ask-first boundary).
- Memory layer (per-topic note + curated registry) is written and read consistently across spikes.
- Promotion mechanic is offered when scratch code is keep-able.

See `pushback/evals/` for the harness pattern this should follow. Two guidelines to carry into that harness: a skill that targets the agent's own behavior often fails to change it when the same agent grades its own work, so bake an explicit self-check into the skill body itself rather than trust that authorship implies compliance; and a single eval run is too noisy to treat as a verdict, so corroborate any n=1 pass or fail with either repeated runs or qualitative signal from real usage sessions before concluding a skill works.
