"""STM32CubeProgrammer CLI adapter for ST-Link/SWD."""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from fc_test.external_tools import (
    CommandResult,
    CommandRunner,
    ExternalCommandError,
    failure_detail,
    run_command,
)
from fc_test.flashing.programmer import Probe, ProgrammingError


ExecutableLocator = Callable[[str], str | None]
_STLINK_SERIAL_PATTERN = re.compile(r"ST-LINK\s+SN\s*:\s*([0-9A-Za-z]+)", re.I)
_MACOS_APPLICATION = Path(
    "/Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/"
    "STM32CubeProgrammer.app/Contents"
)
_STANDARD_APPLICATION_CANDIDATES = (
    _MACOS_APPLICATION / "MacOs/bin/STM32_Programmer_CLI",
    _MACOS_APPLICATION / "Resources/bin/STM32_Programmer_CLI",
)


def locate_stm32cubeprogrammer(
    *,
    override: Path | None = None,
    executable_locator: ExecutableLocator = shutil.which,
    environment: Mapping[str, str] = os.environ,
    application_candidates: Sequence[Path] = _STANDARD_APPLICATION_CANDIDATES,
) -> Path:
    """Locate the official programmer without changing the user's PATH."""

    if override is not None:
        explicit = override.expanduser()
        if explicit.is_file() and os.access(explicit, os.X_OK):
            return explicit.resolve()
        raise ProgrammingError(
            f"configured STM32CubeProgrammer CLI is not an executable file: {override}"
        )

    configured = environment.get("STM32CUBE_PROGRAMMER_CLI")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())

    on_path = executable_locator("STM32_Programmer_CLI")
    if on_path:
        candidates.append(Path(on_path))

    candidates.extend(application_candidates)

    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()

    raise ProgrammingError(
        "STM32CubeProgrammer CLI was not found; install STM32CubeProgrammer or "
        "set STM32CUBE_PROGRAMMER_CLI to its executable"
    )


class Stm32CubeProgrammer:
    """Program and reset STM32 targets through the official ST CLI."""

    def __init__(
        self,
        executable: Path,
        *,
        command_runner: CommandRunner = run_command,
        swd_frequency_khz: int = 1000,
    ) -> None:
        self._executable = executable
        self._command_runner = command_runner
        self._swd_frequency_khz = swd_frequency_khz

    @classmethod
    def create(cls, executable: Path | None = None) -> "Stm32CubeProgrammer":
        """Create an adapter using the installed programmer."""

        return cls(locate_stm32cubeprogrammer(override=executable))

    def discover_probes(self) -> tuple[Probe, ...]:
        result = self._run((str(self._executable), "--list"), timeout_seconds=30)
        if result.returncode != 0:
            raise ProgrammingError(
                "could not list ST-Link probes:\n" + failure_detail(result)
            )

        serials = dict.fromkeys(_STLINK_SERIAL_PATTERN.findall(result.stdout))
        return tuple(Probe(serial_number=serial) for serial in serials)

    def program_and_verify(self, probe: Probe, firmware_path: Path) -> None:
        result = self._run(
            (
                str(self._executable),
                "-c",
                "port=SWD",
                f"sn={probe.serial_number}",
                "mode=UR",
                f"freq={self._swd_frequency_khz}",
                "-d",
                str(firmware_path),
                "-v",
            ),
            timeout_seconds=120,
        )
        if result.returncode != 0:
            raise ProgrammingError(
                f"programming or verification failed for ST-Link "
                f"{probe.serial_number}:\n{failure_detail(result)}"
            )

    def reset(self, probe: Probe) -> None:
        result = self._run(
            (
                str(self._executable),
                "-c",
                "port=SWD",
                f"sn={probe.serial_number}",
                "mode=UR",
                f"freq={self._swd_frequency_khz}",
                "-rst",
            ),
            timeout_seconds=30,
        )
        if result.returncode != 0:
            raise ProgrammingError(
                f"firmware was verified but reset failed for ST-Link "
                f"{probe.serial_number}:\n{failure_detail(result)}"
            )

    def _run(
        self, arguments: tuple[str, ...], *, timeout_seconds: float
    ) -> CommandResult:
        try:
            return self._command_runner(
                arguments, cwd=None, timeout_seconds=timeout_seconds
            )
        except ExternalCommandError as error:
            raise ProgrammingError(str(error)) from error
