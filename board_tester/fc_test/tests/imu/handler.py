"""Live, operator-confirmed BMI270 motion test."""

from __future__ import annotations

from rich.console import Group
from rich.table import Table

from fc_test.protocol.messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    ProtocolMessageError,
)
from fc_test.tests.base import (
    ComponentTestResult,
    require_event_integer,
)
from fc_test.tests.live_operator import LiveOperatorTestHandler


class ImuTestHandler(LiveOperatorTestHandler):
    """Present raw acceleration and gyro axes until the operator finishes."""

    def __init__(self, *, input_reader=input) -> None:
        super().__init__(input_reader=input_reader)
        self._latest: dict[str, int] = {}
        self._samples = 0

    @property
    def ready_event(self) -> str:
        return "imu_ready"

    @property
    def prompt(self) -> str:
        return "Move the board in all directions. Does IMU data change? [Y/n] "

    def reset_measurements(self) -> None:
        self._latest = {}
        self._samples = 0

    def record_event(self, event: ComponentTestEvent) -> None:
        if event.event != "imu_sample":
            return
        if event.data is None:
            raise ProtocolMessageError("imu_sample event is missing data")

        latest: dict[str, int] = {}
        for group_name in ("acceleration_raw", "gyroscope_raw"):
            group = event.data.get(group_name)
            if not isinstance(group, dict):
                raise ProtocolMessageError(
                    f"imu_sample data.{group_name} must be an object"
                )
            for axis in ("x", "y", "z"):
                latest[f"{group_name}_{axis}"] = require_event_integer(
                    group, axis, f"imu_sample data.{group_name}"
                )
        self._latest = latest
        self._samples += 1

    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        return ComponentTestResult(
            status=completion.status,
            details={
                "firmware_status": completion.status,
                "sample_count": self._samples,
                "last_raw_sample": dict(self._latest),
            },
        )

    def render(self):
        table = Table(title="BMI270 live raw data")
        table.add_column("Axis")
        table.add_column("Acceleration")
        table.add_column("Gyroscope")
        for axis in ("x", "y", "z"):
            table.add_row(
                axis.upper(),
                self._bar(self._latest.get(f"acceleration_raw_{axis}")),
                self._bar(self._latest.get(f"gyroscope_raw_{axis}")),
            )
        return Group(
            table,
            "Move the board; press Enter to confirm it changes, or type n then "
            "Enter to fail.",
        )

    @staticmethod
    def _bar(value: int | None) -> str:
        """Render a centred, deliberately qualitative raw-value column bar."""
        if value is None:
            return "—"
        width = 12
        magnitude = min(width, abs(value) * width // 32768)
        left = "█" * magnitude if value < 0 else ""
        right = "█" * magnitude if value >= 0 else ""
        return f"{value:6d}  {left:>{width}}│{right:<{width}}"
