"""Shared firmware preparation and flashing workflow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fc_test.firmware import FirmwareArtifact, FirmwareProfile, build_firmware
from fc_test.flashing.programmer import Probe, Programmer, flash_firmware
from fc_test.flashing.stlink import Stm32CubeProgrammer


FirmwareBuilder = Callable[[FirmwareProfile], FirmwareArtifact]
ProgrammerFactory = Callable[[Path | None], Programmer]


@dataclass(frozen=True, slots=True)
class FlashOutcome:
    """Artifact and probe identities from a successful workflow."""

    artifact: FirmwareArtifact
    probe: Probe


def build_and_flash_firmware(
    profile: FirmwareProfile = "release",
    *,
    firmware_path: Path | None = None,
    probe_serial: str | None = None,
    programmer_path: Path | None = None,
    firmware_builder: FirmwareBuilder = build_firmware,
    programmer_factory: ProgrammerFactory = Stm32CubeProgrammer.create,
) -> FlashOutcome:
    """Build by default, then program, verify, and reset through one probe."""

    if firmware_path is None:
        artifact = firmware_builder(profile)
    else:
        artifact = FirmwareArtifact(profile=profile, elf_path=firmware_path.resolve())

    programmer = programmer_factory(programmer_path)
    probe = flash_firmware(
        programmer,
        artifact.elf_path,
        requested_serial=probe_serial,
    )
    return FlashOutcome(artifact=artifact, probe=probe)
