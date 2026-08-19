"""Small, injectable boundary for running external development tools."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Captured result of one external command."""

    arguments: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class ExternalCommandError(RuntimeError):
    """An external command could not be started or did not finish in time."""


class CommandRunner(Protocol):
    """Injectable command execution contract used by build and flashing code."""

    def __call__(
        self,
        arguments: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout_seconds: float,
    ) -> CommandResult: ...


def run_command(
    arguments: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: float,
) -> CommandResult:
    """Run one command without a shell and capture text output."""

    command = tuple(str(argument) for argument in arguments)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as error:
        raise ExternalCommandError(f"executable was not found: {command[0]}") from error
    except OSError as error:
        raise ExternalCommandError(
            f"could not start {command[0]}: {error.strerror or error}"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise ExternalCommandError(
            f"{command[0]} timed out after {timeout_seconds:g} seconds"
        ) from error

    return CommandResult(
        arguments=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def failure_detail(result: CommandResult) -> str:
    """Return a concise useful detail from a failed command."""

    output = result.stderr.strip() or result.stdout.strip()
    if not output:
        return f"command exited with status {result.returncode}"
    return output
