# Profiling

Profiling is the first action, not the last.
Two minutes running the suite under a profiler tells you which phase is slow — fixture setup, teardown, or test body — and that changes everything about which lever you reach for next.
Two hours guessing at parallelism or fixture restructuring without a profile almost always targets the wrong hotspot.

## Python

**`pytest --durations=N`** — built-in slowest-N report. No install required.

```
pytest --durations=20
```

Output shows phase per test (`setup`, `call`, `teardown`). If setup dominates, see `shared-fixtures.md`. If a single `call` entry dominates, investigate that test body.

```
slowest 20 durations
8.43s setup    tests/test_api.py::test_full_stack
3.12s call     tests/test_import.py::test_heavy_module
0.91s teardown tests/test_db.py::test_migration
```

**`pyinstrument`** — sampling profiler, low overhead. Recommended for a first look.

```bash
pip install pyinstrument
pyinstrument -m pytest tests/
```

Produces a flamegraph-style tree in the terminal. Identifies which functions inside fixture code consume the time.

**`pytest-profiling`** — cProfile-backed per-test profile.

```bash
pip install pytest-profiling
pytest --profile tests/
```

Writes `.prof` files per test. Heavyweight — use selectively when `pyinstrument` points at a hot function but doesn't show enough call depth.

**`python -X importtime`** — surfaces slow imports during collection. Useful when `--collect-only` takes several seconds even before tests run.

```bash
python -X importtime -m pytest --collect-only 2>&1 | sort -t: -k2 -n | tail -20
```

**`pytest --collect-only`** — sanity check to separate collection time from test-execution time. If collection alone takes >5 seconds, the import-time tool above is the next step.

## JVM

**Gradle `--profile`** — generates an HTML report at `build/reports/profile/`.

```bash
./gradlew test --profile
```

Open the HTML report and look at the "Tests" section for per-test durations and the "Configuration" section for configuration-phase overhead. If configuration takes longer than test execution, `--configuration-cache` is the fix (see below).

**Java Flight Recorder** — for deep JVM-level profiling when `--profile` shows test execution is slow but doesn't narrow the cause.

```bash
./gradlew test -Dorg.gradle.jvmargs="-XX:+FlightRecorder \
  -XX:StartFlightRecording=filename=test.jfr,dumponexit=true"
```

Open `test.jfr` in JDK Mission Control. Heavyweight — use when the HTML profile shows a specific test module is slow and you need to attribute it to a method.

**async-profiler** — sampling profiler that produces flame graphs without JVM overhead. Attach to the test JVM via PID or via the Gradle agent argument. See `async-profiler` GitHub for current attach syntax.

**Gradle `--scan` and `--configuration-cache`** — `./gradlew test --scan` provides a hosted build scan with configuration/execution breakdown. `--configuration-cache` (stable since Gradle 8) skips re-evaluating build scripts on repeat runs with unchanged inputs. Pays back on multi-module projects with stable configurations.

## .NET

**`dotnet test --logger "console;verbosity=detailed"`** — per-test timing with no extra tooling.

```bash
dotnet test --logger "console;verbosity=detailed"
```

Shows `Passed`, `Failed`, or `Skipped` per test with elapsed time in milliseconds. The baseline before reaching for heavier tools.

**`dotnet-trace`** — for tracing the test host process. Requires the test host PID; launch the tests in a separate terminal and attach.

```bash
dotnet-trace collect --process-id <pid> --output test-trace.nettrace
```

Open in PerfView or Visual Studio's diagnostic tools. Use when `--logger` shows a specific test is slow but doesn't explain why.

**VSTest `--diag`** — diagnostic log for test infrastructure issues (slow test discovery, slow data adapters, adapter crashes).

```bash
dotnet test --diag test-diag.log
```

Look for lines with `Adapter` or `Discovery` in the log. If discovery dominates the run time, a test adapter configuration issue is the likely cause, not the tests themselves.

**BenchmarkDotNet caveat:** BenchmarkDotNet is for microbenchmarking hot paths in production code, not for diagnosing test suite speed. Do not reach for it when the question is "why are my tests slow." It adds significant overhead and measures the wrong thing.
