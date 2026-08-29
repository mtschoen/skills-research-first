import io
import json
import os
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import setup
from setup import (
    Result,
    _extract_archive,
    install_cdb_windows,
    install_for,
    install_lldb_macos,
    install_native_linux,
    install_netcoredbg,
    netcoredbg_asset_substring,
    platform_targets,
    select_asset,
)


def test_platform_targets_per_system():
    assert platform_targets("Linux") == ("netcoredbg", "gdb", "lldb")
    assert platform_targets("Darwin") == ("netcoredbg", "lldb")
    assert platform_targets("Windows") == ("netcoredbg", "cdb", "lldb")
    assert platform_targets("plan9") == ()


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Windows", "AMD64", "win64"),
        ("Windows", "ARM64", "win64"),
        ("Linux", "x86_64", "linux-amd64"),
        ("Linux", "aarch64", "linux-arm64"),
        ("Darwin", "x86_64", "osx-amd64"),
        ("Darwin", "arm64", "osx-amd64"),
        ("Plan9", "x86_64", None),
    ],
)
def test_netcoredbg_asset_substring(system, machine, expected):
    assert netcoredbg_asset_substring(system, machine) == expected


def test_select_asset_matches_and_misses():
    names = [
        "netcoredbg-linux-amd64.tar.gz",
        "netcoredbg-linux-arm64.tar.gz",
        "netcoredbg-win64.zip",
    ]
    assert select_asset(names, "linux-arm64") == "netcoredbg-linux-arm64.tar.gz"
    assert select_asset(names, "win64") == "netcoredbg-win64.zip"
    assert select_asset(names, "osx-amd64") is None


def test_run_skips_present_debuggers(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup, "find_debugger", lambda kind: f"/usr/bin/{kind}")
    installs: list[str] = []
    monkeypatch.setattr(
        setup,
        "install_for",
        lambda kind, system, dry_run: installs.append(kind) or Result(kind, "installed", ""),
    )

    results = setup.run(report=lambda _line: None)

    assert installs == []  # nothing missing, so nothing installed
    assert {result.kind for result in results} == {"netcoredbg", "gdb", "lldb"}
    assert all(result.status == "present" for result in results)


def test_run_installs_only_missing(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        setup, "find_debugger", lambda kind: "/usr/bin/gdb" if kind == "gdb" else None
    )
    installed: list[str] = []
    monkeypatch.setattr(
        setup,
        "install_for",
        lambda kind, system, dry_run: installed.append(kind) or Result(kind, "installed", ""),
    )

    results = setup.run(report=lambda _line: None)

    assert installed == ["netcoredbg", "lldb"]  # gdb present, skipped
    by_kind = {result.kind: result.status for result in results}
    assert by_kind == {"netcoredbg": "installed", "gdb": "present", "lldb": "installed"}


