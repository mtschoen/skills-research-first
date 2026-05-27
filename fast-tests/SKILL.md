---
name: fast-tests
description: "Use when the agent observes slow test runs in this session (multi-minute wall clock, repeated re-runs blocking iteration, tests dominating the inner loop) OR when adding tests likely to slow the loop down (integration tests, sleeps/timeouts, external services, fixture-heavy setup). Steers toward fast integration-test loops by speeding up SETUP — never by replacing integration tests with unit mocks that fake the verify. Project-agnostic; per-language references for Python, JVM, .NET."
---

# Fast Tests

Integration tests are the authoritative signal — they verify the product works.
If they're slow, the answer is to **speed up the setup**, not to replace them with unit-level mocks that pretend to verify behavior.
The bias toward unit testing assumes unit correctness implies system correctness; in practice the interesting bugs live at integration boundaries (DPI mismatches, launcher indirection, codec queues, protocol drift).
None of those show up in unit tests.
This skill reinforces that bias and gives the agent techniques to make integration tests cheap enough that they ARE the fast path.

## When to use

- You're in a session and the test run wall clock is multi-minute — every fix-and-rerun cycle is blocked by waiting.
- Repeated re-runs are dominating the inner loop: you fix one thing, re-run, wait, fix another, re-run, wait.
- You are about to add tests that carry the slow-loop risk shape:
  - Integration tests spinning up real services, databases, or browsers
  - Tests with explicit `sleep()` or timeout-driven assertions
  - Tests that hit external services or require network access
  - Tests with heavy fixture setup (schema migrations, large datasets, full app wiring)

If the test loop is fast and you're not adding anything likely to break that, don't invoke this skill — just test.

## When NOT to use

This skill is about the inner loop only. Explicit scope boundaries:

- **Test correctness** — whether to write a test, what to test, or how to structure assertions:
  that's `superpowers:test-driven-development`.
- **Test coverage** — whether every line is covered and the coverage gate passes:
  that's `maintaining-full-coverage`.
- **Post-change verification** — confirming a change works before claiming done:
  that's `smoke-test`.
- **Hardware-bound platform code** that is genuinely untestable without physical devices or elevated
  privileges and has no viable mock path: escalate via `escalate-over-shortcut`.
  Don't improvise a test-skipping shortcut.
- **CI parallelism and sharding strategy** — this skill focuses on the developer inner loop.
  CI implications surface in the references where relevant, but CI architecture is out of scope here.

## The decision tree

Profile first.
Every branch below starts from a profile result — not from guessing.
Running the suite under a profiler takes two minutes; it changes which lever you reach for.
Don't skip the profile step to go straight to "I'll add parallelism" — you'll spend a session applying the wrong fix.

**How to profile:** for Python, `pytest --durations=20` surfaces the 20 slowest test items immediately;
for deeper fixture attribution use `pytest-profiling` or `py-spy`.
For JVM, Gradle's `--profile` flag writes an HTML report; for Maven, `mvn test -Dsurefire.reportFormat=brief`.
For .NET, `dotnet test --logger "console;verbosity=detailed"` shows per-test timing.
The cue you're looking for is not "which test is slow" but "which *phase* of which test is slow" —
fixture setup, teardown, or body.

1. **Profile shows setup / fixtures heavy (>40% of wall clock in fixture code, database migrations,
   or test wiring)** → amortize the expensive setup across the maximum number of tests.
   The goal is to pay the expensive setup cost once and let many tests share the result.
   For pytest this means session-scoped or module-scoped fixtures; for JUnit 5 this means
   `@TestInstance(Lifecycle.PER_CLASS)` + `@BeforeAll`; for xUnit this means `IClassFixture`
   or `ICollectionFixture`.
   See `references/shared-fixtures.md`.
   If the fixture outlives a single test class — a database container, a browser instance, a running
   daemon — that's a persistent environment: see `references/persistent-environments.md`.

2. **Profile shows cold-start downloads or first-run compilation eating time (model weights,
   package caches, JIT warm-up, emulator first-boot)** → prime the cache before the suite runs.
   Warm once, reuse many.
   The key distinction: cold-start costs are one-time per environment, not one-time per test —
   so the fix is environment-level, not fixture-level.
   A CI job that caches compiled JVM bytecode between runs, a container image that bakes in the
   emulator snapshot, a Python `.pth` that pre-imports the heavy module.
   See `references/pre-warming.md`.

