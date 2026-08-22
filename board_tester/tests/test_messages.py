from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fc_test.configuration import load_configurations
from fc_test.protocol.messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    DeviceMetadata,
    FirmwareMetadata,
    ProtocolMessageError,
    StartTestResponse,
    decode_start_test_response,
    decode_component_test_message,
    encode_run_component_test,
    encode_start_test,
)
from fc_test.protocol.session import start_test
from fc_test.reporting.json_report import create_initial_report, record_session_validation
from fc_test.session_validation import SessionValidation


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INITIAL_TEST_CONFIG = REPOSITORY_ROOT / "configs/test/test-config-v001.json"


def response_line(*, command_id: int = 1) -> bytes:
    return json.dumps(
        {
            "protocol_version": 1,
            "type": "START_TEST_RESPONSE",
            "command_id": command_id,
            "status": "ok",
            "device": {
                "uid": "00112233445566778899AABB",
                "mcu": "STM32F405RGT6",
                "board_id": "flightcomputer-v1",
                "board_name": "Flight Computer V1",
                "board_revision": "1.7",
            },
            "firmware": {"version": "0.1.0", "git_revision": "abc123"},
            "capabilities": [],
        },
        separators=(",", ":"),
    ).encode()


class MessageTests(unittest.TestCase):
    def test_component_lifecycle_messages_are_correlated(self) -> None:
        encoded = encode_run_component_test(command_id=2, test_type="rgb_led")
        event = decode_component_test_message(
            b'{"protocol_version":1,"type":"TEST_EVENT","command_id":2,'
            b'"test_type":"rgb_led","event":"operator_confirmation_required"}',
            expected_command_id=2,
            expected_test_type="rgb_led",
        )
        completion = decode_component_test_message(
            b'{"protocol_version":1,"type":"TEST_COMPLETED","command_id":2,'
            b'"test_type":"rgb_led","status":"passed"}',
            expected_command_id=2,
            expected_test_type="rgb_led",
        )

        self.assertEqual(json.loads(encoded)["type"], "RUN_COMPONENT_TEST")
        self.assertIsInstance(event, ComponentTestEvent)
        self.assertEqual(event.event, "operator_confirmation_required")
        self.assertEqual(completion, ComponentTestCompletion(2, "rgb_led", "passed"))

    def test_rgb_parameters_are_encoded_as_raw_bytes(self) -> None:
        encoded = encode_run_component_test(
            command_id=2,
            test_type="rgb_led",
            parameters={"red": 40, "green": 220, "blue": 200},
        )

        self.assertEqual(
            json.loads(encoded)["parameters"],
            {"red": 40, "green": 220, "blue": 200},
        )

    def test_rgb_parameters_reject_values_outside_one_byte(self) -> None:
        with self.assertRaisesRegex(ValueError, "0 through 255"):
            encode_run_component_test(
                command_id=2,
                test_type="rgb_led",
                parameters={"red": 256, "green": 220, "blue": 200},
            )

    def test_start_test_request_has_the_protocol_contract(self) -> None:
        test_uuid = UUID("ccc7d571-141e-4054-8e77-6ac3a97ababa")

        encoded = encode_start_test(command_id=1, test_uuid=test_uuid)

        self.assertEqual(
            json.loads(encoded),
            {
                "protocol_version": 1,
                "type": "START_TEST",
                "command_id": 1,
                "test_uuid": str(test_uuid),
            },
        )

    def test_response_metadata_is_decoded(self) -> None:
        response = decode_start_test_response(response_line(), expected_command_id=1)

        self.assertEqual(response.device.uid, "00112233445566778899AABB")
        self.assertEqual(response.firmware.version, "0.1.0")
        self.assertEqual(response.capabilities, ())

    def test_response_requires_the_matching_command_id(self) -> None:
        with self.assertRaisesRegex(ProtocolMessageError, "does not match"):
            decode_start_test_response(response_line(command_id=2), expected_command_id=1)

    def test_error_response_is_actionable(self) -> None:
        line = b'{"protocol_version":1,"type":"ERROR","command_id":1,"error":"invalid_request"}'
        with self.assertRaisesRegex(ProtocolMessageError, "invalid_request"):
            decode_start_test_response(line, expected_command_id=1)

    def test_session_sends_then_reads_the_start_test_exchange(self) -> None:
        class FakeConnection:
            def __init__(self) -> None:
                self.writes: list[tuple[bytes, float]] = []

            def write_line(self, payload: bytes, *, timeout_seconds: float) -> None:
                self.writes.append((payload, timeout_seconds))

            def read_line(self, *, timeout_seconds: float) -> bytes:
                self.read_timeout = timeout_seconds
                return response_line()

        connection = FakeConnection()
        response = start_test(
            connection,
            test_uuid=UUID("ccc7d571-141e-4054-8e77-6ac3a97ababa"),
        )

        self.assertEqual(json.loads(connection.writes[0][0])["type"], "START_TEST")
        self.assertEqual(response.command_id, 1)
        self.assertEqual(connection.read_timeout, 2.0)


class ReportingTests(unittest.TestCase):
    def test_initial_report_is_created_only_from_valid_metadata(self) -> None:
        configurations = load_configurations(INITIAL_TEST_CONFIG)
        response = StartTestResponse(
            command_id=1,
            device=DeviceMetadata(
                uid="00112233445566778899AABB",
                mcu="STM32F405RGT6",
                board_id="flightcomputer-v1",
                board_name="Flight Computer V1",
                board_revision="1.7",
            ),
            firmware=FirmwareMetadata("0.1.0", "abc123"),
            capabilities=(),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = create_initial_report(
                configurations,
                response,
                results_directory=Path(directory),
                now=datetime(2026, 8, 20, 12, 34, 56, tzinfo=UTC),
            )
            contents = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(contents["status"], "in_progress")
        self.assertEqual(contents["device"]["uid"], response.device.uid)
        self.assertEqual(contents["firmware"]["git_revision"], "abc123")
        self.assertEqual(contents["results"], [])

    def test_failed_session_validation_updates_existing_report(self) -> None:
        configurations = load_configurations(INITIAL_TEST_CONFIG)
        response = StartTestResponse(
            command_id=1,
            device=DeviceMetadata(
                uid="00112233445566778899AABB",
                mcu="STM32F405RGT6",
                board_id="flightcomputer-v1",
                board_name="Flight Computer V1",
                board_revision="1.7",
            ),
            firmware=FirmwareMetadata("0.1.0", "abc123"),
            capabilities=(),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = create_initial_report(
                configurations,
                response,
                results_directory=Path(directory),
                now=datetime(2026, 8, 20, 12, 34, 56, tzinfo=UTC),
            )
            record_session_validation(
                path,
                SessionValidation(
                    board_capabilities=("imu",),
                    firmware_capabilities=(),
                    failures=("firmware is missing board capability/capabilities: imu",),
                ),
                now=datetime(2026, 8, 20, 12, 35, tzinfo=UTC),
            )
            contents = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(contents["status"], "failed")
        self.assertEqual(contents["failure"]["stage"], "session_validation")
        self.assertEqual(contents["session_validation"]["status"], "failed")
        self.assertEqual(contents["results"], [])
