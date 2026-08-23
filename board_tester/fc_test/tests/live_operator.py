"""Shared lifecycle for live component tests ended by an operator decision."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from queue import Empty, Queue
from threading import Thread

from rich.live import Live

from fc_test.configuration import TestDefinition
from fc_test.protocol.component_session import stop_component_test
from fc_test.protocol.messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    ProtocolMessageError,
)
from fc_test.protocol.session import FramedConnection
from fc_test.tests.base import ComponentTestHandler, ComponentTestResult


class LiveOperatorTestHandler(ComponentTestHandler):
    """Share transport, live-display, prompt, and stop behavior."""

    def __init__(self, *, input_reader: Callable[[str], str] = input) -> None:
        self._input = input_reader
        self._answers: Queue[str] = Queue()
        self._connection: FramedConnection | None = None
        self._command_id = 0
        self._test_type = ""
        self._live: Live | None = None
        self._prompt_started = False

    def begin(self, definition: TestDefinition) -> None:
        self._answers = Queue()
        self._test_type = definition.type
        self._prompt_started = False
        self.reset_measurements()

    def run(
        self,
        connection: FramedConnection,
        *,
        command_id: int,
        definition: TestDefinition,
        workflow,
    ) -> ComponentTestResult:
        self.begin(definition)
        self._connection = connection
        self._command_id = command_id
        try:
            with Live(self.render(), refresh_per_second=8, transient=True) as live:
                self._live = live
                completion = workflow(
                    connection,
                    command_id=command_id,
                    test_type=definition.type,
                    on_event=self.handle_event,
                )
        finally:
            self._live = None
            self._connection = None
        return self.finish(completion)

    def handle_event(
        self, event: ComponentTestEvent
    ) -> ComponentTestCompletion | None:
        if event.event == self.ready_event and not self._prompt_started:
            self._prompt_started = True
            Thread(target=self._read_answer, daemon=True).start()
        else:
            self.record_event(event)

        if self._live is not None:
            self._live.update(self.render())

        try:
            answer = self._answers.get_nowait()
        except Empty:
            return None

        if self._connection is None:
            raise ProtocolMessageError("operator test has no active connection")
        stop_component_test(
            self._connection,
            command_id=self._command_id + 1000,
            test_type=self._test_type,
        )
        status = "passed" if answer.strip().lower() not in {"n", "no"} else "failed"
        return ComponentTestCompletion(self._command_id, self._test_type, status)

    def _read_answer(self) -> None:
        self._answers.put(self._input(self.prompt))

    @property
    @abstractmethod
    def ready_event(self) -> str:
        """Event name that indicates the operator prompt may start."""

    @property
    @abstractmethod
    def prompt(self) -> str:
        """Operator prompt, including its Y/n suffix."""

    @abstractmethod
    def reset_measurements(self) -> None:
        """Clear component-specific sample state before a new run."""

    @abstractmethod
    def record_event(self, event: ComponentTestEvent) -> None:
        """Validate and retain one component-specific sample event."""

    @abstractmethod
    def render(self):
        """Build the current Rich renderable."""
