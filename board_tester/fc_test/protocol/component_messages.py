"""RUN/STOP component-test commands and lifecycle responses."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fc_test.protocol.message_validation import (
    PROTOCOL_VERSION,
    ProtocolMessageError,
    decode_object,
    require_keys,
    require_positive_integer,
    require_string,
    validate_command_id,
    validate_test_type,
)


@dataclass(frozen=True, slots=True)
class ComponentTestEvent:
    command_id: int
    test_type: str
    event: str
    data: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ComponentTestCompletion:
    command_id: int
    test_type: str
    status: str


def encode_run_component_test(
    *,
    command_id: int,
    test_type: str,
    parameters: dict[str, int] | None = None,
) -> bytes:
    """Encode a request to start one firmware component test."""

    validate_command_id(command_id)
    validate_test_type(test_type, "test_type")
    request: dict[str, Any] = {
        "protocol_version": PROTOCOL_VERSION,
        "type": "RUN_COMPONENT_TEST",
        "command_id": command_id,
        "test_type": test_type,
    }
    if parameters is not None:
        if parameters.keys() != {"red", "green", "blue"}:
            raise ValueError("RGB parameters must contain red, green, and blue")
        if any(
            type(value) is not int or value < 0 or value > 255
            for value in parameters.values()
        ):
            raise ValueError("RGB parameters must be integers from 0 through 255")
        request["parameters"] = parameters
    return json.dumps(request, separators=(",", ":")).encode("ascii")


def encode_stop_component_test(*, command_id: int) -> bytes:
    """Encode a request to stop the single active firmware component test."""

    validate_command_id(command_id)
    return json.dumps(
        {
            "protocol_version": PROTOCOL_VERSION,
            "type": "STOP_COMPONENT_TEST",
            "command_id": command_id,
        },
        separators=(",", ":"),
    ).encode("ascii")


def decode_component_test_message(
    line: bytes, *, expected_command_id: int, expected_test_type: str
) -> ComponentTestEvent | ComponentTestCompletion | str:
    """Decode one strictly correlated component lifecycle message."""

    response = decode_object(line)
    if response.get("protocol_version") != PROTOCOL_VERSION:
        raise ProtocolMessageError("response has an unsupported protocol_version")
    if response.get("type") == "ERROR":
        require_keys(
            response,
            {"protocol_version", "type", "command_id", "error"},
            "response",
        )
        command_id = require_positive_integer(response, "command_id", "response")
        if command_id != expected_command_id:
            raise ProtocolMessageError(
                "response command_id does not match active test"
            )
        error = require_string(response, "error", "response")
        raise ProtocolMessageError(f"device rejected component test: {error}")

    message_type = require_string(response, "type", "response")
    if message_type == "TEST_EVENT":
        return _decode_event(response, expected_command_id, expected_test_type)
    if message_type in {"TEST_STARTED", "TEST_COMPLETED", "TEST_STOPPED"}:
        return _decode_lifecycle_response(
            response, message_type, expected_command_id, expected_test_type
        )
    raise ProtocolMessageError(
        f"response type is not a component lifecycle message: {message_type}"
    )


def _decode_event(
    response: dict[str, Any], expected_command_id: int, expected_test_type: str
) -> ComponentTestEvent:
    allowed = {
        "protocol_version",
        "type",
        "command_id",
        "test_type",
        "event",
        "data",
    }
    required = allowed - {"data"}
    if set(response) - allowed or not required.issubset(response):
        raise ProtocolMessageError("response has unexpected TEST_EVENT fields")
    data = response.get("data")
    if data is not None and not isinstance(data, dict):
        raise ProtocolMessageError("response.data must be an object")
    return ComponentTestEvent(
        _matching_command_id(response, expected_command_id),
        _matching_test_type(response, expected_test_type),
        require_string(response, "event", "response"),
        data,
    )


def _decode_lifecycle_response(
    response: dict[str, Any],
    message_type: str,
    expected_command_id: int,
    expected_test_type: str,
) -> ComponentTestCompletion | str:
    require_keys(
        response,
        {"protocol_version", "type", "command_id", "test_type", "status"},
        "response",
    )
    command_id = _matching_command_id(response, expected_command_id)
    test_type = _matching_test_type(response, expected_test_type)
    status = require_string(response, "status", "response")
    expected_statuses = {
        "TEST_STARTED": {"running"},
        "TEST_COMPLETED": {"passed", "failed"},
        "TEST_STOPPED": {"stopped"},
    }
    if status not in expected_statuses[message_type]:
        raise ProtocolMessageError(
            f"response status {status!r} is invalid for {message_type}"
        )
    if message_type == "TEST_COMPLETED":
        return ComponentTestCompletion(command_id, test_type, status)
    return message_type


def _matching_command_id(value: dict[str, Any], expected: int) -> int:
    command_id = require_positive_integer(value, "command_id", "response")
    if command_id != expected:
        raise ProtocolMessageError("response command_id does not match active test")
    return command_id


def _matching_test_type(value: dict[str, Any], expected: str) -> str:
    test_type = require_string(value, "test_type", "response")
    if test_type != expected:
        raise ProtocolMessageError("response test_type does not match active test")
    return test_type
