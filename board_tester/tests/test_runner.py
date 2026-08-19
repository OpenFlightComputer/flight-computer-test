from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from fc_test.firmware import FirmwareArtifact
from fc_test.flashing.programmer import Probe, ProgrammingError
from fc_test.flashing.workflow import FlashOutcome
from fc_test.runner import run


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INITIAL_TEST_CONFIG = REPOSITORY_ROOT / "configs/test/test-config-v001.json"


class RunnerTests(unittest.TestCase):
    def test_run_prints_loaded_configuration_summary(self) -> None:
        stdout = io.StringIO()
        workflow_calls: list[tuple[str, str | None, Path | None]] = []

        def workflow(profile, *, probe_serial=None, programmer_path=None):
            workflow_calls.append((profile, probe_serial, programmer_path))
            return FlashOutcome(
                artifact=FirmwareArtifact(
                    profile=profile,
                    elf_path=Path("/build/manufacturing-test.elf"),
                ),
                probe=Probe("ABC123"),
            )

        with redirect_stdout(stdout):
            exit_code = run(INITIAL_TEST_CONFIG, firmware_workflow=workflow)

        self.assertEqual(exit_code, 0)
        self.assertEqual(workflow_calls, [("release", None, None)])
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
            "Flight Computer V1 Initial Acceptance\n"
            "\n"
            "UUID:\n"
            "ccc7d571-141e-4054-8e77-6ac3a97ababa\n"
            "\n"
            "Configured test order:\n"
            "\n"
            "1. mcu_runtime\n"
            "2. status_leds\n"
            "3. rgb_led\n"
            "4. imu\n"
            "5. barometer\n"
            "6. sd_card\n"
            "\n"
            "Building and flashing firmware (Release)...\n"
            "Firmware: /build/manufacturing-test.elf\n"
            "ST-Link: ABC123\n"
            "Programming, verification, and reset completed.\n",
        )

    def test_run_reports_programming_error_without_traceback(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        def fail(_profile, *, probe_serial=None, programmer_path=None):
            raise ProgrammingError("no ST-Link probe detected")

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = run(INITIAL_TEST_CONFIG, firmware_workflow=fail)

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
