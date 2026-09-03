from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from fc_test.firmware import FirmwareArtifact
from fc_test.flashing.programmer import Probe, ProgrammingError
from fc_test.flashing.workflow import FlashOutcome
from fc_test.main import main
from fc_test.protocol.connection import SerialPort, UsbDiscoveryError
from fc_test.protocol.messages import (
    ComponentTestCompletion,
    DeviceMetadata,
    FirmwareMetadata,
    StartTestResponse,
)
from fc_test.protocol.messages import ProtocolMessageError
from fc_test.runner import run
from fc_test.summary import TestOutcome as ComponentOutcome
from fc_test.tests.base import GenericComponentTestHandler


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CURRENT_TEST_CONFIG = REPOSITORY_ROOT / "configs/test/test-config-v006.json"


class RunnerTests(unittest.TestCase):
    def test_cli_forwards_explicit_usb_port(self) -> None:
        with patch("fc_test.main.run", return_value=0) as runner:
            exit_code = main(
                [
                    "run",
                    "--config",
                    str(CURRENT_TEST_CONFIG),
                    "--port",
                    "/dev/cu.explicit",
                ]
            )

        self.assertEqual(exit_code, 0)
        runner.assert_called_once_with(
            CURRENT_TEST_CONFIG,
            firmware_profile="release",
            probe_serial=None,
            programmer_path=None,
            port="/dev/cu.explicit",
        )

    def test_run_prints_loaded_configuration_summary(self) -> None:
        stdout = io.StringIO()
        workflow_calls: list[tuple[str, str | None, Path | None]] = []
        summary_calls: list[tuple[tuple[ComponentOutcome, ...], bool]] = []

        def workflow(profile, *, probe_serial=None, programmer_path=None):
            workflow_calls.append((profile, probe_serial, programmer_path))
            return FlashOutcome(
                artifact=FirmwareArtifact(
                    profile=profile,
                    elf_path=Path("/build/manufacturing-test.elf"),
                ),
                probe=Probe("ABC123"),
            )

        @contextmanager
        def usb_connection(requested_port=None):
            self.assertIsNone(requested_port)
            connection = type(
                "Connection",
                (),
                {"port": SerialPort("/dev/cu.usbmodem-test", 0xCAFE, 0x4001)},
            )()
            yield connection

        with redirect_stdout(stdout):
            exit_code = run(
                CURRENT_TEST_CONFIG,
                firmware_workflow=workflow,
                usb_connection_workflow=usb_connection,
                start_test_workflow=lambda _connection, *, test_uuid: StartTestResponse(
                    command_id=1,
                    device=DeviceMetadata(
                        uid="00112233445566778899AABB",
                        mcu="STM32F405RGT6",
                        board_id="flightcomputer-v1",
                        board_name="Flight Computer V1",
                        board_revision="1.7",
                    ),
                    firmware=FirmwareMetadata("0.1.0", "revision"),
                    capabilities=(
                        "status_led_red",
                        "status_led_green",
                        "rgb_led",
                        "imu",
                        "barometer",
                        "sd_card",
                    ),
                ),
                initial_report_writer=lambda _configurations, _response: Path(
                    "/results/session.json"
                ),
                session_validation_writer=lambda _report_path, _validation: None,
                component_test_workflow=lambda _connection, *, command_id, test_type, on_event: ComponentTestCompletion(
                    command_id, test_type, "passed"
                ),
                handler_factory=lambda _test_type: GenericComponentTestHandler(
                    output=lambda _message: None
                ),
                component_result_writer=lambda *_arguments, **_keywords: None,
                component_run_finalizer=lambda *_arguments, **_keywords: None,
                summary_writer=lambda _definitions, outcomes, *, completed: summary_calls.append(
                    (outcomes, completed)
                ),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(workflow_calls, [("release", None, None)])
        self.assertEqual(
            summary_calls,
            [
                (
                    (
                        ComponentOutcome("rgb_led", "passed"),
                        ComponentOutcome("imu", "passed"),
                        ComponentOutcome("barometer", "passed"),
                        ComponentOutcome("sd_card", "passed"),
                    ),
                    True,
                )
            ],
        )
        self.assertEqual(
            stdout.getvalue(),
            "OpenFlightComputer Hardware Test\n"
            "\n"
            "Board:\n"
            "Flight Computer V1\n"
            "\n"
            "Revision:\n"
            "1.7\n"
            "\n"
            "MCU:\n"
            "STM32F405RGT6\n"
            "\n"
            "Test Configuration:\n"
            "Flight Computer V1 Accepted Hardware\n"
            "\n"
            "UUID:\n"
            "9c7d5a34-1e2b-4f68-9a70-2bc1d3e4f506\n"
            "\n"
            "Configured test order:\n"
            "\n"
            "1. rgb_led\n"
            "2. imu\n"
            "3. barometer\n"
            "4. sd_card\n"
            "\n"
            "Building and flashing firmware (Release)...\n"
            "Firmware: /build/manufacturing-test.elf\n"
            "ST-Link: ABC123\n"
            "Programming, verification, and reset completed.\n"
            "Waiting for USB CDC device...\n"
            "USB CDC: /dev/cu.usbmodem-test\n"
            "Requesting START_TEST metadata...\n"
            "Test run created: /results/session.json\n"
            "Session initialized and validated.\n",
        )

    def test_run_forwards_explicit_port_and_reports_usb_error(self) -> None:
        stderr = io.StringIO()
        requested_ports: list[str | Path | None] = []

        def workflow(profile, *, probe_serial=None, programmer_path=None):
            return FlashOutcome(
                artifact=FirmwareArtifact(profile, Path("/build/firmware.elf")),
                probe=Probe("ABC123"),
            )

        @contextmanager
        def fail_usb(requested_port=None):
            requested_ports.append(requested_port)
            raise UsbDiscoveryError("requested port did not appear")
            yield  # pragma: no cover

        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            exit_code = run(
                CURRENT_TEST_CONFIG,
                port="/dev/cu.explicit",
                firmware_workflow=workflow,
                usb_connection_workflow=fail_usb,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(requested_ports, ["/dev/cu.explicit"])
        self.assertEqual(stderr.getvalue(), "fc-test: requested port did not appear\n")

    def test_run_does_not_create_report_when_start_test_fails(self) -> None:
        report_calls: list[object] = []

        def workflow(profile, *, probe_serial=None, programmer_path=None):
            return FlashOutcome(
                artifact=FirmwareArtifact(profile, Path("/build/firmware.elf")),
                probe=Probe("ABC123"),
            )

        @contextmanager
        def usb_connection(requested_port=None):
            yield type(
                "Connection",
                (),
                {"port": SerialPort("/dev/cu.board", 0xCAFE, 0x4001)},
            )()

        def fail_start(_connection, *, test_uuid):
            raise ProtocolMessageError("device rejected START_TEST")

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            exit_code = run(
                CURRENT_TEST_CONFIG,
                firmware_workflow=workflow,
                usb_connection_workflow=usb_connection,
                start_test_workflow=fail_start,
                initial_report_writer=lambda *_arguments: report_calls.append(True),
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(report_calls, [])

    def test_run_records_then_stops_on_session_validation_failure(self) -> None:
        stderr = io.StringIO()
        validation_updates: list[object] = []

        def workflow(profile, *, probe_serial=None, programmer_path=None):
            return FlashOutcome(
                artifact=FirmwareArtifact(profile, Path("/build/firmware.elf")),
                probe=Probe("ABC123"),
            )

        @contextmanager
        def usb_connection(requested_port=None):
            yield type(
                "Connection",
                (),
                {"port": SerialPort("/dev/cu.board", 0xCAFE, 0x4001)},
            )()

        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            exit_code = run(
                CURRENT_TEST_CONFIG,
                firmware_workflow=workflow,
                usb_connection_workflow=usb_connection,
                start_test_workflow=lambda _connection, *, test_uuid: StartTestResponse(
                    command_id=1,
                    device=DeviceMetadata(
                        uid="00112233445566778899AABB",
                        mcu="STM32F405RGT6",
                        board_id="flightcomputer-v1",
                        board_name="Flight Computer V1",
                        board_revision="1.7",
                    ),
                    firmware=FirmwareMetadata("0.1.0", "revision"),
                    capabilities=(),
                ),
                initial_report_writer=lambda _configurations, _response: Path(
                    "/results/session.json"
                ),
                session_validation_writer=lambda _report_path, validation: validation_updates.append(
                    validation
                ),
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(len(validation_updates), 1)
        self.assertIn("firmware is missing board capability", stderr.getvalue())

    def test_run_reports_programming_error_without_traceback(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        def fail(_profile, *, probe_serial=None, programmer_path=None):
            raise ProgrammingError("no ST-Link probe detected")

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = run(CURRENT_TEST_CONFIG, firmware_workflow=fail)

        self.assertEqual(exit_code, 1)
        self.assertIn("Building and flashing firmware", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "fc-test: no ST-Link probe detected\n")
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_run_reports_configuration_error_without_traceback(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            invalid_config = Path(directory) / "invalid.json"
            invalid_config.write_text("{}", encoding="utf-8")

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = run(invalid_config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("test config is missing required field(s)", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
