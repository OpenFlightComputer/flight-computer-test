from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fc_test.external_tools import CommandResult
from fc_test.firmware import FirmwareBuildError, build_firmware


class FirmwareBuildTests(unittest.TestCase):
    def test_build_configures_then_builds_and_returns_expected_elf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository_root = Path(directory)
            source = repository_root / "firmware/manufacturing_test"
            source.mkdir(parents=True)
            (source / "CMakePresets.json").write_text("{}", encoding="utf-8")
            calls: list[tuple[tuple[str, ...], Path | None, float]] = []

            def run_command(arguments, *, cwd=None, timeout_seconds):
                command = tuple(arguments)
                calls.append((command, cwd, timeout_seconds))
                if command[1:3] == ("--build", "--preset"):
                    elf = (
                        source
                        / "build/release/openflightcomputer-manufacturing-test.elf"
                    )
                    elf.parent.mkdir(parents=True)
                    elf.write_bytes(b"ELF")
                return CommandResult(command, 0, "", "")

            artifact = build_firmware(
                "release",
                repository_root=repository_root,
                command_runner=run_command,
                executable_locator=lambda name: f"/tools/{name}",
            )

        self.assertEqual(artifact.profile, "release")
        self.assertEqual(
            artifact.elf_path.name, "openflightcomputer-manufacturing-test.elf"
        )
        self.assertEqual(
            [call[0] for call in calls],
            [
                ("/tools/cmake", "--preset", "firmware-release"),
                ("/tools/cmake", "--build", "--preset", "firmware-release"),
            ],
        )
        self.assertTrue(all(call[1] == source for call in calls))

    def test_missing_cmake_has_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "firmware/manufacturing_test"
            source.mkdir(parents=True)
            (source / "CMakePresets.json").write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(FirmwareBuildError, "brew install cmake"):
                build_firmware(
                    repository_root=Path(directory),
                    executable_locator=lambda _name: None,
                )

    def test_configuration_failure_includes_tool_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "firmware/manufacturing_test"
            source.mkdir(parents=True)
            (source / "CMakePresets.json").write_text("{}", encoding="utf-8")

            def fail(arguments, *, cwd=None, timeout_seconds):
                return CommandResult(tuple(arguments), 1, "", "missing submodule")

            with self.assertRaisesRegex(FirmwareBuildError, "missing submodule"):
                build_firmware(
                    repository_root=Path(directory),
                    command_runner=fail,
                    executable_locator=lambda name: f"/tools/{name}",
                )

    def test_missing_expected_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "firmware/manufacturing_test"
            source.mkdir(parents=True)
            (source / "CMakePresets.json").write_text("{}", encoding="utf-8")

            def succeed(arguments, *, cwd=None, timeout_seconds):
                return CommandResult(tuple(arguments), 0, "", "")

            with self.assertRaisesRegex(FirmwareBuildError, "expected ELF"):
                build_firmware(
                    repository_root=Path(directory),
                    command_runner=succeed,
                    executable_locator=lambda name: f"/tools/{name}",
                )


if __name__ == "__main__":
    unittest.main()
