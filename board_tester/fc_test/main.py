"""Command-line entry point for the OpenFlightComputer board tester."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from fc_test.firmware import FirmwareBuildError, FirmwareProfile, build_firmware
from fc_test.flashing.programmer import ProgrammingError
from fc_test.flashing.workflow import build_and_flash_firmware
from fc_test.runner import run


def _configuration_file(value: str) -> Path:
    """Return an existing configuration file path or raise an argparse error."""

    path = Path(value).expanduser()
    if not path.exists():
        raise argparse.ArgumentTypeError(
            f"test configuration does not exist: {value}"
        )
    if not path.is_file():
        raise argparse.ArgumentTypeError(
            f"test configuration is not a file: {value}"
        )
    return path


def _firmware_file(value: str) -> Path:
    """Return an existing ELF path or raise an argparse error."""

    path = Path(value).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"firmware ELF does not exist: {value}")
    if path.suffix.lower() != ".elf":
        raise argparse.ArgumentTypeError(f"firmware file must be an ELF: {value}")
    return path


def _programmer_file(value: str) -> Path:
    """Return an existing programmer executable or raise an argparse error."""

    path = Path(value).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(
            f"STM32CubeProgrammer executable does not exist: {value}"
        )
    return path


def _add_profile_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        choices=("debug", "release"),
        default="release",
        help="firmware build profile (default: release)",
    )


def _add_probe_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--probe-serial",
        metavar="SERIAL",
        help="select one ST-Link when multiple probes are connected",
    )


def _add_programmer_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--programmer",
        type=_programmer_file,
        metavar="PATH",
        help="path to the STM32_Programmer_CLI executable",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the deliberately small V1 command-line interface."""

    parser = argparse.ArgumentParser(
        prog="fc-test",
        description="OpenFlightComputer hardware manufacturing and acceptance test",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser(
        "run",
        help="start a board-test run",
        description="Start a board-test run from a test configuration",
    )
    run_parser.add_argument(
        "--config",
        required=True,
        type=_configuration_file,
        metavar="PATH",
        help="path to an existing test configuration file",
    )
    _add_profile_argument(run_parser)
    _add_probe_argument(run_parser)
    _add_programmer_argument(run_parser)

    firmware_parser = commands.add_parser(
        "firmware",
        help="build or flash manufacturing firmware",
    )
    firmware_commands = firmware_parser.add_subparsers(
        dest="firmware_command", required=True
    )

    firmware_build_parser = firmware_commands.add_parser(
        "build",
        help="build manufacturing firmware",
    )
    _add_profile_argument(firmware_build_parser)

    flash_parser = firmware_commands.add_parser(
        "flash",
        help="build and flash manufacturing firmware",
    )
    _add_profile_argument(flash_parser)
    _add_probe_argument(flash_parser)
    _add_programmer_argument(flash_parser)
    flash_parser.add_argument(
        "--firmware",
        type=_firmware_file,
        metavar="ELF",
        help="flash this prebuilt ELF instead of building the selected profile",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and hand the validated request to the central runner."""

    arguments = build_parser().parse_args(argv)
    profile: FirmwareProfile = arguments.profile

    if arguments.command == "run":
        return run(
            arguments.config,
            firmware_profile=profile,
            probe_serial=arguments.probe_serial,
            programmer_path=arguments.programmer,
        )

    if arguments.firmware_command == "build":
        return _build_firmware_command(profile)
    return _flash_firmware_command(
        profile,
        firmware_path=arguments.firmware,
        probe_serial=arguments.probe_serial,
        programmer_path=arguments.programmer,
    )


def _build_firmware_command(profile: FirmwareProfile) -> int:
    print(f"Building manufacturing firmware ({profile.title()})...", flush=True)
    try:
        artifact = build_firmware(profile)
    except FirmwareBuildError as error:
        print(f"fc-test: {error}", file=sys.stderr)
        return 1
    print(f"Firmware built: {artifact.elf_path}")
    return 0


def _flash_firmware_command(
    profile: FirmwareProfile,
    *,
    firmware_path: Path | None,
    probe_serial: str | None,
    programmer_path: Path | None,
) -> int:
    action = "Flashing supplied manufacturing firmware..."
    if firmware_path is None:
        action = f"Building and flashing manufacturing firmware ({profile.title()})..."
    print(action, flush=True)
    try:
        outcome = build_and_flash_firmware(
            profile,
            firmware_path=firmware_path,
            probe_serial=probe_serial,
            programmer_path=programmer_path,
        )
    except (FirmwareBuildError, ProgrammingError) as error:
        print(f"fc-test: {error}", file=sys.stderr)
        return 1
    print(f"Firmware: {outcome.artifact.elf_path}")
    print(f"ST-Link: {outcome.probe.serial_number}")
    print("Programming, verification, and reset completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
