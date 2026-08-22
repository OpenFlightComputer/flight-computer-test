"""Board-tester initiated component-test lifecycle exchange."""

from __future__ import annotations

from collections.abc import Callable

from fc_test.protocol.connection import UsbTimeoutError
from fc_test.protocol.messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    ProtocolMessageError,
    decode_component_test_message,
    encode_run_component_test,
    encode_stop_component_test,
)
from fc_test.protocol.session import FramedConnection


COMPONENT_TEST_WRITE_TIMEOUT_SECONDS = 1.0
COMPONENT_TEST_STARTED_TIMEOUT_SECONDS = 2.0
COMPONENT_TEST_READ_SLICE_SECONDS = 2.0


def run_component_test(
    connection: FramedConnection,
    *,
    command_id: int,
    test_type: str,
    on_event: Callable[[ComponentTestEvent], ComponentTestCompletion | None],
    on_started: Callable[[], ComponentTestCompletion | None] | None = None,
    parameters: dict[str, int] | None = None,
) -> ComponentTestCompletion:
    """Run one component test, waiting indefinitely after it has started."""

    connection.write_line(
        encode_run_component_test(
            command_id=command_id,
            test_type=test_type,
            parameters=parameters,
        ),
        timeout_seconds=COMPONENT_TEST_WRITE_TIMEOUT_SECONDS,
    )
    first = decode_component_test_message(
        connection.read_line(timeout_seconds=COMPONENT_TEST_STARTED_TIMEOUT_SECONDS),
        expected_command_id=command_id,
        expected_test_type=test_type,
    )
    if first != "TEST_STARTED":
        raise ProtocolMessageError("component test did not acknowledge TEST_STARTED")
    if on_started is not None:
        completion = on_started()
        if completion is not None:
            return completion

    while True:
        try:
            message = decode_component_test_message(
                connection.read_line(timeout_seconds=COMPONENT_TEST_READ_SLICE_SECONDS),
                expected_command_id=command_id,
                expected_test_type=test_type,
            )
        except UsbTimeoutError:
            continue
        if isinstance(message, ComponentTestEvent):
            completion = on_event(message)
            if completion is not None:
                return completion
        elif isinstance(message, ComponentTestCompletion):
            return message
        else:
            raise ProtocolMessageError("unexpected component lifecycle acknowledgement")


def stop_component_test(
    connection: FramedConnection, *, command_id: int, test_type: str
) -> None:
    """Request immediate component cleanup and require its stop acknowledgement."""

    connection.write_line(
        encode_stop_component_test(command_id=command_id),
        timeout_seconds=COMPONENT_TEST_WRITE_TIMEOUT_SECONDS,
    )
    response = decode_component_test_message(
        connection.read_line(timeout_seconds=COMPONENT_TEST_STARTED_TIMEOUT_SECONDS),
        expected_command_id=command_id,
        expected_test_type=test_type,
    )
    if response != "TEST_STOPPED":
        raise ProtocolMessageError("component test did not acknowledge TEST_STOPPED")
