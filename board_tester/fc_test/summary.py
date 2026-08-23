"""Terminal presentation for the final component-test outcome."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.text import Text

from fc_test.configuration import TestDefinition


@dataclass(frozen=True, slots=True)
class TestOutcome:
    """One completed component status used by the final summary."""

    test_type: str
    status: str


_DISPLAY_NAMES = {
    "status_led_red": "Status LED Red",
    "status_led_green": "Status LED Green",
    "rgb_led": "RGB LED",
    "imu": "IMU",
    "barometer": "Barometer",
    "sd_card": "SD Card",
}


def print_test_summary(
    definitions: tuple[TestDefinition, ...],
    outcomes: tuple[TestOutcome, ...],
    *,
    completed: bool,
    console: Console | None = None,
) -> None:
    """Print every configured test and the overall board-test outcome."""

    terminal = console or Console(highlight=False)
    results_by_type = {outcome.test_type: outcome.status for outcome in outcomes}
    table = Table(title="Final test summary")
    table.add_column("Test")
    table.add_column("Result", justify="center")

    all_passed = True
    all_ran = True
    for definition in definitions:
        status = results_by_type.get(definition.type)
        if status == "passed":
            result = Text("PASS", style="bold green")
        elif status == "failed":
            result = Text("FAIL", style="bold red")
            all_passed = False
        elif status is None:
            result = Text("NOT RUN", style="bold yellow")
            all_passed = False
            all_ran = False
        else:
            result = Text(status.upper(), style="bold yellow")
            all_passed = False
            all_ran = False
        table.add_row(_DISPLAY_NAMES.get(definition.type, definition.type), result)

    terminal.print()
    terminal.print(table)
    terminal.print()
    if completed and all_ran:
        label = "PASS" if all_passed else "FAIL"
        style = "bold green" if all_passed else "bold red"
    else:
        label = "NOT COMPLETED"
        style = "bold yellow"
    terminal.print(Text.assemble(("FULL TEST: ", "bold"), (label, style)))
