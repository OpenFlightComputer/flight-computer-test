"""Typed JSON messages for the board-tester/manufacturing-firmware protocol."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID


PROTOCOL_VERSION = 1
_UID_PATTERN = re.compile(r"^[0-9A-F]{24}$")


class ProtocolMessageError(ValueError):
    """A complete transport line is not a valid expected protocol message."""


@dataclass(frozen=True, slots=True)
class DeviceMetadata:
    uid: str
    mcu: str
    board_id: str
    board_name: str
    board_revision: str


@dataclass(frozen=True, slots=True)
class FirmwareMetadata:
    version: str
    git_revision: str


@dataclass(frozen=True, slots=True)
class StartTestResponse:
    command_id: int
    device: DeviceMetadata
    firmware: FirmwareMetadata
    capabilities: tuple[str, ...]


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


def encode_start_test(*, command_id: int, test_uuid: UUID) -> bytes:
    """Encode the first board-tester initiated protocol command."""

    if type(command_id) is not int or command_id <= 0:
        raise ValueError("command_id must be a positive integer")
    return json.dumps(
        {
            "protocol_version": PROTOCOL_VERSION,
            "type": "START_TEST",
            "command_id": command_id,
            "test_uuid": str(test_uuid),
        },
        separators=(",", ":"),
    ).encode("ascii")


def encode_run_component_test(
    *,
    command_id: int,
    test_type: str,
    parameters: dict[str, int] | None = None,
) -> bytes:
    """Encode a request to start one firmware component test."""

    _validate_command_id(command_id)
    _validate_test_type(test_type, "test_type")
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

    _validate_command_id(command_id)
    return json.dumps(
        {"protocol_version": PROTOCOL_VERSION, "type": "STOP_COMPONENT_TEST", "command_id": command_id},
        separators=(",", ":"),
    ).encode("ascii")


def decode_start_test_response(
    line: bytes,
    *,
    expected_command_id: int,
) -> StartTestResponse:
    """Decode and strictly validate one successful ``START_TEST`` response."""

    try:
        value = json.loads(line.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise ProtocolMessageError("response is not valid UTF-8") from error
    except json.JSONDecodeError as error:
        raise ProtocolMessageError(
            f"response is not valid JSON: {error.msg}"
        ) from error

    response = _require_object(value, "response")
    if response.get("protocol_version") != PROTOCOL_VERSION:
        raise ProtocolMessageError("response has an unsupported protocol_version")
    if response.get("type") == "ERROR":
        _require_keys(
            response,
            {"protocol_version", "type", "command_id", "error"},
            "response",
        )
        raise ProtocolMessageError(
            f"device rejected START_TEST: {_require_string(response, 'error', 'response')}"
        )
    _require_keys(
        response,
        {
            "protocol_version",
            "type",
            "command_id",
            "status",
            "device",
            "firmware",
            "capabilities",
        },
        "response",
    )
    if response["type"] != "START_TEST_RESPONSE":
        raise ProtocolMessageError("response type is not START_TEST_RESPONSE")
    if response["status"] != "ok":
        raise ProtocolMessageError("START_TEST response status is not ok")
    command_id = _require_positive_integer(response, "command_id", "response")
    if command_id != expected_command_id:
        raise ProtocolMessageError(
            f"response command_id {command_id} does not match {expected_command_id}"
        )

    device_value = _require_object(response["device"], "response.device")
    _require_keys(
        device_value,
        {"uid", "mcu", "board_id", "board_name", "board_revision"},
        "response.device",
    )
    uid = _require_string(device_value, "uid", "response.device")
    if not _UID_PATTERN.fullmatch(uid):
        raise ProtocolMessageError("response.device.uid must be 24 uppercase hex digits")

    firmware_value = _require_object(response["firmware"], "response.firmware")
    _require_keys(
        firmware_value,
        {"version", "git_revision"},
        "response.firmware",
    )
    capabilities = response["capabilities"]
    if not isinstance(capabilities, list) or not all(
        isinstance(capability, str) and capability for capability in capabilities
    ):
        raise ProtocolMessageError("response.capabilities must be an array of strings")
    if len(set(capabilities)) != len(capabilities):
        raise ProtocolMessageError("response.capabilities must not contain duplicates")

    return StartTestResponse(
        command_id=command_id,
        device=DeviceMetadata(
            uid=uid,
            mcu=_require_string(device_value, "mcu", "response.device"),
            board_id=_require_string(device_value, "board_id", "response.device"),
            board_name=_require_string(device_value, "board_name", "response.device"),
            board_revision=_require_string(
                device_value, "board_revision", "response.device"
            ),
        ),
        firmware=FirmwareMetadata(
            version=_require_string(firmware_value, "version", "response.firmware"),
            git_revision=_require_string(
                firmware_value, "git_revision", "response.firmware"
            ),
        ),
        capabilities=tuple(capabilities),
    )


def decode_component_test_message(
    line: bytes, *, expected_command_id: int, expected_test_type: str
) -> ComponentTestEvent | ComponentTestCompletion | str:
    """Decode one strictly correlated component lifecycle message."""

    response = _decode_object(line)
    if response.get("protocol_version") != PROTOCOL_VERSION:
        raise ProtocolMessageError("response has an unsupported protocol_version")
    if response.get("type") == "ERROR":
        _require_keys(response, {"protocol_version", "type", "command_id", "error"}, "response")
        command_id = _require_positive_integer(response, "command_id", "response")
        if command_id != expected_command_id:
            raise ProtocolMessageError("response command_id does not match active test")
        raise ProtocolMessageError(f"device rejected component test: {_require_string(response, 'error', 'response')}")
    message_type = _require_string(response, "type", "response")
    if message_type == "TEST_EVENT":
        allowed = {"protocol_version", "type", "command_id", "test_type", "event", "data"}
        if set(response) - allowed or not {"protocol_version", "type", "command_id", "test_type", "event"}.issubset(response):
            raise ProtocolMessageError("response has unexpected TEST_EVENT fields")
        data = response.get("data")
        if data is not None and not isinstance(data, dict):
            raise ProtocolMessageError("response.data must be an object")
        return ComponentTestEvent(
            _require_matching_command_id(response, expected_command_id),
            _require_matching_test_type(response, expected_test_type),
            _require_string(response, "event", "response"),
            data,
        )
    if message_type in {"TEST_STARTED", "TEST_COMPLETED", "TEST_STOPPED"}:
        _require_keys(response, {"protocol_version", "type", "command_id", "test_type", "status"}, "response")
        return ComponentTestCompletion(
            _require_matching_command_id(response, expected_command_id),
            _require_matching_test_type(response, expected_test_type),
            _require_string(response, "status", "response"),
        ) if message_type == "TEST_COMPLETED" else message_type
    raise ProtocolMessageError(f"response type is not a component lifecycle message: {message_type}")


def _decode_object(line: bytes) -> dict[str, Any]:
    try:
        return _require_object(json.loads(line.decode("utf-8")), "response")
    except UnicodeDecodeError as error:
        raise ProtocolMessageError("response is not valid UTF-8") from error
    except json.JSONDecodeError as error:
        raise ProtocolMessageError(f"response is not valid JSON: {error.msg}") from error


def _validate_command_id(command_id: int) -> None:
    if type(command_id) is not int or command_id <= 0:
        raise ValueError("command_id must be a positive integer")


def _validate_test_type(test_type: str, location: str) -> None:
    if not isinstance(test_type, str) or not re.fullmatch(r"[a-z0-9_]+", test_type):
        raise ValueError(f"{location} must be lowercase letters, digits, or underscores")


def _require_matching_command_id(value: dict[str, Any], expected: int) -> int:
    command_id = _require_positive_integer(value, "command_id", "response")
    if command_id != expected:
        raise ProtocolMessageError("response command_id does not match active test")
    return command_id


def _require_matching_test_type(value: dict[str, Any], expected: str) -> str:
    test_type = _require_string(value, "test_type", "response")
    if test_type != expected:
        raise ProtocolMessageError("response test_type does not match active test")
    return test_type


def _require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolMessageError(f"{location} must be a JSON object")
    return value


def _require_keys(value: dict[str, Any], keys: set[str], location: str) -> None:
    if value.keys() != keys:
        missing = sorted(keys - value.keys())
        unknown = sorted(value.keys() - keys)
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if unknown:
            detail.append(f"unknown {', '.join(unknown)}")
        raise ProtocolMessageError(f"{location} has invalid fields ({'; '.join(detail)})")


def _require_string(value: dict[str, Any], field: str, location: str) -> str:
    result = value[field]
    if not isinstance(result, str) or not result:
        raise ProtocolMessageError(f"{location}.{field} must be a non-empty string")
    return result


def _require_positive_integer(value: dict[str, Any], field: str, location: str) -> int:
    result = value[field]
    if type(result) is not int or result <= 0:
        raise ProtocolMessageError(f"{location}.{field} must be a positive integer")
    return result
