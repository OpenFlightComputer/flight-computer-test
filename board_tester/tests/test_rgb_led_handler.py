from __future__ import annotations

import json
import unittest

from fc_test.configuration import TestDefinition
from fc_test.protocol.messages import ComponentTestEvent
from fc_test.tests.rgb_led.handler import RgbLedTestHandler
from fc_test.tests.registry import create_handler


class RgbLedHandlerTests(unittest.TestCase):
    def test_registry_selects_rgb_handler(self) -> None:
        self.assertIsInstance(create_handler("rgb_led"), RgbLedTestHandler)

    def test_turquoise_is_sent_and_enter_means_pass(self) -> None:
        class FakeConnection:
            def __init__(self) -> None:
                self.writes: list[bytes] = []

            def write_line(self, payload: bytes, *, timeout_seconds: float) -> None:
                self.writes.append(payload)

            def read_line(self, *, timeout_seconds: float) -> bytes:
                return (
                    b'{"protocol_version":1,"type":"TEST_STOPPED",'
                    b'"command_id":1002,"test_type":"rgb_led",'
                    b'"status":"stopped"}'
                )

        connection = FakeConnection()
        received_parameters: list[dict[str, int]] = []

        def workflow(
            _connection,
            *,
            command_id,
            test_type,
            parameters,
            on_event,
        ):
            received_parameters.append(parameters)
            return on_event(
                ComponentTestEvent(command_id, test_type, "rgb_colour_active")
            )

        result = RgbLedTestHandler(input_reader=lambda _prompt: "").run(
            connection,
            command_id=2,
            definition=TestDefinition("rgb_led", True, {"colour": "turquoise"}),
            workflow=workflow,
        )

        self.assertEqual(
            received_parameters,
            [{"red": 64, "green": 224, "blue": 208}],
        )
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.details["colour"], "turquoise")
        self.assertEqual(
            json.loads(connection.writes[0])["type"],
            "STOP_COMPONENT_TEST",
        )


if __name__ == "__main__":
    unittest.main()
