# Parallelism

Parallelism helps when CPU is underutilized during runs and tests are genuinely independent.
It doesn't help when the bottleneck is a single serialized setup step — parallel workers all wait on the same thing.
Before flipping the switch, audit for shared mutable state — global singletons, ambient env vars, in-process caches — that produces intermittent failures under parallel runs.
Profile first (`references/profiling.md`); if CPU is the bottleneck, proceed here.

## Python

**Install `pytest-xdist` and run with `-n auto`:**

```bash
pip install pytest-xdist
pytest -n auto tests/
```

`-n auto` spawns one worker per CPU core. `-n 4` caps at 4 workers.

**Distribution modes** — choose based on fixture design:

- `--dist loadscope` groups tests by module or class. Tests in the same class share a worker, so class-scoped fixtures run once per class instead of once per worker. Best when fixtures are expensive and class-scoped.
- `--dist worksteal` keeps workers busy by stealing from busy queues. Best for suites with uneven test durations — fast workers pick up remaining work rather than idling.

```bash
pytest -n auto --dist loadscope tests/
pytest -n auto --dist worksteal tests/
```

**Session-scoped fixture pitfall:** With xdist, a `scope="session"` fixture runs once per worker process, not once per session. A fixture that boots a database or downloads a model will run N times for N workers.

Mitigation: use a file lock to ensure only one worker performs the expensive initialization, or accept the cost and use `scope="module"` instead. The `pytest-xdist` docs include a `tmp_path`-based lock pattern for this.

**Detecting hidden shared state:** if tests pass with `pytest` but fail with `pytest -n auto`, the failure is almost always shared mutable state — a global variable, a monkeypatch that wasn't restored, an environment variable mutation. Bisect with `-n 2` to narrow to a pair of tests, then audit the conflicting state.

## JVM

**Gradle multi-module parallel builds:**

```bash
./gradlew test --parallel
```

Or set permanently in `gradle.properties`:
```
org.gradle.parallel=true
```

Runs independent subproject builds in parallel. Each subproject still runs its own tests serially by default — combine with JUnit 5 parallel execution for intra-project concurrency.

**JUnit 5 parallel test execution** — add to `src/test/resources/junit-platform.properties`:

```properties
junit.jupiter.execution.parallel.enabled=true
junit.jupiter.execution.parallel.mode.default=concurrent
junit.jupiter.execution.parallel.mode.classes.default=concurrent
```

`mode.default=concurrent` runs methods within a class in parallel. `mode.classes.default=concurrent` runs classes in parallel. Both together maximizes concurrency.

**Static state pitfall:** JUnit 4 created a new test instance per test method, so static fields were effectively reset. JUnit 5 with `@TestInstance(Lifecycle.PER_CLASS)` reuses the same instance — static and instance fields persist across tests in the same class. Parallel execution amplifies this: two methods racing on the same instance field produces intermittent failures that are hard to reproduce serially.

Fix: eliminate mutable static state, use `@TestInstance(Lifecycle.PER_METHOD)` (the default), or synchronize explicitly with `@Execution(ExecutionMode.SAME_THREAD)` on specific tests.

## .NET

**xUnit parallel model** — xUnit parallelizes at the collection level by default. Tests in the same collection run serially; tests in different collections run in parallel.

`xunit.runner.json` knobs:

```json
{
  "parallelizeAssembly": true,
  "parallelizeTestCollections": true,
  "maxParallelThreads": 0
}
```

`maxParallelThreads: 0` means one thread per logical CPU. Place `xunit.runner.json` alongside the test project file.

**Disabling parallelism for a collection** — when a set of tests shares infrastructure that can't run concurrently:

```csharp
[CollectionDefinition("serial", DisableParallelization = true)]
public class SerialCollection { }

[Collection("serial")]
public class MySerialTests { ... }
```

**MSTest:**

```csharp
[assembly: Parallelize(Workers = 0, Scope = ExecutionScope.MethodLevel)]
```

Place in `AssemblyInfo.cs` or any file in the test project.

**NUnit:**

```csharp
[assembly: Parallelizable(ParallelScope.All)]
```

Or at the fixture level:

```csharp
[TestFixture]
[Parallelizable(ParallelScope.Children)]
public class MyTests { ... }
```
