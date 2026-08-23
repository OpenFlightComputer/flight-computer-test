"""Map configured component-test types to tester-side handlers."""

from fc_test.tests.rgb_led.handler import RgbLedTestHandler
from fc_test.tests.imu.handler import ImuTestHandler
from fc_test.tests.barometer.handler import BarometerTestHandler
from fc_test.tests.sd_card.handler import SdCardTestHandler
from fc_test.tests.status_leds.handler import StatusLedTestHandler


_HANDLER_FACTORIES = {
    "status_led_red": lambda: StatusLedTestHandler("red"),
    "status_led_green": lambda: StatusLedTestHandler("green"),
    "rgb_led": RgbLedTestHandler,
    "imu": ImuTestHandler,
    "barometer": BarometerTestHandler,
    "sd_card": SdCardTestHandler,
}


def create_handler(test_type: str):
    """Create the exact implementation registered for a configured test type."""

    try:
        factory = _HANDLER_FACTORIES[test_type]
    except KeyError as error:
        raise ValueError(f"no tester-side handler is registered for {test_type}") from error
    return factory()
