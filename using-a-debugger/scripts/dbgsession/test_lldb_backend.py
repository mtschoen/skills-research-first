import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backends import lldb_cli as lldb_cli_module
from backends.lldb_cli import LldbCliBackend
from discovery import find_debugger

LLDB = find_debugger("lldb")


class _TimeoutTransport:
    """Fake transport whose startup sync never completes, to exercise start()'s
    cleanup path without spawning a real lldb process."""

    def __init__(self):
        self.closed = False

    def write(self, s):
        pass

    def read_until(self, predicate, timeout):
        raise TimeoutError("startup token never seen")

    def close(self):
        self.closed = True


class _TimeoutTransportCloseRaises(_TimeoutTransport):
    """Like _TimeoutTransport, but close() itself fails (e.g. the child process
    already exited between poll() and kill()) - the original TimeoutError must
    still win, not the close() failure."""

    def close(self):
        self.closed = True
        raise OSError("process already exited")


def test_start_closes_transport_and_reraises_on_sync_timeout(monkeypatch):
    fake = _TimeoutTransport()
    monkeypatch.setattr(lldb_cli_module, "open_transport", lambda argv, kind: fake)
    backend = LldbCliBackend("lldb", "pipe", "unused-program", [])

    with pytest.raises(TimeoutError):
        backend.start()

    assert fake.closed
    assert backend._transport is None


def test_start_reraises_original_error_when_close_also_fails(monkeypatch):
    fake = _TimeoutTransportCloseRaises()
    monkeypatch.setattr(lldb_cli_module, "open_transport", lambda argv, kind: fake)
    backend = LldbCliBackend("lldb", "pipe", "unused-program", [])

    with pytest.raises(TimeoutError):
        backend.start()

    assert fake.closed
    assert backend._transport is None


def test_stopped_and_quiet_waits_out_the_idle_window(monkeypatch):
    # lldb streams a stop notification's trailing detail (frame info, source
    # context) as a burst of separate lines rather than one atomic write.
    # _stopped_and_quiet must not fire the instant the stop line is seen - it
    # has to wait for that burst to stop growing, so a command sent right
    # after does not race lldb still flushing it. Drive it off a fake clock
    # instead of a real sleep so the test is fast and deterministic.
    fake_time = {"t": 0.0}
    monkeypatch.setattr(lldb_cli_module.time, "monotonic", lambda: fake_time["t"])
    predicate = lldb_cli_module._stopped_and_quiet(0.2)

    assert predicate("still running\n") is False
    assert predicate("stop reason = breakpoint 1.1\n") is False

    fake_time["t"] = 0.10
    assert predicate("stop reason = breakpoint 1.1\nframe #0: ...\n") is False

    # Same text again before the idle window elapses: still not quiet.
    fake_time["t"] = 0.25
    assert predicate("stop reason = breakpoint 1.1\nframe #0: ...\n") is False

    # 0.2s of no growth since the text last changed at t=0.10: quiet now.
    fake_time["t"] = 0.31
    assert predicate("stop reason = breakpoint 1.1\nframe #0: ...\n") is True


def test_stopped_and_quiet_resets_on_new_output(monkeypatch):
    fake_time = {"t": 0.0}
    monkeypatch.setattr(lldb_cli_module.time, "monotonic", lambda: fake_time["t"])
    predicate = lldb_cli_module._stopped_and_quiet(0.2)

    assert predicate("stop reason = breakpoint 1.1\n") is False

    # A new line arrives just before the window would have elapsed - this
    # resets the idle clock rather than letting the stale check fire.
    fake_time["t"] = 0.19
    assert predicate("stop reason = breakpoint 1.1\nmore output\n") is False

    fake_time["t"] = 0.30
    assert predicate("stop reason = breakpoint 1.1\nmore output\n") is False

    fake_time["t"] = 0.40
    assert predicate("stop reason = breakpoint 1.1\nmore output\n") is True


@pytest.mark.skipif(not LLDB or not shutil.which("clang++"), reason="needs working lldb + clang++")
def test_lldb_live_session_reads_locals():
    d = Path(tempfile.mkdtemp())
    (d / "hello.cpp").write_text(
        "int add(int a,int b){\n    int s=a+b;\n    return s;\n}\nint main(){return add(2,5)-7;}\n"
    )
    exe = d / ("hello.exe" if os.name == "nt" else "hello")
    subprocess.run(
        ["clang++", "-g", "-O0", "-o", str(exe), str(d / "hello.cpp")],
        check=True,
    )
    b = LldbCliBackend("lldb", "pipe", str(exe), [], LLDB)
    b.start()
    try:
        b.set_breakpoint("hello.cpp", 2)
        out = b.run()
        assert "stop reason" in out.lower()
        assert b.read_local("a") == "2"
        assert b.read_local("b") == "5"
    finally:
        b.stop()
