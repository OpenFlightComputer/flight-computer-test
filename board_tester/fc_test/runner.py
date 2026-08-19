"""Central board-test workflow boundary.

The runner will own the complete computer-side sequence: configuration loading,
preflight checks, firmware flashing, connection setup, session initialization,
capability validation, ordered component dispatch, and report finalization.

Session initialization includes the ``START_TEST`` exchange and validation of
device UID, MCU, board, firmware, and capability metadata. That information is
not a component test and must be persisted before test dispatch begins.

Component-specific interaction and acceptance logic belongs in ``fc_test.tests``.
"""

from pathlib import Path


def run(configuration_path: Path) -> int:
    """Print the Milestone 2 startup summary for a validated configuration path."""

    print("OpenFlightComputer Hardware Test")
    print()
    print("Test configuration:")
    print(configuration_path)
    return 0
