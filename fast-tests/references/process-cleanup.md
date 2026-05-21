# Process Cleanup

Tests that spawn processes must clean them up, including grandchildren.
`Process.Start(...)` followed by a naive `Kill()` is not enough on modern Windows (launcher indirection) or Unix (process groups).
The pattern: snapshot existing PIDs by name before launch, then kill anything new on teardown.

## Windows / .NET

The validated snapshot-then-kill-tree pattern:

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

Use `entireProcessTree: true` (`.NET 5+`) to kill grandchildren. On older runtimes, walk children manually via `ManagementObjectSearcher` and `Win32_Process.ParentProcessId`.

## Unix / Python

Equivalent for `subprocess.Popen` on Linux/macOS: track the spawned PID and kill its process group.

```python
import os
import signal
import subprocess

proc = subprocess.Popen(
    [...],
    start_new_session=True,  # Linux: setsid(); macOS: same effect
)
try:
    # ... test body ...
finally:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=2)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
```

The portable case (cross-platform): use `psutil` with `children(recursive=True)` for a process-tree walk that works on Windows, Linux, and macOS.

```python
import psutil

parent = psutil.Process(proc.pid)
for child in parent.children(recursive=True):
    child.terminate()
gone, alive = psutil.wait_procs(parent.children(), timeout=2)
for survivor in alive:
    survivor.kill()
parent.terminate()
```

## JVM

`ProcessBuilder` + `Process.destroyForcibly()` doesn't kill grandchildren on most platforms. Use `ProcessHandle.descendants()` (Java 9+) to walk the tree:

```java
Process proc = new ProcessBuilder("some-cmd").start();
try {
    // ... test body ...
} finally {
    proc.descendants().forEach(ProcessHandle::destroyForcibly);
    proc.destroyForcibly();
    proc.waitFor(2, TimeUnit.SECONDS);
}
```

Zombie-process risk: if tests don't `waitFor()` after kill, processes may linger as `<defunct>` until the test runner exits. A suite with many leaked zombies accumulates file-descriptor pressure that manifests as port-binding failures late in the run — the symptom looks like flakiness, not a process leak.
