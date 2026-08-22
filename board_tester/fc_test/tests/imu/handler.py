"""Live, operator-confirmed BMI270 motion test."""

from __future__ import annotations

from queue import Empty, Queue
from threading import Thread

from rich.console import Group
from rich.live import Live
from rich.table import Table

from fc_test.protocol.component_session import stop_component_test
from fc_test.protocol.messages import ComponentTestCompletion, ComponentTestEvent
from fc_test.protocol.session import FramedConnection
from fc_test.tests.base import ComponentTestHandler, ComponentTestResult


class ImuTestHandler(ComponentTestHandler):
    """Present raw acceleration and gyro axes until the operator finishes."""

    def __init__(self) -> None:
        self._answers: Queue[str] = Queue()
        self._latest: dict[str, int] = {}
        self._samples = 0
        self._connection: FramedConnection | None = None
        self._command_id = 0
        self._test_type = "imu"
        self._live: Live | None = None
        self._prompt_started = False

    def begin(self, definition) -> None:
        self._latest = {}
        self._samples = 0
        self._test_type = definition.type

    def run(self, connection, *, command_id, definition, workflow) -> ComponentTestResult:
        self.begin(definition)
        self._connection = connection
        self._command_id = command_id
        with Live(self._render(), refresh_per_second=8, transient=True) as live:
            self._live = live
            completion = workflow(connection, command_id=command_id, test_type=definition.type,
                                  on_event=self.handle_event)
        self._live = None
        return self.finish(completion)

    def handle_event(self, event: ComponentTestEvent) -> ComponentTestCompletion | None:
        if event.event == "imu_ready" and not self._prompt_started:
            self._prompt_started = True
            Thread(target=self._read_answer, daemon=True).start()
        elif event.event == "imu_sample" and event.data is not None:
            self._latest = {
                f"{group_name}_{axis}": value
                for group_name, group in event.data.items()
                for axis, value in group.items()
            }
            self._samples += 1
        if self._live is not None:
            self._live.update(self._render())
        try:
            answer = self._answers.get_nowait()
        except Empty:
            return None
        passed = answer.strip().lower() not in {"n", "no"}
        assert self._connection is not None
        stop_component_test(self._connection, command_id=self._command_id, test_type=self._test_type)
        return ComponentTestCompletion(self._command_id, self._test_type, "passed" if passed else "failed")

    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        return ComponentTestResult(status=completion.status, details={
            "firmware_status": completion.status, "sample_count": self._samples,
            "last_raw_sample": dict(self._latest),
        })

    def _read_answer(self) -> None:
        self._answers.put(input("Move the board in all directions. Does IMU data change? [Y/n] "))

    def _render(self):
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
        return Group(table, "Move the board; press Enter to confirm it changes, or type n then Enter to fail.")

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
