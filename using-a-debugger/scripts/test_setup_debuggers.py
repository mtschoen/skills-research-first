"""Tests for the setup-debuggers.py CLI entry point.

The module file uses a hyphenated name (so a real invocation can run it as a
script), so it cannot be imported with a plain `import` statement. Load it by
path instead, the same way it runs on the command line.
"""

import importlib.util
import sys
from pathlib import Path
from typing import NamedTuple

_MODULE_PATH = Path(__file__).resolve().parent / "setup-debuggers.py"
_SPEC = importlib.util.spec_from_file_location("setup_debuggers", _MODULE_PATH)
setup_debuggers = importlib.util.module_from_spec(_SPEC)
sys.modules["setup_debuggers"] = setup_debuggers
_SPEC.loader.exec_module(setup_debuggers)


class _FakeResult(NamedTuple):
    kind: str
    status: str
    detail: str


def test_main_passes_only_and_dry_run_through_to_run(monkeypatch):
    captured = {}

    def _fake_run(only, dry_run):
        captured["only"] = only
        captured["dry_run"] = dry_run
        return [_FakeResult("lldb", "present", "on PATH")]

    monkeypatch.setattr(setup_debuggers, "run", _fake_run)
    monkeypatch.setattr(
        sys, "argv", ["setup-debuggers.py", "--dry-run", "--only", "netcoredbg,lldb"]
    )

    result = setup_debuggers.main()

    assert result == 0
    assert captured == {"only": ["netcoredbg", "lldb"], "dry_run": True}


def test_main_defaults_only_to_none_and_dry_run_to_false(monkeypatch):
    captured = {}

    def _fake_run(only, dry_run):
        captured["only"] = only
        captured["dry_run"] = dry_run
        return []

    monkeypatch.setattr(setup_debuggers, "run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["setup-debuggers.py"])

    result = setup_debuggers.main()

    assert result == 0
    assert captured == {"only": None, "dry_run": False}


def test_main_prints_manual_follow_up_and_still_returns_zero(monkeypatch, capsys):
    monkeypatch.setattr(
        setup_debuggers,
        "run",
        lambda only, dry_run: [_FakeResult("cdb", "manual", "install the Windows SDK by hand")],
    )
    monkeypatch.setattr(sys, "argv", ["setup-debuggers.py"])

    result = setup_debuggers.main()

    out = capsys.readouterr().out
    assert result == 0
    assert "Manual follow-up needed:" in out
    assert "cdb: install the Windows SDK by hand" in out


def test_main_prints_failures_and_returns_one(monkeypatch, capsys):
    monkeypatch.setattr(
        setup_debuggers,
        "run",
        lambda only, dry_run: [_FakeResult("gdb", "failed", "download timed out")],
    )
    monkeypatch.setattr(sys, "argv", ["setup-debuggers.py"])

    result = setup_debuggers.main()

    out = capsys.readouterr().out
    assert result == 1
    assert "Failed:" in out
    assert "gdb: download timed out" in out
