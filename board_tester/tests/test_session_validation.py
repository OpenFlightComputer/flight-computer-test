from __future__ import annotations

import unittest
from pathlib import Path

from fc_test.configuration import load_configurations
from fc_test.protocol.messages import (
    DeviceMetadata,
    FirmwareMetadata,
    StartTestResponse,
)
from fc_test.session_validation import validate_session


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INITIAL_TEST_CONFIG = REPOSITORY_ROOT / "configs/test/test-config-v001.json"


def response(*, mcu: str = "STM32F405RGT6", capabilities: tuple[str, ...]) -> StartTestResponse:
    return StartTestResponse(
        command_id=1,
        device=DeviceMetadata(
            uid="00112233445566778899AABB",
            mcu=mcu,
            board_id="flightcomputer-v1",
            board_name="Flight Computer V1",
            board_revision="1.7",
        ),
        firmware=FirmwareMetadata("0.1.0", "revision"),
        capabilities=capabilities,
    )


class SessionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configurations = load_configurations(INITIAL_TEST_CONFIG)
        self.required_capabilities = self.configurations.board.test_capabilities

    def test_matching_board_and_firmware_capabilities_pass(self) -> None:
        validation = validate_session(
            self.configurations,
            response(capabilities=self.required_capabilities + ("future_test",)),
        )

        self.assertTrue(validation.passed)
        self.assertEqual(validation.failures, ())

    def test_missing_board_capability_fails_but_extra_firmware_capabilities_are_allowed(self) -> None:
        validation = validate_session(
            self.configurations,
            response(capabilities=("mcu_runtime", "future_test")),
        )

        self.assertFalse(validation.passed)
        self.assertEqual(
            validation.failures,
            (
                "firmware is missing board capability/capabilities: "
                "status_leds, rgb_led, imu, barometer, sd_card",
            ),
        )

    def test_identity_mismatch_fails(self) -> None:
        validation = validate_session(
            self.configurations,
            response(mcu="STM32F411CEU6", capabilities=self.required_capabilities),
        )

        self.assertFalse(validation.passed)
        self.assertEqual(
            validation.failures,
            ("MCU mismatch: expected STM32F405RGT6, received STM32F411CEU6",),
        )


if __name__ == "__main__":
    unittest.main()
