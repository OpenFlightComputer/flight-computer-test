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
