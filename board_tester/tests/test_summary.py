from __future__ import annotations

import io
import unittest

from rich.console import Console

from fc_test.configuration import TestDefinition as ComponentDefinition
from fc_test.summary import TestOutcome as ComponentOutcome
from fc_test.summary import print_test_summary


def _definition(test_type: str) -> ComponentDefinition:
    return ComponentDefinition(type=test_type, enabled=True, parameters={})


class SummaryTests(unittest.TestCase):
    def _render(self, outcomes: tuple[ComponentOutcome, ...], *, completed: bool) -> str:
        output = io.StringIO()
        console = Console(
            file=output,
            force_terminal=True,
            color_system="standard",
            no_color=False,
            width=60,
        )
        print_test_summary(
            (
                _definition("status_led_red"),
                _definition("status_led_green"),
                _definition("sd_card"),
            ),
            outcomes,
            completed=completed,
            console=console,
        )
        return output.getvalue()

    def test_completed_failure_shows_each_result_and_red_full_failure(self) -> None:
        rendered = self._render(
            (
                ComponentOutcome("status_led_red", "passed"),
                ComponentOutcome("status_led_green", "failed"),
                ComponentOutcome("sd_card", "passed"),
            ),
            completed=True,
        )

        self.assertIn("Status LED Red", rendered)
        self.assertIn("Status LED Green", rendered)
        self.assertIn("SD Card", rendered)
        self.assertIn("PASS", rendered)
        self.assertIn("FAIL", rendered)
        self.assertIn("FULL TEST:", rendered)
        self.assertRegex(rendered, r"\x1b\[[0-9;]*31m")
        self.assertRegex(rendered, r"\x1b\[[0-9;]*32m")

    def test_interrupted_run_marks_remaining_tests_not_run(self) -> None:
        rendered = self._render(
            (ComponentOutcome("status_led_red", "passed"),),
            completed=False,
        )

        self.assertIn("NOT RUN", rendered)
        self.assertIn("NOT COMPLETED", rendered)
        self.assertRegex(rendered, r"\x1b\[[0-9;]*33m")


if __name__ == "__main__":
    unittest.main()
