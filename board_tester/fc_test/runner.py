"""Central board-test workflow boundary.

The runner will own the complete computer-side sequence: configuration loading,
preflight checks, firmware flashing, connection setup, session initialization,
capability validation, ordered component dispatch, and report finalization.

Session initialization includes the ``START_TEST`` exchange and validation of
device UID, MCU, board, firmware, and capability metadata. That information is
not a component test and must be persisted before test dispatch begins.

Component-specific interaction and acceptance logic belongs in ``fc_test.tests``.
"""