3. **Profile shows sequential runs, low CPU utilization, and no shared mutable state** →
   run tests in parallel.
   Pytest-xdist, Gradle parallel test execution, xUnit parallel collections.
   The speedup is proportional to the number of workers you can run without resource conflicts;
   the danger is hidden shared state (global singletons, ambient environment variables,
   in-process caches) that produces intermittent failures when tests stop running serially.
   Before enabling parallelism, audit for shared mutable state — the audit is faster than
   debugging a flaky parallel suite after the fact.
   See `references/parallelism.md`.

4. **Profile shows one or a handful of specific slow tests (explicit `sleep()`, network timeout,
   polling loop)** → reduce or eliminate the sleep.
   The common forms: a `sleep(5)` that waits for an async event (replace with polling + timeout
   or an event/signal); a network call with a 30-second default timeout (reduce or replace with
   a mock at the socket boundary); a polling loop waiting for a condition (replace with a callback
   or observable).
   Mock at the real external boundary — the network socket, the OS timer — not at the boundary
   you own.
   Mocking your own event bus to avoid the wait is mocking a boundary you control;
   the slow path still exists in production.
   See `references/pitfalls.md` for the full anti-pattern catalogue.

5. **Profile shows process or resource leaks (tests getting slower over the run, leftover daemons,
   port conflicts, memory growing)** → kill leaked processes and restore isolation between tests.
   The symptom is a suite that passes when run in isolation but gets slower or flakier as the run
   progresses.
   The cause is usually a test that starts a subprocess, opens a socket, or acquires a resource
   and doesn't clean up on failure.
   On Windows, use job objects or a snapshot-then-kill-tree on teardown.
   On Unix, track the parent PID and kill the process group.
   See `references/process-cleanup.md`.

6. **Suite mixes wall-clock-fast and wall-clock-slow tests, and the slow subset is blocking the
   iteration loop** → tier the suite by wall clock.
   Fast tier runs on every save or test command; slow tier runs pre-commit, in CI, and before
   claiming done.
   The threshold is a choice — 500ms is a reasonable starting point — and it belongs in the
   project's test configuration, not in human memory.
   Tagging is by *measured* duration, not by category label: a 20ms integration test stays in the
   fast tier, a 2-second unit test that starts a subprocess goes in the slow tier.
   See `references/tiering.md`.

If none of these branches fits and the slowness seems structural — the code's design makes cheap
testing impossible without touching the assertions — the solution is to restructure the production
code, not to exclude tests or weaken assertions.
See `references/restructure-over-exclude.md`.

## Principles

**1. Integration tests are the authoritative signal.**

A passing integration test means the product works.
A passing unit test means the unit works — which is a necessary but not sufficient condition.
The interesting failures live at boundaries: the unit tests pass, the product ships, the bug fires
in prod because the interface contract drifted.
Write tests that exercise the real system path.
Treat the impulse to swap integration coverage for unit coverage as a red flag, not a speedup.

**2. Profile before optimizing.**

Optimization without measurement is guessing.
The slow part of your suite is almost never what you think it is until you look.
Profile the first time you're tempted to reach for a structural fix — a 10-minute run often has a
20-second hotspot that a two-line fixture change eliminates.
The failure mode is applying the wrong lever (parallelism when the bottleneck is a single 5-minute
setup) and being surprised when nothing gets faster.

**3. Speed up SETUP, not the test.**

The test body — the assertions, the interaction with the system under test — is usually cheap.
The expensive part is what happens before the first assertion: spinning up an emulator, running
migrations, wiring a DI container, downloading a model.
That's the target.
If you're touching the assertion side or the coverage side to make the suite faster, you've left
this skill's territory and entered the next failure mode.

**4. Tier by wall clock, not by unit-vs-integration.**

"Unit" and "integration" are architectural categories. "Fast" and "slow" are measured categories.
A 20ms integration test belongs in the fast tier.
A 90-second unit test that spawns a subprocess belongs in the slow tier.
Tiering by architecture produces wrong splits that either over-include slow tests in the inner loop
or under-include fast integration tests that would have been cheap to run.
Tier by elapsed time — set a threshold (e.g., 500ms), measure each test, assign accordingly.

**5. Restructure code, not the coverage gate.**

When a test is slow because the production code tangles things that shouldn't be tangled —
network calls inline with business logic, startup side effects, untestable singletons — the right
move is to refactor the production code so the slow dependency is injectable.
This is the same move as deleting dead code: it makes the codebase healthier.
Restructuring to be testable is not overkill.
It is design work that pays down complexity and eliminates the branch that was impossible to test.

**6. Mock at genuine external boundaries only — never at boundaries you own.**

