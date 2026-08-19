"""Central board-test workflow boundary.

The runner will own the complete computer-side sequence: configuration loading,
preflight checks, firmware flashing, connection setup, session initialization,
capability validation, ordered component dispatch, and report finalization.

Session initialization includes the ``START_TEST`` exchange and validation of
device UID, MCU, board, firmware, and capability metadata. That information is
not a component test and must be persisted before test dispatch begins.

Component-specific interaction and acceptance logic belongs in ``fc_test.tests``.
"""

import sys
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol

from fc_test.configuration import ConfigurationError, load_configurations
from fc_test.firmware import FirmwareBuildError, FirmwareProfile
from fc_test.flashing.programmer import ProgrammingError
from fc_test.flashing.workflow import FlashOutcome, build_and_flash_firmware
from fc_test.protocol.connection import (
    UsbCdcConnection,
    UsbTransportError,
    open_usb_cdc,
)


class FirmwareWorkflow(Protocol):
    def __call__(
        self,
        profile: FirmwareProfile,
        *,
        probe_serial: str | None = None,
        programmer_path: Path | None = None,
    ) -> FlashOutcome: ...


class UsbConnectionWorkflow(Protocol):
    def __call__(
        self, requested_port: str | Path | None = None
    ) -> AbstractContextManager[UsbCdcConnection]: ...


def run(
    configuration_path: Path,
    *,
    firmware_profile: FirmwareProfile = "release",
    probe_serial: str | None = None,
    programmer_path: Path | None = None,
    port: str | Path | None = None,
    firmware_workflow: FirmwareWorkflow = build_and_flash_firmware,
    usb_connection_workflow: UsbConnectionWorkflow = open_usb_cdc,
) -> int:
    """Load config, flash the board, and establish its USB CDC transport."""

    try:
        configurations = load_configurations(configuration_path)
    except ConfigurationError as error:
        print(f"fc-test: {error}", file=sys.stderr)
        return 2

    print("OpenFlightComputer Hardware Test")
    print()
    print("Board:")
    print(configurations.board.name)
    print()
    print("Revision:")
    print(configurations.board.revision)
    print()
    print("MCU:")
    print(configurations.board.mcu.model)
    print()
    print("Test Configuration:")
    print(configurations.test.name)
    print()
    print("UUID:")
    print(configurations.test.uuid)
    print()
    print("Configured test order:")
    print()
    for index, test in enumerate(configurations.test.enabled_tests, start=1):
        print(f"{index}. {test.type}")
    print()
    print(
        f"Building and flashing firmware ({firmware_profile.title()})...",
        flush=True,
    )

    try:
        outcome = firmware_workflow(
            firmware_profile,
            probe_serial=probe_serial,
            programmer_path=programmer_path,
        )
    except (FirmwareBuildError, ProgrammingError) as error:
        print(f"fc-test: {error}", file=sys.stderr)
        return 1

    print(f"Firmware: {outcome.artifact.elf_path}")
    print(f"ST-Link: {outcome.probe.serial_number}")
    print("Programming, verification, and reset completed.")

    print("Waiting for USB CDC device...", flush=True)
    try:
        with usb_connection_workflow(port) as connection:
            print(f"USB CDC: {connection.port.device}")
            print("Transport ready.")
    except UsbTransportError as error:
        print(f"fc-test: {error}", file=sys.stderr)
        return 1
    return 0
