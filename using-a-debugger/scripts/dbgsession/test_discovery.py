import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import discovery
from discovery import find_debugger, netcoredbg_install_dir


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        find_debugger("nonsense")


def test_gdb_matches_which():
    result = find_debugger("gdb")
    which_gdb = shutil.which("gdb")
    env_gdb = os.environ.get("GDB")
    if which_gdb is not None:
        assert result == which_gdb
    elif env_gdb is not None:
        assert result == env_gdb
    else:
        assert result is None


def test_lldb_health_check_rejects_bad_candidate(tmp_path, monkeypatch):
    if os.name == "nt":
        bad_lldb = tmp_path / "lldb.bat"
        bad_lldb.write_text("@echo off\nexit /b 1\r\n")
    else:
        bad_lldb = tmp_path / "lldb"
        bad_lldb.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n")
        bad_lldb.chmod(bad_lldb.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    monkeypatch.setenv("LLDB", str(bad_lldb))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    original_which = shutil.which

    def patched_which(name, *args, **kwargs):
        if name == "lldb":
            return None
        return original_which(name, *args, **kwargs)

    monkeypatch.setattr(shutil, "which", patched_which)

    result = find_debugger("lldb")
    assert result is None or result != str(bad_lldb)


def test_lldb_finds_llvm_program_files(tmp_path, monkeypatch):
    llvm_bin = tmp_path / "LLVM" / "bin"
    llvm_bin.mkdir(parents=True)
    lldb_exe = llvm_bin / "lldb.exe"
    lldb_exe.write_text("")
    monkeypatch.setenv("PROGRAMFILES", str(tmp_path))
    monkeypatch.delenv("PROGRAMFILES(X86)", raising=False)
    monkeypatch.delenv("LLDB", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(discovery.shutil, "which", lambda *a, **k: None)
    monkeypatch.setattr(discovery, "_health_check", lambda path: path == str(lldb_exe))

    assert discovery._find_lldb() == str(lldb_exe)


def test_lldb_finds_clion(tmp_path, monkeypatch):
    clion_bin = tmp_path / "Programs" / "CLion" / "bin" / "lldb" / "win" / "x64" / "bin"
    clion_bin.mkdir(parents=True)
    lldb_exe = clion_bin / "lldb.exe"
    lldb_exe.write_text("")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("PROGRAMFILES", raising=False)
    monkeypatch.delenv("PROGRAMFILES(X86)", raising=False)
    monkeypatch.delenv("LLDB", raising=False)
    monkeypatch.setattr(discovery.shutil, "which", lambda *a, **k: None)
    monkeypatch.setattr(discovery, "_health_check", lambda path: path == str(lldb_exe))

    assert discovery._find_lldb() == str(lldb_exe)


def test_netcoredbg_install_dir(monkeypatch):
    if os.name == "nt":
        monkeypatch.setenv("LOCALAPPDATA", "C:\\local\\app\\data")
        assert netcoredbg_install_dir() == Path("C:\\local\\app\\data\\Programs\\netcoredbg")
    else:
        monkeypatch.setenv("XDG_DATA_HOME", "/xdg/data")
        assert netcoredbg_install_dir() == Path("/xdg/data/netcoredbg")

        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setenv("HOME", "/my/home")
        assert netcoredbg_install_dir() == Path("/my/home/.local/share/netcoredbg")


def test_find_netcoredbg(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery.shutil, "which", lambda *a, **k: None)
    monkeypatch.delenv("NETCOREDBG", raising=False)

    monkeypatch.setattr(discovery, "netcoredbg_install_dir", lambda: None)
    assert discovery._find_netcoredbg() is None

    install_dir = tmp_path / "netcoredbg_install"
    sub_dir = install_dir / "netcoredbg"
    sub_dir.mkdir(parents=True)
    binary = "netcoredbg.exe" if os.name == "nt" else "netcoredbg"
    bin_file = sub_dir / binary
    bin_file.write_text("")

    monkeypatch.setattr(discovery, "netcoredbg_install_dir", lambda: install_dir)
    assert discovery._find_netcoredbg() == str(bin_file)

    flat_dir = tmp_path / "netcoredbg_flat"
    flat_dir.mkdir(parents=True)
    flat_bin = flat_dir / binary
    flat_bin.write_text("")

    monkeypatch.setattr(discovery, "netcoredbg_install_dir", lambda: flat_dir)
    assert discovery._find_netcoredbg() == str(flat_bin)


def test_find_cdb(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery.shutil, "which", lambda *a, **k: None)
    monkeypatch.delenv("CDB", raising=False)

    cdb_dir = tmp_path / "Windows Kits" / "10" / "Debuggers" / "x64"
    cdb_dir.mkdir(parents=True)
    cdb_exe = cdb_dir / "cdb.exe"
    cdb_exe.write_text("")

    monkeypatch.setenv("PROGRAMFILES(X86)", str(tmp_path))
    assert discovery._find_cdb() == str(cdb_exe)


def test_health_check(monkeypatch):
    def mock_run_timeout(*a, **k):
        raise subprocess.TimeoutExpired("cmd", 15)

    def mock_run_oserror(*a, **k):
        raise OSError("not found")

    monkeypatch.setattr(discovery.subprocess, "run", mock_run_timeout)
    assert not discovery._health_check("/dummy")

    monkeypatch.setattr(discovery.subprocess, "run", mock_run_oserror)
    assert not discovery._health_check("/dummy")


@pytest.mark.skipif(os.name != "nt", reason="lldb discovery integration is Windows-only")
def test_lldb_discoverable_on_windows():
    result = find_debugger("lldb")
    assert result is not None, "expected find_debugger('lldb') to find a working lldb"
    assert os.path.isfile(result), f"path does not exist: {result}"
    completed = subprocess.run(
        [result, "--version"],
        capture_output=True,
        timeout=15,
    )
    assert completed.returncode == 0, f"lldb --version returned {completed.returncode}"