def test_run_only_filters_targets(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Windows")
    monkeypatch.setattr(setup, "find_debugger", lambda kind: None)
    seen: list[str] = []
    monkeypatch.setattr(
        setup,
        "install_for",
        lambda kind, system, dry_run: seen.append(kind) or Result(kind, "installed", ""),
    )

    setup.run(only=["lldb"], report=lambda _line: None)

    assert seen == ["lldb"]


def test_run_dry_run_does_not_install(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup, "find_debugger", lambda kind: None)
    flags: list[bool] = []
    monkeypatch.setattr(
        setup,
        "install_for",
        lambda kind, system, dry_run: flags.append(dry_run) or Result(kind, "dryrun", ""),
    )

    results = setup.run(dry_run=True, report=lambda _line: None)

    assert all(flags)  # dry_run propagated to every dispatch
    assert all(result.status == "dryrun" for result in results)


def test_run_empty_platform_targets(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Plan9")
    report_lines = []
    results = setup.run(report=report_lines.append)
    assert results == []
    assert len(report_lines) == 1


def _winget_result(returncode, stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr=stderr)


def test_install_lldb_windows_already_installed_is_present(monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: "winget")
    monkeypatch.setattr(
        setup, "_run", lambda cmd: _winget_result(setup._WINGET_NO_APPLICABLE_UPGRADE)
    )

    result = setup.install_lldb_windows(dry_run=False)

    assert result.kind == "lldb"
    assert result.status == "present"


def test_install_lldb_windows_real_failure_reports_failed(monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: "winget")
    monkeypatch.setattr(setup, "_run", lambda cmd: _winget_result(1, stderr="network down"))

    result = setup.install_lldb_windows(dry_run=False)

    assert result.status == "failed"
    assert "network down" in result.detail


def test_install_lldb_windows_success_reports_installed(monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: "winget")
    monkeypatch.setattr(setup, "_run", lambda cmd: _winget_result(0))

    result = setup.install_lldb_windows(dry_run=False)

    assert result.status == "installed"


def test_install_lldb_windows_dry_run(monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: "winget")
    result = setup.install_lldb_windows(dry_run=True)
    assert result.status == "dryrun"


def test_install_lldb_windows_no_winget(monkeypatch):
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    result = setup.install_lldb_windows(dry_run=False)
    assert result.status == "manual"


def test_install_netcoredbg_dry_run_is_inert(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.platform, "machine", lambda: "x86_64")

    def fail_http(*_args, **_kwargs):
        raise AssertionError("dry run must not touch the network")

    monkeypatch.setattr(setup, "_http_get", fail_http)

    result = setup.install_netcoredbg(dry_run=True)

    assert result.kind == "netcoredbg"
    assert result.status == "dryrun"


def test_install_netcoredbg_no_machine_support(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Plan9")
    monkeypatch.setattr(setup.platform, "machine", lambda: "mips")
    result = install_netcoredbg(dry_run=False)
    assert result.status == "failed"


def test_install_netcoredbg_no_install_dir(monkeypatch):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(setup, "netcoredbg_install_dir", lambda: None)
    result = install_netcoredbg(dry_run=False)
    assert result.status == "failed"


def test_install_netcoredbg_success(monkeypatch, tmp_path):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.platform, "machine", lambda: "x86_64")
    install_dir = tmp_path / "installed_netcoredbg"
    monkeypatch.setattr(setup, "netcoredbg_install_dir", lambda: install_dir)

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(name="netcoredbg/netcoredbg")
        info.size = 0
        tf.addfile(info, io.BytesIO(b""))

    releases_json = json.dumps(
        {
            "assets": [
                {
                    "name": "netcoredbg-linux-amd64.tar.gz",
                    "browser_download_url": "https://example.com/netcoredbg.tar.gz",
                }
            ]
        }
    ).encode()

    def mock_http_get(url, **kwargs):
        if "releases" in url:
            return releases_json
        return tar_buf.getvalue()

    monkeypatch.setattr(setup, "_http_get", mock_http_get)

    result = install_netcoredbg(dry_run=False)
    assert result.status == "installed"


def test_install_netcoredbg_download_error(monkeypatch, tmp_path):
    monkeypatch.setattr(setup.platform, "system", lambda: "Linux")
    monkeypatch.setattr(setup.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(setup, "netcoredbg_install_dir", lambda: tmp_path)
    monkeypatch.setattr(setup, "_http_get", MagicMock(side_effect=OSError("network failure")))

    result = install_netcoredbg(dry_run=False)
    assert result.status == "failed"
    assert "download failed" in result.detail


def test_install_native_linux(monkeypatch):
    monkeypatch.setattr(
        setup.shutil, "which", lambda name: "/usr/bin/apt-get" if name == "apt-get" else None
    )
    monkeypatch.setattr(setup.os, "geteuid", lambda: 0)

    # dry run
    result = install_native_linux("gdb", dry_run=True)
    assert result.status == "dryrun"

    # success
    monkeypatch.setattr(setup, "_run", lambda cmd: subprocess.CompletedProcess([], 0, "", ""))
    result = install_native_linux("gdb", dry_run=False)
    assert result.status == "installed"

    # sudo needed but fails
    monkeypatch.setattr(setup.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        setup, "_run", lambda cmd: subprocess.CompletedProcess([], 1, "", "sudo error")
    )
    result = install_native_linux("gdb", dry_run=False)
    assert result.status == "manual"

    # command failed
    def mock_run_fail(cmd):
        if cmd == ["sudo", "-n", "true"]:
            return subprocess.CompletedProcess([], 0, "", "")
        return subprocess.CompletedProcess([], 1, "", "apt failed")

    monkeypatch.setattr(setup, "_run", mock_run_fail)
    result = install_native_linux("gdb", dry_run=False)
    assert result.status == "failed"

    # no package manager
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    result = install_native_linux("gdb", dry_run=False)
    assert result.status == "manual"


def test_install_lldb_macos(monkeypatch):
    # brew available
    monkeypatch.setattr(
        setup.shutil,
        "which",
        lambda name: "/opt/homebrew/bin/brew" if name == "brew" else None,
    )
    result = install_lldb_macos(dry_run=True)
    assert result.status == "dryrun"

    monkeypatch.setattr(setup, "_run", lambda cmd: subprocess.CompletedProcess([], 0, "", ""))
    result = install_lldb_macos(dry_run=False)
    assert result.status == "installed"

    monkeypatch.setattr(
        setup, "_run", lambda cmd: subprocess.CompletedProcess([], 1, "", "brew error")
    )
    result = install_lldb_macos(dry_run=False)
    assert result.status == "failed"

    # no brew -> xcode-select
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    result = install_lldb_macos(dry_run=True)
    assert result.status == "dryrun"

    monkeypatch.setattr(setup, "_run", lambda cmd: subprocess.CompletedProcess([], 0, "", ""))
    result = install_lldb_macos(dry_run=False)
    assert result.status == "manual"


def test_install_cdb_windows(monkeypatch):
    # no winsdksetup
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    result = install_cdb_windows(dry_run=False)
    assert result.status == "manual"

    # winsdksetup present
    monkeypatch.setattr(setup.shutil, "which", lambda name: "C:\\winsdksetup.exe")
    result = install_cdb_windows(dry_run=True)
    assert result.status == "dryrun"

    monkeypatch.setattr(setup, "_run", lambda cmd: subprocess.CompletedProcess([], 0, "", ""))
    result = install_cdb_windows(dry_run=False)
    assert result.status == "installed"

    monkeypatch.setattr(
        setup, "_run", lambda cmd: subprocess.CompletedProcess([], 1, "", "sdk error")
    )
    result = install_cdb_windows(dry_run=False)
    assert result.status == "failed"


def test_install_for_dispatch(monkeypatch):
    monkeypatch.setattr(setup, "install_netcoredbg", lambda dry: Result("netcoredbg", "dryrun", ""))
    assert install_for("netcoredbg", "linux", True).kind == "netcoredbg"

    monkeypatch.setattr(
        setup, "install_native_linux", lambda kind, dry: Result(kind, "installed", "")
    )
    assert install_for("gdb", "linux", False).kind == "gdb"

    monkeypatch.setattr(setup, "install_lldb_macos", lambda dry: Result("lldb", "installed", ""))
    assert install_for("lldb", "darwin", False).kind == "lldb"

    monkeypatch.setattr(setup, "install_cdb_windows", lambda dry: Result("cdb", "installed", ""))
    assert install_for("cdb", "windows", False).kind == "cdb"

    monkeypatch.setattr(setup, "install_lldb_windows", lambda dry: Result("lldb", "installed", ""))
    assert install_for("lldb", "windows", False).kind == "lldb"

    assert install_for("foo", "unknown_os", False).status == "failed"


def test_extract_archive(tmp_path: Path):
    dest_zip = tmp_path / "zip_out"
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.txt", "hello zip")
    _extract_archive(zip_path, dest_zip)
    assert (dest_zip / "test.txt").read_text() == "hello zip"

    dest_tar = tmp_path / "tar_out"
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="test2.txt")
        info.size = len(b"hello tar")
        tf.addfile(info, io.BytesIO(b"hello tar"))
    _extract_archive(tar_path, dest_tar)
    assert (dest_tar / "test2.txt").read_text() == "hello tar"
