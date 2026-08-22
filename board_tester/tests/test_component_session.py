from __future__ import annotations

import json
import unittest

from fc_test.protocol.component_session import run_component_test, stop_component_test


class ComponentSessionTests(unittest.TestCase):
    def test_stop_requires_matching_acknowledgement(self) -> None:
        class FakeConnection:
            def write_line(self, payload: bytes, *, timeout_seconds: float) -> None:
                self.payload = payload

            def read_line(self, *, timeout_seconds: float) -> bytes:
                return (
                    b'{"protocol_version":1,"type":"TEST_STOPPED","command_id":17,'
                    b'"test_type":"rgb_led","status":"stopped"}'
                )

        connection = FakeConnection()
        stop_component_test(connection, command_id=17, test_type="rgb_led")

        self.assertEqual(json.loads(connection.payload)["type"], "STOP_COMPONENT_TEST")

    def test_runs_until_completion_and_routes_events(self) -> None:
        class FakeConnection:
            def __init__(self) -> None:
                self.writes: list[bytes] = []
                self.responses = iter(
                    (
                        b'{"protocol_version":1,"type":"TEST_STARTED","command_id":2,'
                        b'"test_type":"rgb_led","status":"running"}',
                        b'{"protocol_version":1,"type":"TEST_EVENT","command_id":2,'
                        b'"test_type":"rgb_led","event":"operator_confirmation_required"}',
                        b'{"protocol_version":1,"type":"TEST_COMPLETED","command_id":2,'
                        b'"test_type":"rgb_led","status":"passed"}',
                    )
                )

            def write_line(self, payload: bytes, *, timeout_seconds: float) -> None:
                self.writes.append(payload)

            def read_line(self, *, timeout_seconds: float) -> bytes:
                return next(self.responses)

        connection = FakeConnection()
        events: list[str] = []
        completion = run_component_test(
            connection, command_id=2, test_type="rgb_led",
            on_event=lambda event: events.append(event.event),
            parameters={"red": 40, "green": 220, "blue": 200},
        )

        self.assertEqual(events, ["operator_confirmation_required"])
        self.assertEqual(completion.status, "passed")
        self.assertEqual(
            json.loads(connection.writes[0])["parameters"],
            {"red": 40, "green": 220, "blue": 200},
        )


if __name__ == "__main__":
    unittest.main()
