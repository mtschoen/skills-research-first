# Pitfalls

The fast-tests skill exists to prevent specific failure modes when chasing speed.
The patterns below are the ones that look like wins in the moment and bite later.
No language sub-sections — these apply universally.

### 1. Mocking your own boundaries

Mock at OS / third-party / hardware boundaries only.
Mocking your own module's interfaces produces tests that pass while the product breaks.
This is the deepest anti-pattern this skill rejects: you're writing `when(mockRepo.find(...)).thenReturn(...)` for a repository you own and control.
The mock says the test passes; the real repository says the product doesn't.
Right move: persist real data to a real (possibly in-process) database, or factor the dependency at a genuine external boundary.

### 2. Flakiness masquerading as slowness

A test that occasionally hangs averages to "slow" in the durations report.
Don't bump the timeout — investigate the hang.
Cue: the same test shows wide duration variance across runs (1s one time, 45s the next) in `pytest --durations` or Gradle's test report.
Right move: identify the race or deadlock, fix it, and restore deterministic timing.

### 3. Non-deterministic timeouts

`delay(2000)` "sometimes fires in time" is a design problem, not a timing problem.
The fix is virtual time — coroutines-test's `TestCoroutineScheduler`, `FakeClock` in Guava/JUnit, or .NET 8+'s `TimeProvider.ManualTimeProvider` — not a longer timeout.
Cue: a test has an explicit `sleep` or `delay` call in the body rather than in a fixture.
Right move: inject the clock, advance it in the test, assert on the outcome.

### 4. Tests sharing mutable global state

Serializing them with `[Collection(..., DisableParallelization = true)]` or `pytest -p no:xdist` is a symptom, not a cure.
Cue: removing the serialization constraint causes intermittent failures.
Right move: fix the isolation — thread-local state, dependency injection, explicit fixture scope.
Serialization is a temporary quarantine while you find the leak, not a permanent fix.

### 5. "I'll add integration tests later"

Retrofit cost compounds.
Write integration tests when you write the code, even slow ones; speed them up as you go using the techniques in this skill.
Cue: a PR adds production code with only unit-level coverage and a comment about "adding integration tests in a follow-up."
That follow-up doesn't ship — the production code changes again before the integration test is written, and the follow-up is now three times as hard.

### 6. Silent integration-test skip

Skip-when-env-missing (no GPU, no network, no license) is sometimes necessary.
But a silently-skipped integration test that nobody notices is worse than one that fails: the suite reports green while the coverage is hollow.
Cue: `@pytest.mark.skipif(not GPU, reason="...")` with no CI visibility into the skip count.
Right move: log loud and surface skips in CI summaries.
A skip that nobody sees is the same as a test that doesn't exist.

### 7. Tiering by category instead of wall clock

A 20ms integration test belongs in the fast tier.
A 5-second unit test that starts a subprocess belongs in the slow tier.
Cue: the "slow" marker was applied because the test is an integration test, not because it was measured.
Right move: tag by measured duration. Set a threshold (500ms is a reasonable starting point), measure each test with `pytest --durations` or the equivalent, assign accordingly.
See `references/tiering.md`.

### 8. Threshold-lowering to escape a gate

Dropping a coverage threshold, a timeout, or a quality bar to dodge a slow test or a flaky behavior is changing the test to match the bug.
Cue: a PR lowers `--cov-fail-under`, raises a timeout constant, or adds `[ExcludeFromCodeCoverage]` without a documented reason.
Right move: escalate via `escalate-over-improvise` (handoff exists, not yet built) and fix the underlying issue rather than ship the workaround.
The gate exists to tell the truth; weakening it means you're paying to hear less truth.