A mock is an assertion that the real thing would be called.
Mock the database driver, the HTTP socket, the OS timer — things outside your process that you
genuinely cannot own.
Do not mock your own service layer, your own repository, your own interface between two modules
you control.
Mocking your own boundaries means you're no longer testing the integration.
The test passes because the mock says it passes, not because the product works.

## Rationalization table

| Excuse | Reality |
|--------|---------|
| "I'll mock this integration to make it fast" | Mocks at boundaries you own fake the verify. The suite passes while the product breaks at exactly the boundary the mock was hiding. |
| "These tests are inherently slow" | Profile first. The inherently-slow set is usually less than 10% of wall clock. Surgery on those specific tests is faster than a blanket intervention that changes what you're testing. |
| "We'll skip integration tests in dev and run them in CI" | The 5-minute outer loop the user pays is now your problem too. CI catches regressions; dev catches them before push. Shifting them to CI doesn't make them faster — it makes failures more expensive. |
| "Slowness is just how this codebase is" | Slowness is composable. Each new `sleep(5)` compounds. Today's "just how it is" is yesterday's deferred fix. Pick the highest-value hotspot and start there. |
| "Add `@pytest.mark.slow` and skip them in dev" | Tag by wall clock, not by category. A 20ms integration test stays in the fast tier. A `@pytest.mark.slow` tag on a test you're not measuring is not tiering — it's exclusion with extra steps. |
| "Restructuring code to be testable is overkill" | Restructuring code to be testable is the same lever as deleting dead code — both eliminate uncovered, hard-to-reason-about branches and pay down design debt. |
| "Parallelism will fix everything" | Parallelism helps when CPU is the bottleneck. When the bottleneck is a single serialized setup step, parallel test workers all wait on the same thing. Profile first. |
| "The tests are fast enough for now" | Fast enough for now means slow enough to defer. Write down the current wall clock. When it doubles — and it will — you'll be glad you had the number. |

## References

- `references/profiling.md` — Where the time goes. Per-language profilers and cues.
- `references/parallelism.md` — pytest-xdist, Gradle parallel, xUnit collections.
- `references/shared-fixtures.md` — Amortize expensive setup across many tests.
- `references/persistent-environments.md` — Long-lived emulators, browsers, daemons, test hosts.
- `references/pre-warming.md` — Cache priming so fan-outs don't cold-start.
- `references/process-cleanup.md` — Snapshot-then-kill-tree on Windows; ppid tracking on Unix.
- `references/tiering.md` — Wall-clock-based tagging, NOT unit-vs-integration.
- `references/restructure-over-exclude.md` — Reshape code to eliminate unreachable branches.
- `references/pitfalls.md` — Cross-cutting anti-patterns to recognize and avoid.

## Integration notes

**`maintaining-full-coverage`** — orthogonal axes.
Speed never licenses skipping tests.
*Tiering* means "run less often in the dev inner loop," never "omit from the suite" — the full
suite still runs in CI, pre-commit, and before claiming done; coverage stays 100%.
Both skills agree on restructure-over-exclude.
Both reject mocking-owned-boundaries.
If speed pressure is eroding coverage, that's a `maintaining-full-coverage` event, not a
fast-tests trade-off.

**`smoke-test`** — orthogonal layers.
`smoke-test` is the outer-loop verify: "does the product work after this change?"
Fast-tests is the inner-loop mechanic: "how quickly can I re-verify during development?"
No overlap.
Both share the underlying premise that tests passing ≠ product working unless the tests are
actually exercising the product.

**`escalate-over-shortcut`** — partner skill for when no
fast-tests lever fits.
If you find yourself reaching for `[ExcludeFromCodeCoverage]` on a slow class, hard-coding an
emulator-specific shortcut, or swapping a real component for a mock just to skip its startup cost,
that's not a fast-tests technique — that's a hack.
Escalate, don't ship.

**`superpowers:test-driven-development`** — upstream.
Fast-tests assumes tests exist and are the right tests.
Decisions about *what* to test and *how* to structure tests belong to TDD.
Fast-tests picks up after the tests are in place and the loop is slow.

**`superpowers:dispatching-parallel-agents`** — parallel fan-outs that share a persistent
emulator or daemon need coordination.
Multiple subagents binding the same port, writing to the same test database, or competing for a
fixed-count emulator license all produce flaky or hanging test runs.
Coordination patterns are covered in `references/persistent-environments.md`.

Don't let speed pressure drive *which* tests get written (that's `maintaining-full-coverage`'s
fight), whether `smoke-test` runs (it's cheap regardless of suite speed), or silently become
"make this fake-pass" (escalate the moment that temptation surfaces — the test suite's job is to
tell the truth).
