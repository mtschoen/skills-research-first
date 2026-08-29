"""Tests for the dbg-session.py CLI entry point.

The module file uses a hyphenated name (so a real invocation can run it as a
script), so it cannot be imported with a plain `import` statement. Load it by
path instead, the same way it runs on the command line.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parent / "dbg-session.py"
_SPEC = importlib.util.spec_from_file_location("dbg_session", _MODULE_PATH)
dbg_session = importlib.util.module_from_spec(_SPEC)
sys.modules["dbg_session"] = dbg_session
_SPEC.loader.exec_module(dbg_session)


def test_session_dir_joins_base_and_name(tmp_path, monkeypatch):
    monkeypatch.setattr(dbg_session, "_SESSION_BASE", tmp_path)
    assert dbg_session._session_dir("my-session") == tmp_path / "my-session"


def test_wait_for_port_file_returns_true_once_written(tmp_path):
    session_dir = tmp_path / "sess"
    session_dir.mkdir()
    (session_dir / "port").write_text("12345")

    assert dbg_session._wait_for_port_file(session_dir) is True


def test_wait_for_port_file_times_out_when_absent(tmp_path, monkeypatch):
    # Bound the wait tightly so the timeout path is exercised in a few
    # milliseconds instead of the real 10 second default.
    monkeypatch.setattr(dbg_session, "_PORT_WAIT_SECONDS", 0.05)
    monkeypatch.setattr(dbg_session, "_PORT_POLL_INTERVAL", 0.01)
    session_dir = tmp_path / "sess"
    session_dir.mkdir()

    assert dbg_session._wait_for_port_file(session_dir) is False


def test_cmd_start_server_child_delegates_to_run_server_child(monkeypatch):
    monkeypatch.setenv("_DBG_SERVER", "1")
    calls = []
    fake_server = type(sys)("server")
    fake_server.run_server_child = lambda args: calls.append(args)
    monkeypatch.setitem(sys.modules, "server", fake_server)

    args = argparse.Namespace(debugger="lldb", session="s", program="p", program_args=[])
    result = dbg_session._cmd_start(args)

    assert result == 0
    assert calls == [args]


def test_cmd_start_launches_detached_child_and_waits_for_port(tmp_path, monkeypatch):
    monkeypatch.delenv("_DBG_SERVER", raising=False)
    monkeypatch.setattr(dbg_session, "_SESSION_BASE", tmp_path)

    captured = {}

    def _fake_popen(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        # Simulate the detached server child having started and written its
        # port file by the time _wait_for_port_file polls for it.
        (tmp_path / "s" / "port").write_text("54321")
        return object()

    monkeypatch.setattr(dbg_session.subprocess, "Popen", _fake_popen)

    args = argparse.Namespace(
        debugger="lldb", debugger_path=None, session="s", program="prog", program_args=["a"]
    )
    result = dbg_session._cmd_start(args)

    assert result == 0
    assert captured["argv"][0] == sys.executable
    assert captured["kwargs"]["env"]["_DBG_SERVER"] == "1"
    assert (tmp_path / "s" / "server.log").exists()


def test_cmd_start_reports_error_when_port_file_never_appears(tmp_path, monkeypatch):
    monkeypatch.delenv("_DBG_SERVER", raising=False)
    monkeypatch.setattr(dbg_session, "_SESSION_BASE", tmp_path)
    monkeypatch.setattr(dbg_session, "_PORT_WAIT_SECONDS", 0.05)
    monkeypatch.setattr(dbg_session, "_PORT_POLL_INTERVAL", 0.01)
    monkeypatch.setattr(dbg_session.subprocess, "Popen", lambda *a, **k: object())

    args = argparse.Namespace(
        debugger="lldb", debugger_path=None, session="s", program="prog", program_args=[]
    )
    result = dbg_session._cmd_start(args)

    assert result == 1


def test_cmd_send_prints_reply_and_forwards_verb(monkeypatch, capsys):
    calls = []

    def _fake_send_verb(session_dir, verb):
        calls.append((session_dir, verb))
        return "reply-text"

    monkeypatch.setattr(dbg_session, "send_verb", _fake_send_verb)
    monkeypatch.setattr(dbg_session, "_SESSION_BASE", Path("/tmp/base-does-not-matter"))

    args = argparse.Namespace(session="my-sess", verb="bt")
    result = dbg_session._cmd_send(args)

    assert result == 0
    assert capsys.readouterr().out == "reply-text"
    assert calls == [(dbg_session._session_dir("my-sess"), "bt")]


def test_cmd_stop_sends_stop_sentinel(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        dbg_session, "send_verb", lambda session_dir, verb: calls.append(verb) or "stopped"
    )

    args = argparse.Namespace(session="my-sess")
    result = dbg_session._cmd_stop(args)

    assert result == 0
    assert calls == ["__STOP__"]
    assert capsys.readouterr().out == "stopped"


def test_build_parser_parses_all_subcommands():
    parser = dbg_session._build_parser()

    start_args = parser.parse_args(
        ["start", "--debugger", "lldb", "--session", "s1", "prog", "arg1", "arg2"]
    )
    assert start_args.subcommand == "start"
    assert start_args.debugger == "lldb"
    assert start_args.session == "s1"
    assert start_args.program == "prog"
    assert start_args.program_args == ["arg1", "arg2"]

    send_args = parser.parse_args(["send", "--session", "s1", "bt"])
    assert send_args.subcommand == "send"
    assert send_args.verb == "bt"

    stop_args = parser.parse_args(["stop", "--session", "s1"])
    assert stop_args.subcommand == "stop"
    assert stop_args.session == "s1"


def test_main_dispatches_to_matching_subcommand(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["dbg-session.py", "stop", "--session", "s1"])
    calls = []
    monkeypatch.setattr(dbg_session, "_cmd_stop", lambda args: calls.append(args.session) or 0)

    result = dbg_session.main()

    assert result == 0
    assert calls == ["s1"]
