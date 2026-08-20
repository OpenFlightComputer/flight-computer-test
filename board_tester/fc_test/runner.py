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
from fc_test.protocol.messages import ProtocolMessageError, StartTestResponse
from fc_test.protocol.session import FramedConnection, start_test
from fc_test.reporting.json_report import ReportError, create_initial_report
from fc_test.reporting.json_report import record_session_validation
from fc_test.session_validation import SessionValidation, validate_session


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


class StartTestWorkflow(Protocol):
    def __call__(self, connection: FramedConnection, *, test_uuid) -> StartTestResponse: ...


class InitialReportWriter(Protocol):
    def __call__(self, configurations, response: StartTestResponse) -> Path: ...


class SessionValidationWriter(Protocol):
    def __call__(self, report_path: Path, validation: SessionValidation) -> None: ...


def run(
    configuration_path: Path,
    *,
    firmware_profile: FirmwareProfile = "release",
    probe_serial: str | None = None,
    programmer_path: Path | None = None,
    port: str | Path | None = None,
    firmware_workflow: FirmwareWorkflow = build_and_flash_firmware,
    usb_connection_workflow: UsbConnectionWorkflow = open_usb_cdc,
    start_test_workflow: StartTestWorkflow = start_test,
    initial_report_writer: InitialReportWriter = create_initial_report,
    session_validator=validate_session,
    session_validation_writer: SessionValidationWriter = record_session_validation,
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
            print("Requesting START_TEST metadata...", flush=True)
            response = start_test_workflow(
                connection, test_uuid=configurations.test.uuid
            )
            report_path = initial_report_writer(configurations, response)
            validation = session_validator(configurations, response)
            session_validation_writer(report_path, validation)
    except (UsbTransportError, ProtocolMessageError, ReportError) as error:
        print(f"fc-test: {error}", file=sys.stderr)
        return 1
    print(f"Test run created: {report_path}")
    if not validation.passed:
        print(
            "fc-test: session validation failed: " + "; ".join(validation.failures),
            file=sys.stderr,
        )
        return 1
    print("Session initialized and validated.")
    return 0
