"""Programmer-neutral manufacturing-firmware flashing workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Probe:
    """One uniquely selectable debug probe."""

    serial_number: str


class ProgrammingError(RuntimeError):
    """Firmware programming could not be completed safely."""


class Programmer(Protocol):
    """Programmer-neutral operations required by the V1 workflow."""

    def discover_probes(self) -> tuple[Probe, ...]: ...

    def program_and_verify(self, probe: Probe, firmware_path: Path) -> None: ...

    def reset(self, probe: Probe) -> None: ...


def flash_firmware(
    programmer: Programmer,
    firmware_path: Path,
    *,
    requested_serial: str | None = None,
) -> Probe:
    """Select one probe, program and verify firmware, then reset the target."""

    if not firmware_path.is_file():
        raise ProgrammingError(f"firmware ELF does not exist: {firmware_path}")

    probes = programmer.discover_probes()
    probe = _select_probe(probes, requested_serial=requested_serial)
    programmer.program_and_verify(probe, firmware_path)
    programmer.reset(probe)
    return probe


def _select_probe(
    probes: tuple[Probe, ...], *, requested_serial: str | None
) -> Probe:
    if requested_serial is not None:
        for probe in probes:
            if probe.serial_number == requested_serial:
                return probe
        available = ", ".join(probe.serial_number for probe in probes) or "none"
        raise ProgrammingError(
            f"requested ST-Link probe was not found: {requested_serial}; "
            f"available probes: {available}"
        )

    if not probes:
        raise ProgrammingError(
            "no ST-Link probe detected; check its USB connection and power"
        )
    if len(probes) > 1:
        serials = ", ".join(probe.serial_number for probe in probes)
        raise ProgrammingError(
            "multiple ST-Link probes detected; select one with "
            f"--probe-serial: {serials}"
        )
    return probes[0]
