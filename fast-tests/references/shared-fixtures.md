# Shared Fixtures

When fixture setup costs more than the test body, the answer is to pay the setup once and let many tests share the result.
Scope the fixture to the broadest unit that makes correctness sense — don't cache test-mutated state across tests.
A session-scoped fixture that tests write into is a shared-mutable-state bug waiting to surface under parallel runs.

## Python

**Fixture scopes** — `scope` controls how often pytest tears down and re-runs the fixture:

| Scope | Runs once per... | Default? |
|---|---|---|
| `"function"` | test function | yes |
| `"class"` | test class | |
| `"module"` | `.py` file | |
| `"session"` | entire test run | |

```python
@pytest.fixture(scope="session")
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()
```

The default is `"function"` — one setup+teardown per test. When setup costs >100ms or involves I/O (database connection, network, subprocess), session or module scope is almost always the right call.

**`conftest.py` placement** — fixtures are visible to tests at the same level and below. A fixture in `tests/conftest.py` is available to all tests. A fixture in `tests/sub/conftest.py` is only available to tests under `tests/sub/`. Define expensive shared fixtures high in the tree.

**`yield` for setup/teardown** — everything before `yield` is setup; everything after is teardown. The fixture runs to completion even if the test fails.

```python
@pytest.fixture(scope="module")
def server(tmp_path_factory):
    base = tmp_path_factory.mktemp("server")
    proc = start_server(base)
    yield proc
    proc.terminate()
    proc.wait()
```

**Factory-as-fixture** — when tests need configured variants without duplicating setup code, the fixture returns a builder function:

```python
@pytest.fixture(scope="session")
def make_user(db):
    def _make(role="viewer"):
        return db.create_user(role=role)
    return _make

def test_admin_access(make_user):
    user = make_user(role="admin")
    ...
```

**Cost model:** a 200ms database setup × 50 tests = 10 seconds per run with function scope. Session scope: 200ms once. Module scope: 200ms × number of modules.

## JVM

**JUnit 5 `@BeforeAll` without static** — use `@TestInstance(Lifecycle.PER_CLASS)` to share setup across all tests in a class without requiring a static method:

```java
@TestInstance(Lifecycle.PER_CLASS)
class IntegrationTest {
    private Connection conn;

    @BeforeAll
    void startDatabase() {
        conn = Database.connect();
    }

    @AfterAll
    void stopDatabase() {
        conn.close();
    }
}
```

Before: 30 tests × 3s `@BeforeEach` = 90s. After: one `@BeforeAll` = 3s.

**JUnit 4 `@BeforeClass`** — requires a static method:

```java
public class IntegrationTest {
    private static Connection conn;

    @BeforeClass
    public static void startDatabase() {
        conn = Database.connect();
    }

    @AfterClass
    public static void stopDatabase() {
        conn.close();
    }
}
```

**`@RegisterExtension` with `ExtensionContext.Store`** — for resources that need a defined lifecycle scoped to a class or suite:

```java
@RegisterExtension
static final DatabaseExtension DB = new DatabaseExtension();
```

Implement `BeforeAllCallback` and `AfterAllCallback`; store the resource in `context.getStore(GLOBAL)` for session-scoped sharing across test classes.

## .NET

**xUnit `IClassFixture<T>`** — shared setup for all tests in a class. xUnit creates one `T` instance before the first test and disposes it after the last:

```csharp
public class DatabaseFixture : IDisposable {
    public TestDatabase Db { get; } = new TestDatabase();
    public void Dispose() => Db.Dispose();
}

public class MyTests : IClassFixture<DatabaseFixture> {
    private readonly DatabaseFixture _fixture;
    public MyTests(DatabaseFixture fixture) { _fixture = fixture; }
}
```

**xUnit `ICollectionFixture<T>`** — share a fixture across multiple test classes in the same collection:

```csharp
[CollectionDefinition("Database")]
public class DatabaseCollection : ICollectionFixture<DatabaseFixture> { }

[Collection("Database")]
public class OrderTests : { ... }

[Collection("Database")]
public class InvoiceTests : { ... }
```

Both `OrderTests` and `InvoiceTests` get the same `DatabaseFixture` instance.

**xUnit `IAsyncLifetime`** — for async setup/teardown:

```csharp
public class ServerFixture : IAsyncLifetime {
    public HttpClient Client { get; private set; }
    public Task InitializeAsync() { Client = await StartServerAsync(); return Task.CompletedTask; }
    public Task DisposeAsync() { Client.Dispose(); return Task.CompletedTask; }
}
```

**NUnit `[OneTimeSetUp]`** — per-fixture setup that runs once per test class (not once per test):

```csharp
[TestFixture]
public class IntegrationTests {
    private IConnection _conn;

    [OneTimeSetUp]
    public void Setup() { _conn = Database.Connect(); }

    [OneTimeTearDown]
    public void Teardown() { _conn?.Dispose(); }
}
```
