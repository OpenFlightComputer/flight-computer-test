"""Bounded newline framing shared by the computer-side USB transport."""

from __future__ import annotations

from collections import deque


MAX_LINE_LENGTH = 4096


class FramingError(ValueError):
    """Base class for invalid protocol framing."""


class LineTooLongError(FramingError):
    """Raised after an oversized incoming line has been fully discarded."""


class NewlineFramer:
    """Assemble arbitrary byte chunks into bounded LF-terminated lines."""

    def __init__(self, *, max_line_length: int = MAX_LINE_LENGTH) -> None:
        if max_line_length < 1:
            raise ValueError("max_line_length must be positive")
        self._max_line_length = max_line_length
        self._line = bytearray()
        self._events: deque[bytes | LineTooLongError] = deque()
        self._discarding = False

    def feed(self, data: bytes) -> None:
        """Consume bytes, retaining complete lines and framing errors in order."""

        for byte in data:
            if self._discarding:
                if byte == ord("\n"):
                    self._discarding = False
                    self._events.append(
                        LineTooLongError(
                            f"incoming line exceeds {self._max_line_length} bytes"
                        )
                    )
                continue

            if byte == ord("\n"):
                if self._line.endswith(b"\r"):
                    self._line.pop()
                self._events.append(bytes(self._line))
                self._line.clear()
                continue

            if len(self._line) == self._max_line_length:
                self._line.clear()
                self._discarding = True
                continue

            self._line.append(byte)

    def pop_line(self) -> bytes | None:
        """Return the next complete line, or raise its ordered framing error."""

        if not self._events:
            return None
        event = self._events.popleft()
        if isinstance(event, LineTooLongError):
            raise event
        return event


def encode_line(payload: bytes, *, max_line_length: int = MAX_LINE_LENGTH) -> bytes:
    """Validate and LF-terminate one outgoing protocol payload."""

    if len(payload) > max_line_length:
        raise LineTooLongError(f"outgoing line exceeds {max_line_length} bytes")
    if b"\n" in payload or b"\r" in payload:
        raise FramingError("outgoing payload must not contain CR or LF bytes")
    return payload + b"\n"
