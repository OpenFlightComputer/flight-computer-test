"""Build the manufacturing firmware through the canonical CMake presets."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fc_test.external_tools import (
    CommandRunner,
    ExternalCommandError,
    failure_detail,
    run_command,
)


FirmwareProfile = Literal["debug", "release"]
ExecutableLocator = Callable[[str], str | None]
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class FirmwareArtifact:
    """One successfully built firmware image."""

    profile: FirmwareProfile
    elf_path: Path


class FirmwareBuildError(RuntimeError):
    """The manufacturing firmware could not be built."""


def build_firmware(
    profile: FirmwareProfile = "release",
    *,
    repository_root: Path = REPOSITORY_ROOT,
    command_runner: CommandRunner = run_command,
    executable_locator: ExecutableLocator = shutil.which,
) -> FirmwareArtifact:
    """Configure and incrementally build one firmware profile."""

    if profile not in ("debug", "release"):
        raise FirmwareBuildError(f"unsupported firmware build profile: {profile}")

    source_directory = repository_root / "firmware/manufacturing_test"
    presets_path = source_directory / "CMakePresets.json"
    if not presets_path.is_file():
        raise FirmwareBuildError(
            f"firmware source tree was not found: expected {presets_path}"
        )

    cmake = executable_locator("cmake")
    if cmake is None:
        raise FirmwareBuildError(
            "CMake was not found; install it with `brew install cmake`"
        )
    if executable_locator("ninja") is None:
        raise FirmwareBuildError(
            "Ninja was not found; install it with `brew install ninja`"
        )

    preset = f"firmware-{profile}"
    try:
        configure_result = command_runner(
            (cmake, "--preset", preset),
            cwd=source_directory,
            timeout_seconds=60,
        )
    except ExternalCommandError as error:
        raise FirmwareBuildError(f"firmware configuration failed: {error}") from error
    if configure_result.returncode != 0:
        raise FirmwareBuildError(
            "firmware configuration failed:\n" + failure_detail(configure_result)
        )

    try:
        build_result = command_runner(
            (cmake, "--build", "--preset", preset),
            cwd=source_directory,
            timeout_seconds=300,
        )
    except ExternalCommandError as error:
        raise FirmwareBuildError(f"firmware build failed: {error}") from error
    if build_result.returncode != 0:
        raise FirmwareBuildError(
            "firmware build failed:\n" + failure_detail(build_result)
        )

    elf_path = (
        source_directory
        / "build"
        / profile
        / "openflightcomputer-manufacturing-test.elf"
    )
    if not elf_path.is_file():
        raise FirmwareBuildError(
            f"firmware build completed without producing the expected ELF: {elf_path}"
        )

    return FirmwareArtifact(profile=profile, elf_path=elf_path.resolve())
