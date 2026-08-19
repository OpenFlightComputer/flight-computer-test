"""USB CDC discovery, connection ownership, and byte-framed I/O."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import serial
from serial.tools import list_ports

from fc_test.protocol.framing import NewlineFramer, encode_line


DEVELOPMENT_USB_VID = 0xCAFE
DEVELOPMENT_USB_PID = 0x4001
ENUMERATION_TIMEOUT_SECONDS = 10.0
ENUMERATION_POLL_SECONDS = 0.25
SERIAL_READ_SLICE_SECONDS = 0.1
SERIAL_BAUD_RATE = 115200


class UsbTransportError(RuntimeError):
    """Base class for actionable USB CDC transport failures."""


class UsbDiscoveryError(UsbTransportError):
    """Raised when a unique requested USB CDC port cannot be discovered."""


class UsbConnectionError(UsbTransportError):
    """Raised when an enumerated USB CDC port cannot be used."""


class UsbTimeoutError(UsbTransportError):
    """Raised when a complete frame is not transferred before its deadline."""


@dataclass(frozen=True)
class SerialPort:
    """The stable subset of pyserial port metadata used for selection."""

    device: str
    vid: int | None
    pid: int | None
    description: str | None = None
    serial_number: str | None = None


class SerialDevice(Protocol):
    timeout: float | None
    write_timeout: float | None

    def read(self, size: int = 1) -> bytes: ...

    def write(self, data: bytes | memoryview) -> int | None: ...

    def close(self) -> None: ...


PortLister = Callable[[], Iterable[SerialPort]]
SerialFactory = Callable[..., SerialDevice]


def list_available_ports() -> tuple[SerialPort, ...]:
    """Return a deterministic snapshot of serial ports reported by pyserial."""

    return tuple(
        sorted(
            (
                SerialPort(
                    device=port.device,
                    vid=port.vid,
                    pid=port.pid,
                    description=port.description,
                    serial_number=port.serial_number,
                )
                for port in list_ports.comports()
            ),
            key=lambda port: port.device,
        )
    )


def wait_for_cdc_port(
    requested_port: str | Path | None = None,
    *,
    vid: int = DEVELOPMENT_USB_VID,
    pid: int = DEVELOPMENT_USB_PID,
    timeout_seconds: float = ENUMERATION_TIMEOUT_SECONDS,
    poll_seconds: float = ENUMERATION_POLL_SECONDS,
    port_lister: PortLister = list_available_ports,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> SerialPort:
    """Wait for exactly one matching CDC device after the SWD reset."""

    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must not be negative")
    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")

    requested = str(requested_port) if requested_port is not None else None
    deadline = monotonic() + timeout_seconds

    while True:
        try:
            ports = tuple(port_lister())
        except (serial.SerialException, OSError) as error:
            raise UsbDiscoveryError(
                f"could not enumerate USB CDC ports: {error}"
            ) from error
        if requested is not None:
            matches = tuple(port for port in ports if port.device == requested)
        else:
            matches = tuple(
                port for port in ports if port.vid == vid and port.pid == pid
            )

        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            devices = ", ".join(port.device for port in matches)
            raise UsbDiscoveryError(
                "multiple OpenFlightComputer USB CDC ports detected "
                f"({devices}); select one with --port"
            )

        now = monotonic()
        if now >= deadline:
            if requested is not None:
                raise UsbDiscoveryError(
                    f"USB CDC port {requested} did not appear within "
                    f"{timeout_seconds:g} seconds"
                )
            raise UsbDiscoveryError(
                "no OpenFlightComputer USB CDC device with VID:PID "
                f"{vid:04X}:{pid:04X} appeared within {timeout_seconds:g} seconds"
            )
        sleeper(min(poll_seconds, deadline - now))


class UsbCdcConnection:
    """Own one open pyserial device and expose bounded framed byte I/O."""

    def __init__(self, port: SerialPort, device: SerialDevice) -> None:
        self.port = port
        self._device = device
        self._framer = NewlineFramer()
        self._closed = False

    @classmethod
    def open(
        cls,
        port: SerialPort,
        *,
        serial_factory: SerialFactory = serial.Serial,
    ) -> UsbCdcConnection:
        try:
            device = serial_factory(
                port=port.device,
                baudrate=SERIAL_BAUD_RATE,
                timeout=SERIAL_READ_SLICE_SECONDS,
                write_timeout=SERIAL_READ_SLICE_SECONDS,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )
        except (serial.SerialException, OSError) as error:
            raise UsbConnectionError(
                f"could not open USB CDC port {port.device}: {error}"
            ) from error
        return cls(port, device)

    def __enter__(self) -> UsbCdcConnection:
        return self

    def __exit__(self, *_error: object) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        try:
            self._device.close()
        except (serial.SerialException, OSError) as error:
            raise UsbConnectionError(
                f"could not close USB CDC port {self.port.device}: {error}"
            ) from error
        self._closed = True

    def read_line(
        self,
        *,
        timeout_seconds: float,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> bytes:
        """Read one complete line while retaining partial input across timeouts."""

        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must not be negative")
        deadline = monotonic() + timeout_seconds

        while True:
            line = self._framer.pop_line()
            if line is not None:
                return line

            remaining = deadline - monotonic()
            if remaining <= 0:
                raise UsbTimeoutError(
                    f"no complete USB CDC line received within {timeout_seconds:g} seconds"
                )
            self._device.timeout = min(SERIAL_READ_SLICE_SECONDS, remaining)
            try:
                chunk = self._device.read(512)
            except (serial.SerialException, OSError) as error:
                raise UsbConnectionError(
                    f"failed reading USB CDC port {self.port.device}: {error}"
                ) from error
            if chunk:
                self._framer.feed(chunk)

    def write_line(
        self,
        payload: bytes,
        *,
        timeout_seconds: float,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        """Write one complete frame, handling valid partial serial writes."""

        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must not be negative")
        frame = encode_line(payload)
        offset = 0
        deadline = monotonic() + timeout_seconds

        while offset < len(frame):
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise UsbTimeoutError(
                    f"USB CDC line was not written within {timeout_seconds:g} seconds"
                )
            self._device.write_timeout = remaining
            try:
                written = self._device.write(memoryview(frame)[offset:])
            except serial.SerialTimeoutException as error:
                raise UsbTimeoutError(
                    f"USB CDC line was not written within {timeout_seconds:g} seconds"
                ) from error
            except (serial.SerialException, OSError) as error:
                raise UsbConnectionError(
                    f"failed writing USB CDC port {self.port.device}: {error}"
                ) from error
            if written is None or written <= 0:
                raise UsbConnectionError(
                    f"USB CDC port {self.port.device} accepted no output bytes"
                )
            offset += written


@contextmanager
def open_usb_cdc(
    requested_port: str | Path | None = None,
    *,
    port_lister: PortLister = list_available_ports,
    serial_factory: SerialFactory = serial.Serial,
) -> Iterator[UsbCdcConnection]:
    """Discover, open, yield, and reliably close the board's USB CDC port."""

    port = wait_for_cdc_port(requested_port, port_lister=port_lister)
    connection = UsbCdcConnection.open(port, serial_factory=serial_factory)
    try:
        yield connection
    finally:
        connection.close()
