"""Stable public imports for the board-tester/firmware protocol messages."""

from fc_test.protocol.component_messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    decode_component_test_message,
    encode_run_component_test,
    encode_stop_component_test,
)
from fc_test.protocol.message_validation import PROTOCOL_VERSION, ProtocolMessageError
from fc_test.protocol.session_messages import (
    DeviceMetadata,
    FirmwareMetadata,
    StartTestResponse,
    decode_start_test_response,
    encode_start_test,
)

__all__ = [
    "PROTOCOL_VERSION",
    "ComponentTestCompletion",
    "ComponentTestEvent",
    "DeviceMetadata",
    "FirmwareMetadata",
    "ProtocolMessageError",
    "StartTestResponse",
    "decode_component_test_message",
    "decode_start_test_response",
    "encode_run_component_test",
    "encode_start_test",
    "encode_stop_component_test",
]
