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
from pathlib import Path

from fc_test.configuration import ConfigurationError, load_configurations


def run(configuration_path: Path) -> int:
    """Load configuration and print the hardware-free Milestone 3 summary."""

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
    return 0
