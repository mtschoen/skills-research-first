# effective-refactor

Agent skill: how to execute refactors by traversing the reference graph with
tools and error surfaces instead of hand-editing call sites.

Origin: skills-dev issue #15. Core theses: (1) use mechanical refactoring
tools for mechanical operations; (2) "lean on the compiler" - break the
definition and chase the error surface; (3) recognize when a change is not a
refactor and needs a migration plan (Mikado / strangler fig).

## Status

Draft, deliberately light on evals (per issue #15, this skill evolves
organically before the publish-grade eval pass).

Validation so far (2026-08-20):

- RED baseline: one sonnet subject, no skill, on the `orderflow` fixture
  (small Python library with rename / god-function / shape-change / divergent
  call-site bait). Observed method: read the entire tree up front, hand-edited
  14 files in one batch, no mechanical tooling or error surface considered,
  tests run only once at the end. Result correct at toy scale; method does not
  scale.
- GREEN: one sonnet subject with the skill, same fixture and task, to confirm
  the skill changes the method (scope probe, break-and-chase, per-refactor
  checkpoints).

## Planned (pre-publish)

- Eval harness under `evals/` following the using-a-debugger pattern: fixture
  repos per scenario, graded on method (tool use, checkpoint discipline,
  old-name sweep) not just on green tests.
- Pressure scenarios for the discipline rules (batching, red-tree pushing).
- A C# fixture so Strategy 1 and the compiler surface get exercised for real,
  not just described.
