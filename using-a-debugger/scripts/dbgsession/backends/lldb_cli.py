"""lldb CLI backend using pipe transport with content-gated async stop detection."""

import contextlib
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backends.base import Backend
from transport import open_transport

_TIMEOUT = 30.0
# lldb, when its stdout is a pipe rather than a terminal, does not print each
# line of a stop notification (the "stopped" line, thread status, frame info,
# source context) as one atomic write - they land in our read queue as a fast
# burst of separate lines. Once no further lines have arrived for this long,
# the burst is done and it is safe to send the next command; this replaces a
# fixed post-stop sleep, which under load was not always long enough to
# outlast the burst and let a written command race lldb's echo of it.
_QUIET_SECONDS = 0.2
_STOP_PATTERN = re.compile(r"stop reason =|Process \d+ exited|exited with status")


def _has_stopped(text: str) -> bool:
    return bool(_STOP_PATTERN.search(text))


def _stopped_and_quiet(idle_seconds: float) -> Callable[[str], bool]:
    """Build a read_until predicate: true once _has_stopped matches AND the
    accumulated text has stopped growing for `idle_seconds`."""
    state = {"stable_since": None, "last_len": -1}

    def predicate(text: str) -> bool:
        if not _has_stopped(text):
            state["last_len"] = len(text)
            state["stable_since"] = None
            return False
        now = time.monotonic()
        if len(text) != state["last_len"]:
            state["last_len"] = len(text)
            state["stable_since"] = now
            return False
        if state["stable_since"] is None:
            state["stable_since"] = now
            return False
        return (now - state["stable_since"]) >= idle_seconds

    return predicate


class LldbCliBackend(Backend):
    def __init__(
        self,
        debugger: str,
        kind: str,
        program: str,
        program_args: list,
        debugger_path: str | None = None,
    ) -> None:
        self._debugger = debugger
        self._kind = kind
        self._program = program
        self._program_args = program_args
        self._debugger_path = debugger_path or "lldb"
        self._transport = None
        self._counter = 0

    def _next_token(self) -> str:
        self._counter += 1
        return f"@@DBG{self._counter}@@"

    def _run_sync(self, command: str) -> str:
        token = self._next_token()
        self._transport.write(command + "\n")
        self._transport.write(f'script print("{token}")\n')
        acc = self._transport.read_until(
            lambda text: any(line.strip() == token for line in text.splitlines()),
            _TIMEOUT,
        )
        lines = acc.splitlines(keepends=True)
        result_lines = [line for line in lines if line.strip() != token]
        return "".join(result_lines)

    def _run_exec(self, command: str) -> str:
        self._transport.write(command + "\n")
        # Wait for the stop line, then for the trailing burst of detail that
        # follows it to go quiet (see _stopped_and_quiet) instead of guessing
        # a fixed delay - writing the next command before that burst has
        # fully arrived races lldb's echo of our input and can corrupt it.
        stop_text = self._transport.read_until(_stopped_and_quiet(_QUIET_SECONDS), _TIMEOUT)
        token = self._next_token()
        self._transport.write(f'script print("{token}")\n')
        drain = self._transport.read_until(
            lambda text: any(line.strip() == token for line in text.splitlines()),
            _TIMEOUT,
        )
        lines = drain.splitlines(keepends=True)
        drain_clean = "".join(line for line in lines if line.strip() != token)
        return stop_text + drain_clean

    def start(self) -> None:
        argv = [self._debugger_path, "--no-use-colors", self._program]
        if self._program_args:
            argv += ["--", *self._program_args]
        self._transport = open_transport(argv, self._kind)
        # Synchronize on the lldb REPL coming up, the same way MiBackend waits
        # for "(gdb)" and CdbBackend waits for its token echo - otherwise the
        # caller's first command can race lldb's startup banner.
        try:
            token = self._next_token()
            self._transport.write(f'script print("{token}")\n')
            self._transport.read_until(
                lambda text: any(line.strip() == token for line in text.splitlines()),
                _TIMEOUT,
            )
        except Exception:
            with contextlib.suppress(OSError):
                self._transport.close()
            self._transport = None
            raise

    def set_breakpoint(self, file: str, line: int) -> str:
        return self._run_sync(f"breakpoint set --file {file} --line {line}")

    def run(self) -> str:
        return self._run_exec("run")

    def cont(self) -> str:
        return self._run_exec("continue")

    def step_over(self) -> str:
        return self._run_exec("next")

    def step_into(self) -> str:
        return self._run_exec("step")

    def read_local(self, name: str) -> str:
        text = self._run_sync(f"frame variable {name}")
        for line in text.splitlines():
            if name in line and " = " in line:
                return line.rsplit(" = ", 1)[-1].strip()
        return ""

    def backtrace(self) -> str:
        return self._run_sync("bt")

    def raw(self, command: str) -> str:
        return self._run_sync(command)

    def stop(self) -> None:
        if self._transport is not None:
            try:
                self._transport.write("process kill\n")
            except OSError as error:
                import sys as _sys

                print(f"stop: process kill write failed: {error}", file=_sys.stderr)
            self._transport.close()
            self._transport = None
