from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fc_test.external_tools import CommandResult
from fc_test.firmware import FirmwareArtifact
from fc_test.flashing.programmer import Probe, ProgrammingError, flash_firmware
from fc_test.flashing.stlink import (
    Stm32CubeProgrammer,
    locate_stm32cubeprogrammer,
)
from fc_test.flashing.workflow import build_and_flash_firmware


class FakeProgrammer:
    def __init__(self, probes: tuple[Probe, ...], events: list[str] | None = None):
        self.probes = probes
        self.events = events if events is not None else []

    def discover_probes(self) -> tuple[Probe, ...]:
        self.events.append("discover")
        return self.probes

    def program_and_verify(self, probe: Probe, firmware_path: Path) -> None:
        self.events.append(f"program:{probe.serial_number}:{firmware_path.name}")

    def reset(self, probe: Probe) -> None:
        self.events.append(f"reset:{probe.serial_number}")


class ProgrammerWorkflowTests(unittest.TestCase):
    def test_program_verify_precedes_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "firmware.elf"
            firmware.write_bytes(b"ELF")
            events: list[str] = []
            programmer = FakeProgrammer((Probe("ABC123"),), events)

            selected = flash_firmware(programmer, firmware)

        self.assertEqual(selected.serial_number, "ABC123")
        self.assertEqual(
            events,
            ["discover", "program:ABC123:firmware.elf", "reset:ABC123"],
        )

    def test_no_probe_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "firmware.elf"
            firmware.write_bytes(b"ELF")
            with self.assertRaisesRegex(ProgrammingError, "no ST-Link probe"):
                flash_firmware(FakeProgrammer(()), firmware)

    def test_multiple_probes_require_serial_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "firmware.elf"
            firmware.write_bytes(b"ELF")
            programmer = FakeProgrammer((Probe("ONE"), Probe("TWO")))

            with self.assertRaisesRegex(ProgrammingError, "ONE, TWO"):
                flash_firmware(programmer, firmware)

            selected = flash_firmware(
                programmer, firmware, requested_serial="TWO"
            )

        self.assertEqual(selected.serial_number, "TWO")

    def test_programming_failure_prevents_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "firmware.elf"
            firmware.write_bytes(b"ELF")
            events: list[str] = []

            class FailingProgrammer(FakeProgrammer):
                def program_and_verify(self, probe, firmware_path):
                    events.append("program")
                    raise ProgrammingError("verification failed")

            with self.assertRaisesRegex(ProgrammingError, "verification failed"):
                flash_firmware(
                    FailingProgrammer((Probe("ABC123"),), events), firmware
                )

        self.assertEqual(events, ["discover", "program"])

    def test_shared_workflow_builds_before_flashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "firmware.elf"
            events: list[str] = []

            def build(profile):
                events.append(f"build:{profile}")
                firmware.write_bytes(b"ELF")
                return FirmwareArtifact(profile=profile, elf_path=firmware)

            programmer = FakeProgrammer((Probe("ABC123"),), events)

            def create_programmer(path):
                events.append(f"programmer:{path}")
                return programmer

            outcome = build_and_flash_firmware(
                programmer_path=Path("/custom/STM32_Programmer_CLI"),
                firmware_builder=build,
                programmer_factory=create_programmer,
            )

        self.assertEqual(outcome.artifact.elf_path, firmware)
        self.assertEqual(outcome.probe.serial_number, "ABC123")
        self.assertEqual(
            events,
            [
                "build:release",
                "programmer:/custom/STM32_Programmer_CLI",
                "discover",
                "program:ABC123:firmware.elf",
                "reset:ABC123",
            ],
        )

    def test_explicit_firmware_path_bypasses_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "supplied.elf"
            firmware.write_bytes(b"ELF")
            programmer = FakeProgrammer((Probe("ABC123"),))

            def unexpected_build(_profile):
                self.fail("explicit firmware path must bypass the build")

            outcome = build_and_flash_firmware(
                firmware_path=firmware,
                firmware_builder=unexpected_build,
                programmer_factory=lambda _path: programmer,
            )

        self.assertEqual(outcome.artifact.elf_path, firmware.resolve())


