from __future__ import annotations

import unittest
from collections import deque

from fc_test.protocol.connection import (
    SerialPort,
    UsbCdcConnection,
    UsbDiscoveryError,
    UsbTimeoutError,
    open_usb_cdc,
    wait_for_cdc_port,
)
from fc_test.protocol.framing import (
    FramingError,
    LineTooLongError,
    NewlineFramer,
    encode_line,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class FakeSerial:
    def __init__(
        self,
        chunks: tuple[bytes, ...] = (),
        *,
        clock: FakeClock | None = None,
        write_limit: int | None = None,
    ) -> None:
        self.chunks = deque(chunks)
        self.clock = clock
        self.write_limit = write_limit
        self.timeout: float | None = None
        self.write_timeout: float | None = None
        self.written = bytearray()
        self.closed = False

    def read(self, _size: int = 1) -> bytes:
        if self.chunks:
            return self.chunks.popleft()
        if self.clock is not None:
            self.clock.now += self.timeout or 0.0
        return b""

    def write(self, data: bytes | memoryview) -> int:
        count = len(data) if self.write_limit is None else min(self.write_limit, len(data))
        self.written.extend(data[:count])
        return count

    def close(self) -> None:
        self.closed = True


class FramingTests(unittest.TestCase):
    def test_fragmented_crlf_and_multiple_lines_are_assembled(self) -> None:
        framer = NewlineFramer()
        framer.feed(b"first\r")
        self.assertIsNone(framer.pop_line())

        framer.feed(b"\nsecond\nthird")

        self.assertEqual(framer.pop_line(), b"first")
        self.assertEqual(framer.pop_line(), b"second")
        self.assertIsNone(framer.pop_line())

    def test_exact_limit_is_accepted(self) -> None:
        framer = NewlineFramer(max_line_length=4)
        framer.feed(b"1234\n")
        self.assertEqual(framer.pop_line(), b"1234")

    def test_oversized_line_is_discarded_and_following_line_survives(self) -> None:
        framer = NewlineFramer(max_line_length=4)
        framer.feed(b"12345ignored\nok\n")

        with self.assertRaises(LineTooLongError):
            framer.pop_line()
        self.assertEqual(framer.pop_line(), b"ok")

    def test_outgoing_lines_are_validated_and_terminated(self) -> None:
        self.assertEqual(encode_line(b"payload"), b"payload\n")
        with self.assertRaises(FramingError):
            encode_line(b"two\nlines")
        with self.assertRaises(FramingError):
            encode_line(b"carriage\rreturn")
        with self.assertRaises(LineTooLongError):
            encode_line(b"12345", max_line_length=4)


class DiscoveryTests(unittest.TestCase):
    def test_discovery_retries_until_matching_device_appears(self) -> None:
        clock = FakeClock()
        snapshots = deque(
            [(), (), (SerialPort("/dev/cu.board", 0xCAFE, 0x4001),)]
        )

        port = wait_for_cdc_port(
            timeout_seconds=1.0,
            poll_seconds=0.25,
            port_lister=lambda: snapshots.popleft(),
            monotonic=clock.monotonic,
            sleeper=clock.sleep,
        )

        self.assertEqual(port.device, "/dev/cu.board")
        self.assertEqual(clock.now, 0.5)

    def test_explicit_port_bypasses_vid_pid_filter(self) -> None:
        selected = wait_for_cdc_port(
            "/dev/cu.custom",
            timeout_seconds=0,
            port_lister=lambda: (
                SerialPort("/dev/cu.custom", 0x1234, 0x5678),
            ),
        )
        self.assertEqual(selected.device, "/dev/cu.custom")

    def test_multiple_matches_require_explicit_port(self) -> None:
        with self.assertRaisesRegex(UsbDiscoveryError, "--port"):
            wait_for_cdc_port(
                timeout_seconds=0,
                port_lister=lambda: (
                    SerialPort("/dev/cu.one", 0xCAFE, 0x4001),
                    SerialPort("/dev/cu.two", 0xCAFE, 0x4001),
                ),
            )

    def test_missing_device_times_out_with_identity(self) -> None:
        with self.assertRaisesRegex(UsbDiscoveryError, "CAFE:4001"):
            wait_for_cdc_port(timeout_seconds=0, port_lister=lambda: ())


class ConnectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.port = SerialPort("/dev/cu.board", 0xCAFE, 0x4001)

    def test_open_configures_serial_and_context_closes_it(self) -> None:
        device = FakeSerial()
        arguments: dict[str, object] = {}

        def serial_factory(**kwargs):
            arguments.update(kwargs)
            return device

        with open_usb_cdc(
            port_lister=lambda: (self.port,), serial_factory=serial_factory
        ) as connection:
            self.assertEqual(connection.port, self.port)
            self.assertFalse(device.closed)

        self.assertTrue(device.closed)
        self.assertEqual(arguments["port"], "/dev/cu.board")
        self.assertEqual(arguments["baudrate"], 115200)
        self.assertFalse(arguments["xonxoff"])
        self.assertFalse(arguments["rtscts"])
        self.assertFalse(arguments["dsrdtr"])

    def test_read_returns_queued_lines_in_order(self) -> None:
        device = FakeSerial((b"one\ntwo\n",))
        connection = UsbCdcConnection(self.port, device)

        self.assertEqual(connection.read_line(timeout_seconds=1), b"one")
        self.assertEqual(connection.read_line(timeout_seconds=1), b"two")

    def test_partial_input_survives_a_read_timeout(self) -> None:
        clock = FakeClock()
        device = FakeSerial((b"partial",), clock=clock)
        connection = UsbCdcConnection(self.port, device)

        with self.assertRaises(UsbTimeoutError):
            connection.read_line(timeout_seconds=0.2, monotonic=clock.monotonic)

        device.chunks.append(b" line\n")
        self.assertEqual(
            connection.read_line(timeout_seconds=0.2, monotonic=clock.monotonic),
            b"partial line",
        )

    def test_partial_writes_send_one_complete_frame(self) -> None:
        device = FakeSerial(write_limit=2)
        connection = UsbCdcConnection(self.port, device)

        connection.write_line(b"hello", timeout_seconds=1)

        self.assertEqual(device.written, b"hello\n")


if __name__ == "__main__":
    unittest.main()
