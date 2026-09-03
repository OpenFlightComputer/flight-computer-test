"""Validation primitives shared by protocol message families."""

from __future__ import annotations

import json
import re
from typing import Any


PROTOCOL_VERSION = 1


class ProtocolMessageError(ValueError):
    """A complete transport line is not a valid expected protocol message."""


def decode_object(line: bytes) -> dict[str, Any]:
    try:
        return require_object(json.loads(line.decode("utf-8")), "response")
    except UnicodeDecodeError as error:
        raise ProtocolMessageError("response is not valid UTF-8") from error
    except json.JSONDecodeError as error:
        excerpt = repr(line[:120])
        if len(line) > 120:
            excerpt += "..."
        raise ProtocolMessageError(
            f"response is not valid JSON: {error.msg}; received {excerpt}"
        ) from error


def validate_command_id(command_id: int) -> None:
    if type(command_id) is not int or command_id <= 0:
        raise ValueError("command_id must be a positive integer")


def validate_test_type(test_type: str, location: str) -> None:
    if not isinstance(test_type, str) or not re.fullmatch(
        r"[a-z0-9_]+", test_type
    ):
        raise ValueError(
            f"{location} must be lowercase letters, digits, or underscores"
        )


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolMessageError(f"{location} must be a JSON object")
    return value


def require_keys(value: dict[str, Any], keys: set[str], location: str) -> None:
    if value.keys() == keys:
        return
    missing = sorted(keys - value.keys())
    unknown = sorted(value.keys() - keys)
    detail = []
    if missing:
        detail.append(f"missing {', '.join(missing)}")
    if unknown:
        detail.append(f"unknown {', '.join(unknown)}")
    raise ProtocolMessageError(
        f"{location} has invalid fields ({'; '.join(detail)})"
    )


def require_string(value: dict[str, Any], field: str, location: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise ProtocolMessageError(f"{location}.{field} must be a non-empty string")
    return result


def require_positive_integer(
    value: dict[str, Any], field: str, location: str
) -> int:
    result = value.get(field)
    if type(result) is not int or result <= 0:
        raise ProtocolMessageError(
            f"{location}.{field} must be a positive integer"
        )
    return result