class Stm32CubeProgrammerTests(unittest.TestCase):
    def test_locator_prefers_command_line_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            override = Path(directory) / "custom-programmer"
            environment = Path(directory) / "environment-programmer"
            override.write_bytes(b"tool")
            environment.write_bytes(b"tool")
            override.chmod(0o755)
            environment.chmod(0o755)

            located = locate_stm32cubeprogrammer(
                override=override,
                executable_locator=lambda _name: None,
                environment={"STM32CUBE_PROGRAMMER_CLI": str(environment)},
            )

        self.assertEqual(located, override.resolve())

    def test_invalid_command_line_override_does_not_fall_back(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = Path(directory) / "environment-programmer"
            environment.write_bytes(b"tool")
            environment.chmod(0o755)

            with self.assertRaisesRegex(ProgrammingError, "not an executable file"):
                locate_stm32cubeprogrammer(
                    override=Path(directory) / "missing-programmer",
                    environment={"STM32CUBE_PROGRAMMER_CLI": str(environment)},
                )

    def test_locator_prefers_explicit_environment_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "STM32_Programmer_CLI"
            executable.write_bytes(b"tool")
            executable.chmod(0o755)

            located = locate_stm32cubeprogrammer(
                executable_locator=lambda _name: None,
                environment={"STM32CUBE_PROGRAMMER_CLI": str(executable)},
            )

        self.assertEqual(located, executable.resolve())

    def test_locator_reports_missing_programmer(self) -> None:
        with self.assertRaisesRegex(ProgrammingError, "was not found"):
            locate_stm32cubeprogrammer(
                executable_locator=lambda _name: None,
                environment={},
                application_candidates=(),
            )

    def test_list_output_is_parsed_and_duplicates_are_removed(self) -> None:
        output = """
        ST-Link Probe 0 :
          ST-LINK SN  : 066EFF313736504157095133
        ST-Link Probe 1 :
          ST-LINK SN: AABBCCDD
          ST-LINK SN: AABBCCDD
        """

        def run(arguments, *, cwd=None, timeout_seconds):
            return CommandResult(tuple(arguments), 0, output, "")

        programmer = Stm32CubeProgrammer(Path("/tools/programmer"), command_runner=run)

        self.assertEqual(
            programmer.discover_probes(),
            (Probe("066EFF313736504157095133"), Probe("AABBCCDD")),
        )

    def test_program_and_reset_commands_select_probe_and_use_swd(self) -> None:
        calls: list[tuple[str, ...]] = []

        def run(arguments, *, cwd=None, timeout_seconds):
            calls.append(tuple(arguments))
            return CommandResult(tuple(arguments), 0, "", "")

        programmer = Stm32CubeProgrammer(Path("/tools/programmer"), command_runner=run)
        probe = Probe("ABC123")
        firmware = Path("/firmware/test.elf")
        programmer.program_and_verify(probe, firmware)
        programmer.reset(probe)

        self.assertEqual(
            calls[0],
            (
                "/tools/programmer",
                "-c",
                "port=SWD",
                "sn=ABC123",
                "mode=UR",
                "freq=1000",
                "-d",
                "/firmware/test.elf",
                "-v",
            ),
        )
        self.assertEqual(calls[1][-1], "-rst")

    def test_programming_failure_does_not_hide_programmer_output(self) -> None:
        def run(arguments, *, cwd=None, timeout_seconds):
            return CommandResult(tuple(arguments), 1, "No STM32 target found", "")

        programmer = Stm32CubeProgrammer(Path("/tools/programmer"), command_runner=run)
        with self.assertRaisesRegex(ProgrammingError, "No STM32 target found"):
            programmer.program_and_verify(Probe("ABC123"), Path("firmware.elf"))


if __name__ == "__main__":
    unittest.main()
