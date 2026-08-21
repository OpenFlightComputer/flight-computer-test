"""Map configured component-test types to tester-side handlers."""

from fc_test.tests.base import GenericComponentTestHandler
from fc_test.tests.status_leds.handler import StatusLedTestHandler


def create_handler(test_type: str):
    if test_type == "status_led_red":
        return StatusLedTestHandler("red")
    if test_type == "status_led_green":
        return StatusLedTestHandler("green")
    return GenericComponentTestHandler()
