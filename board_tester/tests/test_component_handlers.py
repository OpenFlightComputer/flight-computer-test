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


if __name__ == "__main__":
    unittest.main()
