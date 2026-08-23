"""Shared metadata for the component tests supported by the board tester."""

TEST_DISPLAY_NAMES = {
    "status_led_red": "Status LED Red",
    "status_led_green": "Status LED Green",
    "rgb_led": "RGB LED",
    "imu": "IMU",
    "barometer": "Barometer",
    "sd_card": "SD Card",
}

SUPPORTED_TEST_TYPES = frozenset(TEST_DISPLAY_NAMES)
