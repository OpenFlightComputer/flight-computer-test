"""Command-line entry point for the OpenFlightComputer board tester."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and hand the validated request to the central runner."""

    arguments = build_parser().parse_args(argv)
    return run(arguments.config)


if __name__ == "__main__":
    raise SystemExit(main())
