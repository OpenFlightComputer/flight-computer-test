"""Automatic SD-card test progress and result reporting."""

from __future__ import annotations

from fc_test.protocol.messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    ProtocolMessageError,
)
from fc_test.tests.base import (
    ComponentTestHandler,
    ComponentTestResult,
    require_event_integer,
)


class SdCardTestHandler(ComponentTestHandler):
    """Show card instructions and retain firmware-verified card information."""

    _MESSAGES = {
        "sd_card_remove_required": "Remove the SD card, then wait.",
        "sd_card_removed": "Card removed.",
        "sd_card_insert_required": "Insert an SD card to begin the automatic check.",
        "sd_card_detected": "Card detected; initializing it.",
        "sd_card_initialized": "Card initialized.",
        "sd_card_written": "Test data written.",
        "sd_card_verified": "Read-back verification passed.",
        "sd_card_cleaned_up": "Test sectors cleared.",
    }

    def __init__(self, output=print) -> None:
        self._output = output
        self._events: list[str] = []
        self._card: dict[str, object] = {}

    def begin(self, definition) -> None:
        self._events = []
        self._card = {}
        self._output("Starting automatic SD-card test.")
        self._output(
            "WARNING: This test overwrites and clears eight raw sectors near "
            "the end of the SD card. Use a disposable card; existing filesystem "
            "data may be damaged."
        )

    def handle_event(self, event: ComponentTestEvent) -> ComponentTestCompletion | None:
        self._events.append(event.event)
        self._output(self._MESSAGES.get(event.event, f"sd_card: {event.event}"))
        if event.data is not None:
            self._card = dict(event.data)
            if event.event == "sd_card_initialized":
                card_type = self._card.get("card_type")
                if not isinstance(card_type, str) or not card_type:
                    raise ProtocolMessageError(
                        "sd_card_initialized data.card_type must be a string"
                    )
                sector_count = require_event_integer(
                    self._card, "sector_count", "sd_card_initialized"
                )
                test_sector = require_event_integer(
                    self._card, "test_sector", "sd_card_initialized"
                )
                self._output(
                    f"{card_type}: {sector_count:,} sectors; "
                    f"test starts at sector {test_sector:,}."
                )
        return None

    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        return ComponentTestResult(
            status=completion.status,
            details={
                "firmware_status": completion.status,
                "events": list(self._events),
                "card": dict(self._card),
            },
        )
