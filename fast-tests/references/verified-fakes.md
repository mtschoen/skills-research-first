# Verified fakes at an owned seam

The one sanctioned way to fake a boundary you own, and the measurements to take
before betting a campaign on it.

## When this applies

The spawn-volume branch of the decision tree sent you here: a suite spends its
wall clock launching short-lived subprocesses (git, CLI tools) because many
integration tests drive real orchestration against the real external tool, and
production-side dedup alone cannot get the volume down far enough.

## The pattern

Precedented shape, not an invention: owner-maintained fakes with fidelity via
contract tests (Google SWE book ch.13 "Test Doubles"), verified fakes
(pythonspeed.com/articles/verified-fakes/), and the practical-test-pyramid
contract-test half (Fowler). JGit maintains InMemoryRepository purely for
tests, with its command subset tested against the real thing.

1. **Seam**: the sanctioned wrapper module every subprocess call routes
   through. A fixture patches the consumer's import sites with methods of a
   fake instance. Production code stays untouched.
2. **Fake**: a small in-memory model of ONLY the behaviors the code under test
   observes (branches, opaque commit ids, dirty-file set, failure-mode
   switches). Fidelity to the observed surface, never to the tool in general.
3. **Contract suite**: one parametrized test module runs against BOTH the real
   implementation (on a real temporary instance of the external tool) and the
   fake, pinning agreement on every modeled behavior. It runs in the normal
   suite - the real leg is dozens of calls, not thousands. This is the
   load-bearing piece; without it the fake is a canned mock.
4. **Split audit**: classify the expensive tests into orchestration-asserting
   (migrate to the fake) and external-tool-semantics (keep real - they are the
   integration tier and the contract suite's justification).

## Measure the payoff floor FIRST

Before estimating savings, profile the per-test spawn floor from call sites the
fake structurally cannot intercept: raw calls elsewhere in production code that
bypass the seam, and function-local imports that defeat patching. Net saving
per migrated test = seam-routed spawns minus that floor. In the campaign that
produced this reference, an unmeasured floor of ~18 of ~25 spawns per test made
the initial estimate 7x too optimistic; the real lever turned out to be routing
the stray call sites through the seam before migrating tests.

Migration order that follows: route stray call sites through the seam first
(production refactor, contract-pin each routed function), then migrate tests in
batches with a spawn re-census per batch.

## Regression-guard with counts, not clocks

Assert spawn counts per test or per suite (from the census instrumentation).
Counts are deterministic and load-independent; wall clock on shared runners is
noise-dominated (co-tenant load and runner heterogeneity swamp sub-20% wins).

## What this is NOT

- **An in-process reimplementation of the tool** (e.g. a pure-Python git
  library replacing git): a different real implementation changes the system
  under test - tests then verify the library's semantics, not the shipped
  tool's.
- **Canned-transcript subprocess mocks** (pre-recorded argv->output maps):
  tautological for stateful sequences - the transcript encodes the very
  behavior the test should be free to exercise.
