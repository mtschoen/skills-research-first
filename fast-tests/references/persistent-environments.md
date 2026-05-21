# Persistent Environments

When the fixture outlives a single test class — a database container, a browser instance, a running daemon — pay the boot cost once across the whole session (or development day), not once per run.
The distinction from `shared-fixtures.md`: shared fixtures are in-process resources the test runner manages; persistent environments are out-of-process resources that survive between test runner invocations.

## Python

**`testcontainers-python`** — spin up Postgres, Redis, Kafka, or any Docker image and keep it running for the session:

```python
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()
```

For inner-loop speed, pull the container start out of the test run entirely: `docker compose up -d` before running tests, and connect with a hardcoded DSN in a session-scoped fixture that just checks connectivity rather than booting a container.

**Selenium / Playwright browser reuse** — one browser per session, fresh context per test:

```python
@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()

@pytest.fixture
def page(browser):
    context = browser.new_context()  # cheap
    pg = context.new_page()
    yield pg
    context.close()
```

**Long-lived dev database** — keep the database running between test runs; truncate between tests instead of restarting:

```python
@pytest.fixture(autouse=True)
def clean_tables(db):
    yield
    db.execute("TRUNCATE orders, users CASCADE")
```

**Docker Compose test stack** — manage out-of-band:

```bash
docker compose -f docker-compose.test.yml up -d
pytest tests/
docker compose -f docker-compose.test.yml down  # only on CI teardown
```

Tests connect via env-var DSN; no container lifecycle inside the test code.

## JVM

**Persistent Android Virtual Device** — the WindowStream lesson: a persistent AVD beats Gradle Managed Devices for inner-loop speed. GMD cold-boots an emulator per run (~2–3 minutes); a pre-running AVD takes 0 seconds because it's already up.

```bash
# Start once at the beginning of a dev session
emulator -avd Pixel_4 -no-snapshot-save -no-boot-anim &
adb wait-for-device

# Run tests directly — no emulator startup cost
./gradlew connectedAndroidTest
```

Use `-no-snapshot-save` to keep the AVD clean between sessions without full cold boot.

**Gradle daemon** — the daemon caches JVM startup and build configuration across runs. Confirm it's running:

```bash
./gradlew --status
```

First run of the day: `./gradlew test --daemon --parallel --configure-on-demand`. Subsequent runs reuse the warm daemon automatically. If the daemon is repeatedly killed (low memory, CI ephemeral runner), it's not helping — tune `org.gradle.jvmargs` heap instead.

**Long-lived JDBC connection pool** — keep a connection pool alive in a JVM-level static field or Spring `ApplicationContext` that's shared via `@RegisterExtension` at session scope. Avoid opening a new connection per test class.

## .NET

**`dotnet test --no-build --no-restore`** — when only test code changed, skip the build and restore steps:

```bash
dotnet test --no-build --no-restore MyProject.Tests/
```

Cuts 5–15 seconds on mid-size projects where MSBuild dominates cold runs.

**`dotnet watch test`** — rebuild and re-run on file change during development:

```bash
dotnet watch test --project MyProject.Tests/
```

**Persistent Postgres in Docker** — pull lifecycle management out of the test code:

```bash
docker run -d --name testdb -p 5432:5432 -e POSTGRES_PASSWORD=test postgres:16
```

Tests connect via `"Host=localhost;Database=test;Username=postgres;Password=test"`. Use EF Core's `UseNpgsql` rather than `UseInMemoryDatabase` — in-memory providers don't catch SQL dialect issues, constraint violations, or transaction semantics.

**Persistent Kestrel / IIS Express** — for integration tests against a running API, keep the host alive across test classes rather than `WebApplicationFactory.CreateClient()` per class:

```csharp
[CollectionDefinition("Api")]
public class ApiCollection : ICollectionFixture<ApiFixture> { }

public class ApiFixture : IAsyncLifetime {
    public HttpClient Client { get; private set; }
    public Task InitializeAsync() { /* start host once */ }
    public Task DisposeAsync() { /* stop host once */ }
}
```

## Cross-language coordination

When parallel agents share a persistent emulator or daemon, port and PID conflicts emerge.
The pattern: allocate ports from a per-agent range (agent 1 uses 5555–5559, agent 2 uses 5560–5564) rather than competing over a single fixed port.
On test exit, clean up reliably — `atexit` hook in Python, `try/finally` in JVM and .NET, signal traps where daemons need SIGTERM.
See `superpowers:dispatching-parallel-agents` for the broader orchestration pattern.
