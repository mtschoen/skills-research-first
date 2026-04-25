# Fast Tests — Skill Handoff

**Status:** Not yet built. This document briefs the agent who will create the skill.

**What to build:** A project-agnostic skill that steers agents toward fast test loops without compromising an integration-testing-first philosophy. Deploy to `~/.claude/skills/fast-tests/` after development (follow the pattern in `reference_skills_dev.md` from the user's auto-memory).

## Core thesis (the skill's voice)

**Integration tests are the authoritative signal.** They are what verify the product works. If they are slow, speed up the SETUP — do NOT replace integration tests with unit-level mocks that pretend to verify behavior.

The bias toward unit testing assumes an idealized world where unit correctness implies system correctness. In practice, the interesting bugs live at integration boundaries — DPI mismatches between physical and logical pixels, Store-app launcher indirection, emulator cold-boot, codec queues filling when the consumer is slow, protocol field-name drift between two implementations. None of these show up in unit tests.

The skill should reinforce this bias and give agents techniques to make integration tests cheap enough that they ARE the fast path.

## When to apply

- Project has multi-system integration (OS capture, hardware encoding, emulators, browsers, databases, external APIs)
- Agents are iterating via TDD with gates (coverage or otherwise) and the inner loop is dominated by test-run wall clock
- Test setup is observably slower than test assertion

## Techniques the skill should organize

### 1. Persistent environments

Never boot an emulator, daemon, or external service per test run. Keep it warm across the session.

- **Android:** persistent AVD (not Gradle Managed Devices per-run) — first-run GMD downloads multi-hundred-MB SDK images and cold-boots per run (~2–3 min). A persistent AVD runs in the background; tests connect to it.
- **Browsers (Playwright, Cypress, etc.):** reuse browser, reuse context; reset state per test via API, not restart.
- **Docker test containers:** keep running; clean DB state between tests instead of restart.
- **.NET test host:** prefer `dotnet test --no-build --no-restore` or `dotnet watch test` when only test code changed.
- **Gradle daemon:** confirm it's running; `--daemon --parallel --configure-on-demand` up front.

### 2. Shared / warm fixtures

Pay expensive setup once per test class or collection, not per test.

- xUnit: `[Collection]` + `IAsyncLifetime` class fixture
- JUnit 5: `@TestInstance(Lifecycle.PER_CLASS)` + `@BeforeAll`
- pytest: session-scoped fixtures

This matters most when setup is seconds, not milliseconds. Booting a CLI + network listeners + encoder at 3 s → a 30-test suite pays 90 s cumulative with per-test fixtures vs. 3 s with class-level.

### 3. Pre-warmed external caches

Agents should not hit cold CDNs or package registries during test runs.

- Run `dotnet restore`, `npm install`, `./gradlew build`, `sdkmanager --install ...` ONCE before dispatching a fleet of agents, not per agent
- Cache directories (`~/.gradle/caches`, `~/.nuget/packages`, `~/.android/avd`, `~/.m2/repository`) must already be populated before fanning out
- Agents inherit the cache; downloading should be a rare exception

### 4. Process / resource cleanup

Tests that spawn processes must clean them up. Agents tend toward `Process.Start(...); finally kill` which is insufficient on modern Windows (Store-app indirection, process trees).

**Pattern that works** (validated from the WindowStream project):

```csharp
HashSet<int> existingPids = Process.GetProcessesByName("notepad")
    .Select(p => p.Id).ToHashSet();

Process launcher = Process.Start(...);
try {
    // ... test body ...
} finally {
    foreach (Process candidate in Process.GetProcessesByName("notepad")) {
        if (existingPids.Contains(candidate.Id)) {
            candidate.Dispose();
            continue;
        }
        try { candidate.Kill(entireProcessTree: true); candidate.WaitForExit(2000); }
        catch { /* best-effort */ }
        finally { candidate.Dispose(); }
    }
}
```

Why: `Process.Start("notepad.exe")` on Windows 11 returns a launcher that exits immediately; `CloseMainWindow` / `Kill` on the returned handle is a no-op against the actual UI process. Snapshot-then-kill-new catches the real process.

Equivalent for Linux/macOS processes: watch `/proc` or `ps` output, kill by spawned ppid or new pids that weren't there before.

### 5. Fast/slow tiering when feasible

Not every test needs to run on every change. Allow a default-fast mode and a full-integration mode.

- Tag slow tests (`[Trait("Category","Slow")]`, `@Tag("slow")`, `@pytest.mark.slow`)
- Default command runs fast tier; second command runs all
- **Do NOT tier by "unit" vs "integration."** Tier by wall clock. A 20 ms integration test stays in the fast tier. Categorizing by test shape encourages the wrong thinking.

### 6. Restructure code, not the coverage gate

When a coverage gate flags an unreachable branch in generated/framework code, agents tend to add a Kover/Coverlet exclusion. A better instinct: restructure the source to eliminate the branch.

**Example from WindowStream:**

```kotlin
// Before: Kover counts the while-false branch as uncovered
while (isActive) {
    delay(1000)
    evictExpired()
}

// After: no unreachable branch (delay() throws CancellationException on cancellation)
while (true) {
    delay(1000)
    evictExpired()
}
```

Exclusion IS correct for truly-untestable classes (platform framework bindings — MediaCodec, NsdManager, Android lifecycle, XR Compose composables). It is wrong for code whose only testability issue is shape. The skill should teach agents to recognize the difference.

## Pitfalls to call out in the skill

1. **Flakiness masquerading as slowness.** A test that occasionally hangs on a network timeout averages to "slow." Investigate the hang; don't just bump the timeout.
2. **Non-deterministic timeouts.** `delay(2000)` in a test that "sometimes fires" is a design problem, not a timing problem. Inject a test clock (virtual-time schedulers in coroutines-test, `FakeClock` types, `ManualTimeProvider` in .NET 8+).
3. **Tests that share mutable global state.** Serializing them via `[Collection]` is a symptom, not a cure. Fix the isolation.
4. **"I'll add integration tests later."** Retrofit cost compounds. Write integration tests when you write the code, even if slow; speed them up as you go — don't defer.
5. **Silent integration-test skip.** Skip-when-env-missing (e.g., no NVIDIA driver) is fine, but log it loud and surface in CI summaries. A silently skipped integration test that nobody notices is worse than one that fails.
6. **Mocking across boundaries you own.** Mocking your own module's internal interfaces produces tests that pass while the product breaks. Mock only at genuine external boundaries (OS APIs, third-party services, hardware).

## Suggested skill structure

```
~/skills-dev/fast-tests/
  SKILL.md                       # principles + triggers + thesis
  references/
    persistent-environments.md   # emulators, daemons, browsers, test hosts — with examples
    shared-fixtures.md           # xunit/junit/pytest patterns with code
    pre-warming.md               # cache-warming, SDK priming, dependency pre-install
    process-cleanup.md           # PID-snapshot + kill-tree pattern (concrete code)
    tiering.md                   # fast/slow tagging, wall-clock-based categorization
    restructure-over-exclude.md  # prefer code shape over coverage exclusion, with examples
    pitfalls.md                  # flakiness, non-determinism, silent skips, cross-own-boundary mocking
```

Keep the skill body principle-driven and concise. References carry the concrete examples. Per the user's `feedback_skills_tool_agnostic.md` memory: describe actions in prose, do not hard-code MCP/CLI dependencies.

## Concrete session insights (context for the skill author)

These are real observations from the WindowStream session (Windows → Android XR window-streaming project, April 2026). Pull from them for examples but do not tie the skill to this specific project.

- **Integration tests pay for themselves.** The end-to-end `SessionHost_Produces_Decodable_Idr_Frames_Over_Loopback` test caught real issues (NVENC queue filling at default GOP length, DPI mismatch between WGC physical pixels and `WindowInformation` logical pixels, Windows 11 Notepad launcher indirection) that no amount of unit tests would have found.
- **Gradle Managed Devices is expensive.** First-run downloaded a 500 MB+ system image and cold-booted an AVD; ~3 min added to every agent's iteration loop. Persistent AVD would have cut that to seconds.
- **Coverlet on .NET 10 SDK with `Directory.Build.props Condition="'$(IsTestProject)'=='true'"`** silently disabled coverage collection because `IsTestProject` wasn't set early enough for VSTest. Fix: set the properties directly in each test csproj, not in a conditional `Directory.Build.props` block.
- **Kover default engine counted synthetic kotlinx-serialization branches** as uncovered — `$$serializer` and `$Companion` singletons generated by the compiler plugin. Switching `useJacoco()` + class exclusions fixed it.
- **Coroutine cooperative-cancellation idiom** (`while (isActive) { delay(...) }`) has an inherently unreachable while-false branch. Restructure to `while (true) { delay(...) }` when possible; exclude only when restructuring hurts readability.
- **Agent isolation self-check matters.** A hook bug (`git worktree add ... 2>/dev/null || true`) silently fell back to no-isolation on race conditions; multiple parallel agents committed to `main`. Fix the hook to fail loud, and give each agent a pre-run `pwd` / `git rev-parse` check it must pass before touching files.

## Deployment

After building the skill, deploy per the user's standard skill workflow:
1. Work under `~/skills-dev/fast-tests/`
2. Install to `~/.claude/skills/fast-tests/` via the existing install script (see `~/skills-dev/install-skills.sh` or `install-skills.bat`)
3. Publish to GitHub if appropriate (per `reference_skills_dev.md` — user publishes selectively)

## Reading list for the skill author

- `~/.claude/skills/maintaining-full-coverage/` — existing skill on coverage discipline; complements this one
- `~/.claude/skills/smoke-test/` — existing skill on post-change verification
- `~/.claude/skills/wrap/` — reference for skill structure/style in this user's kit
- WindowStream project at `C:\Users\mtsch\WindowStream` — git log and `docs/superpowers/specs/2026-04-19-windowstream-design.md` for a worked example of integration-heavy testing

No user interview is required; the thesis and techniques above are well-validated. Keep the skill under 300 lines in `SKILL.md`; push detail into references.
