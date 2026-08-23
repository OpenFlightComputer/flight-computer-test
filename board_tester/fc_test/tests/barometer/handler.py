"""Live, operator-confirmed BMP388 pressure and temperature test."""

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


class BarometerTestHandler(LiveOperatorTestHandler):
    """Show compensated BMP388 readings until the operator confirms them."""

    def __init__(self, *, input_reader=input) -> None:
        super().__init__(input_reader=input_reader)
        self._pressure_centi_pa: int | None = None
        self._temperature_centi_c: int | None = None
        self._initial_pressure_centi_pa: int | None = None
        self._initial_temperature_centi_c: int | None = None
        self._samples = 0

    @property
    def ready_event(self) -> str:
        return "barometer_ready"

    @property
    def prompt(self) -> str:
        return (
            "Lift/lower the board and warm the sensor area gently. "
            "Do pressure and temperature look live? [Y/n] "
        )

    def reset_measurements(self) -> None:
        self._pressure_centi_pa = None
        self._temperature_centi_c = None
        self._initial_pressure_centi_pa = None
        self._initial_temperature_centi_c = None
        self._samples = 0

    def record_event(self, event: ComponentTestEvent) -> None:
        if event.event != "barometer_sample":
            return
        if event.data is None:
            raise ProtocolMessageError("barometer_sample event is missing data")
        self._pressure_centi_pa = require_event_integer(
            event.data, "pressure_centi_pa", "barometer_sample"
        )
        self._temperature_centi_c = require_event_integer(
            event.data, "temperature_centi_c", "barometer_sample"
        )
        if self._initial_pressure_centi_pa is None:
            self._initial_pressure_centi_pa = self._pressure_centi_pa
            self._initial_temperature_centi_c = self._temperature_centi_c
        self._samples += 1

    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        return ComponentTestResult(
            status=completion.status,
            details={
                "firmware_status": completion.status,
                "sample_count": self._samples,
                "last_pressure_pa": self._as_decimal(self._pressure_centi_pa),
                "last_temperature_c": self._as_decimal(self._temperature_centi_c),
            },
        )

    def render(self):
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
        return Group(
            table,
            "Lift/lower the board and warm the sensor area; press Enter to pass, "
            "or n then Enter to fail.",
        )

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
