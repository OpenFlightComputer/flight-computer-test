from __future__ import annotations

import unittest

from fc_test.configuration import TestDefinition
from fc_test.protocol.messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    ProtocolMessageError,
)
from fc_test.tests.barometer.handler import BarometerTestHandler
from fc_test.tests.base import prompt_yes_no
from fc_test.tests.imu.handler import ImuTestHandler
from fc_test.tests.registry import create_handler
from fc_test.tests.sd_card.handler import SdCardTestHandler
from fc_test.tests.status_leds.handler import StatusLedTestHandler
from fc_test.test_catalog import SUPPORTED_TEST_TYPES


class ComponentHandlerTests(unittest.TestCase):
    def test_yes_no_prompt_retries_and_accepts_full_answers(self) -> None:
        answers = iter(("maybe", "yes"))
        output: list[str] = []

        passed = prompt_yes_no(
            "Did it work?",
            input_reader=lambda _prompt: next(answers),
            output=output.append,
        )

        self.assertTrue(passed)
        self.assertEqual(output, ["Please enter Y or n."])

    def test_registry_rejects_missing_handler(self) -> None:
        with self.assertRaisesRegex(ValueError, "no tester-side handler"):
            create_handler("not_implemented")

    def test_every_supported_type_has_a_handler(self) -> None:
        for test_type in SUPPORTED_TEST_TYPES:
            with self.subTest(test_type=test_type):
                self.assertIsNotNone(create_handler(test_type))

    def test_status_led_uses_injected_workflow(self) -> None:
        calls: list[str] = []

        def workflow(
            _connection, *, command_id, test_type, on_event, on_started
        ):
            calls.append(test_type)
            return ComponentTestCompletion(command_id, test_type, "passed")

        result = StatusLedTestHandler("red").run(
            object(),
            command_id=2,
            definition=TestDefinition("status_led_red", True, {}),
            workflow=workflow,
        )

        self.assertEqual(calls, ["status_led_red"])
        self.assertEqual(result.status, "passed")

    def test_sd_card_warns_before_destructive_test(self) -> None:
        output: list[str] = []
        handler = SdCardTestHandler(output=output.append)

        handler.begin(TestDefinition("sd_card", True, {}))

        self.assertEqual(output[0], "Starting automatic SD-card test.")
        self.assertIn("overwrites and clears eight raw sectors", output[1])
        self.assertIn("existing filesystem data may be damaged", output[1])

    def test_imu_rejects_incomplete_sample_shape(self) -> None:
        handler = ImuTestHandler()
        handler.begin(TestDefinition("imu", True, {}))

        with self.assertRaisesRegex(ProtocolMessageError, "gyroscope_raw"):
            handler.record_event(
                ComponentTestEvent(
                    2,
                    "imu",
                    "imu_sample",
                    {"acceleration_raw": {"x": 1, "y": 2, "z": 3}},
                )
            )

    def test_barometer_rejects_non_integer_sample(self) -> None:
        handler = BarometerTestHandler()
        handler.begin(TestDefinition("barometer", True, {}))

        with self.assertRaisesRegex(ProtocolMessageError, "pressure_centi_pa"):
            handler.record_event(
                ComponentTestEvent(
                    2,
                    "barometer",
                    "barometer_sample",
                    {"pressure_centi_pa": 1013.25, "temperature_centi_c": 2200},
                )
            )

    def test_barometer_pressure_delta_is_shown_in_pascals(self) -> None:
        self.assertEqual(
            BarometerTestHandler._delta(10100000, 10099750, "Pa"),
            "+2.50 Pa",
        )

    def test_component_failures_are_printed_and_retained(self) -> None:
        output: list[str] = []
        handler = SdCardTestHandler(output=output.append)
        handler.begin(TestDefinition("sd_card", True, {}))

        handler.handle_event(
            ComponentTestEvent(
                2,
                "sd_card",
                "component_failure",
                {"stage": "cmd0", "reason": "unexpected_response", "code": 255},
            )
        )
        result = handler.finish(ComponentTestCompletion(2, "sd_card", "failed"))

        self.assertIn("CMD0".lower(), output[-1].lower())
        self.assertIn("code 255", output[-1])
        self.assertEqual(result.details["failure"]["stage"], "cmd0")

    def test_imu_uses_independent_physical_scales(self) -> None:
        acceleration = ImuTestHandler._bar(
            16384, counts_per_unit=16384.0, full_scale=1.0, decimals=3
        )
        gyroscope = ImuTestHandler._bar(
            4096, counts_per_unit=16.384, full_scale=250.0, decimals=1
        )

        self.assertIn("+1.000", acceleration)
        self.assertEqual(acceleration.count("█"), 12)
        self.assertIn("+250.0", gyroscope)
        self.assertEqual(gyroscope.count("█"), 12)


if __name__ == "__main__":
    unittest.main()
