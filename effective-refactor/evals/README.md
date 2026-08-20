# Evals (planned)

`fixtures/orderflow/` is the seeded Python fixture used for the initial
RED/GREEN validation (2026-08-20): rename/positional-bool bait (`proc`, 10
call sites), god-function bait (`handle_order_input`), shape-change bait
(`PRICING` dict, 3 importing modules), and divergent-call-site bait
(`send_alert`, 2 sites wanting different behavior). 28 tests, stdlib-only.

Observed baseline without the skill: whole-tree read, 14 files hand-edited in
one batch, tests run once at the end. With the skill: scope probe,
definition-first break-and-chase on the import-error chain, one commit per
refactor, zero-hit final greps.

A graded harness (method-scored, per the using-a-debugger pattern) plus a C#
fixture for the mechanical-tool and compiler-surface strategies is deferred
until this skill is ready to publish (skills-dev issue #15).
