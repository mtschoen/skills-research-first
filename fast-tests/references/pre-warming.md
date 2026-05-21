# Pre-warming

Cold-start costs — first-run package installs, model downloads, JIT warm-up, emulator first-boot — are environment-level, not test-level.
Pay them once, before the suite (or before dispatching parallel agents), not once per test.

## Python

Run `pip install` before fan-out so each agent or worker inherits a fully-populated environment.
Reuse virtualenvs across agent runs rather than recreating them; creation itself is cheap, but the install step is not.

Default cache directory: `~/.cache/pip`.
Virtualenv storage: `~/.local/share/virtualenvs` (pipenv) or wherever the venv tool stores them.
Set `PIP_CACHE_DIR` explicitly in CI to make the location predictable.

When network access is intermittent, pre-build a local wheel cache with `pip wheel --wheel-dir ./wheels -r requirements.txt`
and install from it with `pip install --no-index --find-links ./wheels -r requirements.txt`.
This eliminates the network round-trip entirely on warm runs.

TODO: project-specific concrete steps (which packages benefit most, how to verify the cache hit) —
fill in when the first liminal-style project surfaces a real example.

## JVM

Pre-populate the Gradle cache before dispatching parallel agents.
A single warm-up invocation downloads all dependencies and wrapper binaries:

```bash
./gradlew dependencies --dry-run
```

Key cache directories:
- `~/.gradle/caches` — downloaded artifacts and compiled build scripts.
- `~/.gradle/wrapper/dists` — Gradle wrapper binaries.

For Android: pre-install the system image before any emulator run.
A cold `sdkmanager` fetch inside a parallelized agent is a multi-minute blocking download.

```bash
sdkmanager --install "system-images;android-34;default;x86_64"
```

Run this once, before fan-out, on the machine or in the CI layer.
The emulator itself (`emulator -avd <name> -no-window`) can then start without triggering any further SDK fetches.

TODO: concrete per-project warmup script — fill in when a JVM project surfaces specific packages
or emulator configurations that benefit from staged pre-warming.

## .NET

Run `dotnet restore` once at the workspace root before fan-out.
This populates `~/.nuget/packages` — the global package cache shared across all projects on the machine.
Subsequent `dotnet build` and `dotnet test` invocations in parallel agents resolve entirely from the local cache.

```bash
dotnet restore
```

The NuGet HTTP source is only contacted when a package version is absent from the global cache.
For CI layers or isolated machines, use `dotnet restore --packages ./local-nuget` to redirect to
a directory that can be restored from a cache artifact.

TODO: concrete sequencing for monorepos with shared package sets — fill in when a multi-project
.NET solution surfaces ordering dependencies or cache-miss patterns worth documenting.
