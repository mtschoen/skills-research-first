# Tiering

Tier by wall clock, not by unit-vs-integration architectural category.
A 20ms integration test belongs in the fast tier.
A 5-second unit test that spawns a subprocess belongs in the slow tier.
Set a threshold (500ms is a reasonable starting point), measure each test, assign accordingly.

## Critical clarification

Tiering means "run less often in the dev inner loop" — NOT "omit from the suite."
The full suite still runs in CI, pre-commit, and before claiming done.
Coverage stays 100% per `maintaining-full-coverage`.

The "@pytest.mark.slow + skip in dev" rationalization fast-tests rejects (see SKILL.md rationalization table)
is the failure mode this skill guards against — tiering is a scheduling optimization, not a coverage loophole.

## Python

**Tag slow tests** with `@pytest.mark.slow` on any test above threshold.

**Fast-tier default** in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-m 'not slow'"
```

**Run all tiers** (CI, pre-commit, before claiming done): `pytest --override-ini="addopts="` or `pytest -m ""`.

**Measurement step:** run `pytest --durations=0` once to get a full duration list.
Decorate tests above threshold, re-run with the fast filter to confirm.
Re-measure periodically — slow tests creep in silently.

TODO: automated re-tiering script (parses `--durations=0` output, updates marks) — fill in when a project
accumulates enough tests to make manual re-tiering tedious.

## JVM

**Tag slow tests** with JUnit 5's `@Tag("slow")` on test classes or methods.

```java
@Tag("slow")
class FullPipelineTest { ... }
```

**Fast-tier default** in the Gradle `test` task:

```kotlin
tasks.test {
    useJUnitPlatform { excludeTags("slow") }
}
```

**Separate task for the slow tier:** `tasks.register<Test>("slowTest") { useJUnitPlatform { includeTags("slow") } }`.
Run `./gradlew slowTest` in CI and before claiming done to cover the full suite.

TODO: per-project threshold convention — fill in when a JVM project surfaces a distribution
that suggests a threshold other than 500ms.

## .NET

**Tag slow tests** with xUnit's `[Trait]`:

```csharp
[Trait("Category", "Slow")]
public async Task FullPipelineTest() { ... }
```

**Fast-tier run:**

```bash
dotnet test --filter "Category!=Slow"
```

**Full suite run** (CI and before claiming done): `dotnet test`.

TODO: integration with the per-repo coverage gate (see `maintaining-full-coverage`) — fill in
when a .NET project needs the slow tier wired into the coverage report to avoid false-green gates.
