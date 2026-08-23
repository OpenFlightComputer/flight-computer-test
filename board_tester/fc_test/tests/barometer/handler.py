"""Live, operator-confirmed BMP388 pressure and temperature test."""

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


class BarometerTestHandler(ComponentTestHandler):
    """Show compensated BMP388 readings until the operator confirms them."""

    def __init__(self) -> None:
        self._answers: Queue[str] = Queue()
        self._pressure_centi_pa: int | None = None
        self._temperature_centi_c: int | None = None
        self._initial_pressure_centi_pa: int | None = None
        self._initial_temperature_centi_c: int | None = None
        self._samples = 0
        self._connection: FramedConnection | None = None
        self._command_id = 0
        self._test_type = "barometer"
        self._live: Live | None = None
        self._prompt_started = False

    def begin(self, definition) -> None:
        self._pressure_centi_pa = None
        self._temperature_centi_c = None
        self._initial_pressure_centi_pa = None
        self._initial_temperature_centi_c = None
        self._samples = 0
        self._test_type = definition.type
        self._prompt_started = False

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
        if event.event == "barometer_ready" and not self._prompt_started:
            self._prompt_started = True
            Thread(target=self._read_answer, daemon=True).start()
        elif event.event == "barometer_sample" and event.data is not None:
            self._pressure_centi_pa = self._integer(event.data, "pressure_centi_pa")
            self._temperature_centi_c = self._integer(event.data, "temperature_centi_c")
            if self._initial_pressure_centi_pa is None:
                self._initial_pressure_centi_pa = self._pressure_centi_pa
                self._initial_temperature_centi_c = self._temperature_centi_c
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
            "firmware_status": completion.status,
            "sample_count": self._samples,
            "last_pressure_pa": self._as_decimal(self._pressure_centi_pa),
            "last_temperature_c": self._as_decimal(self._temperature_centi_c),
        })

    def _read_answer(self) -> None:
        self._answers.put(input(
            "Lift/lower the board and warm the sensor area gently. "
            "Do pressure and temperature look live? [Y/n] "
        ))

    def _render(self):
        table = Table(title="BMP388 live values")
        table.add_column("Measurement")
        table.add_column("Current", justify="right")
        table.add_column("Change since start", justify="right")
        table.add_row(
            "Pressure", self._formatted(self._pressure_centi_pa, "hPa"),
            self._delta(self._pressure_centi_pa, self._initial_pressure_centi_pa, "hPa"),
        )
        table.add_row(
            "Temperature", self._formatted(self._temperature_centi_c, "°C"),
            self._delta(self._temperature_centi_c, self._initial_temperature_centi_c, "°C"),
        )
        return Group(table, "Lift/lower the board and warm the sensor area; press Enter to pass, or n then Enter to fail.")

    @staticmethod
    def _integer(data: dict[str, object], key: str) -> int:
        value = data.get(key)
        if type(value) is not int:
            raise ValueError(f"barometer event {key} must be an integer")
        return value

    @staticmethod
    def _as_decimal(value: int | None) -> float | None:
        return None if value is None else value / 100.0

    @classmethod
    def _formatted(cls, value: int | None, unit: str) -> str:
        if value is None:
            return "—"
        scaled = value / 100.0
        if unit == "hPa":
            scaled /= 100.0
        return f"{scaled:,.2f} {unit}"

    @classmethod
    def _delta(cls, value: int | None, initial: int | None, unit: str) -> str:
        if value is None or initial is None:
            return "—"
        scaled = (value - initial) / 100.0
        if unit == "hPa":
            scaled /= 100.0
        return f"{scaled:+.2f} {unit}"
