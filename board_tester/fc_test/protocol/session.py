"""The board-tester initiated START_TEST session exchange."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from fc_test.protocol.messages import StartTestResponse, decode_start_test_response, encode_start_test


START_TEST_COMMAND_ID = 1
START_TEST_WRITE_TIMEOUT_SECONDS = 1.0
START_TEST_RESPONSE_TIMEOUT_SECONDS = 2.0


class FramedConnection(Protocol):
    def write_line(self, payload: bytes, *, timeout_seconds: float) -> None: ...

    def read_line(self, *, timeout_seconds: float) -> bytes: ...


def start_test(connection: FramedConnection, *, test_uuid: UUID) -> StartTestResponse:
    """Request session metadata and return the strictly matched response."""

    connection.write_line(
        encode_start_test(command_id=START_TEST_COMMAND_ID, test_uuid=test_uuid),
        timeout_seconds=START_TEST_WRITE_TIMEOUT_SECONDS,
    )
    return decode_start_test_response(
        connection.read_line(timeout_seconds=START_TEST_RESPONSE_TIMEOUT_SECONDS),
        expected_command_id=START_TEST_COMMAND_ID,
    )
