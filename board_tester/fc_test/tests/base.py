"""Component-specific presentation and result handling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from fc_test.configuration import TestDefinition
from fc_test.protocol.messages import ComponentTestCompletion, ComponentTestEvent
from fc_test.protocol.session import FramedConnection


@dataclass(frozen=True, slots=True)
class ComponentTestResult:
    """A component-specific terminal result ready for generic persistence."""

    status: str
    details: dict[str, object]


class ComponentTestHandler(ABC):
    """Own the tester-facing behavior for one component test type."""

    def run(
        self,
        connection: FramedConnection,
        *,
        command_id: int,
        definition: TestDefinition,
        workflow,
    ) -> ComponentTestResult:
        """Run this handler's test through the shared lifecycle transport."""

        self.begin(definition)
        completion = workflow(
            connection,
            command_id=command_id,
            test_type=definition.type,
            on_event=self.handle_event,
        )
        return self.finish(completion)

    @abstractmethod
    def begin(self, definition: TestDefinition) -> None:
        """Perform optional local preparation before the firmware command."""

    @abstractmethod
    def handle_event(self, event: ComponentTestEvent) -> ComponentTestCompletion | None:
        """Present and record a component-specific non-terminal event."""

    @abstractmethod
    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        """Produce component-specific result data from firmware completion."""


class GenericComponentTestHandler(ComponentTestHandler):
    """Temporary handler that preserves raw events until component UIs exist."""

    def __init__(self, output=print) -> None:
        self._output = output
        self._events: list[str] = []

    def begin(self, definition: TestDefinition) -> None:
        self._events = []
        self._output(f"Starting component test: {definition.type}")

    def handle_event(self, event: ComponentTestEvent) -> ComponentTestCompletion | None:
        self._events.append(event.event)
        self._output(f"{event.test_type}: {event.event}")
        return None

    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        return ComponentTestResult(
            status=completion.status,
            details={"events": list(self._events), "firmware_status": completion.status},
        )
