"""Component-specific presentation and result handling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from fc_test.configuration import TestDefinition
from fc_test.protocol.messages import (
    ComponentTestCompletion,
    ComponentTestEvent,
    ProtocolMessageError,
)
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


def prompt_yes_no(
    question: str,
    *,
    input_reader: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> bool:
    """Ask a Y/n question, accepting Enter as the default yes answer."""

    while True:
        answer = input_reader(f"{question} [Y/n]: ").strip().lower()
        if answer in {"", "y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        output("Please enter Y or n.")


def require_event_integer(data: dict[str, object], key: str, event: str) -> int:
    """Read one exact integer from component event data."""

    value = data.get(key)
    if type(value) is not int:
        raise ProtocolMessageError(f"{event} data.{key} must be an integer")
    return value


def require_failure_details(event: ComponentTestEvent) -> dict[str, object]:
    """Validate the diagnostic payload shared by firmware component failures."""

    if event.data is None:
        raise ProtocolMessageError("component_failure event is missing data")
    stage = event.data.get("stage")
    reason = event.data.get("reason")
    code = event.data.get("code")
    if not isinstance(stage, str) or not stage:
        raise ProtocolMessageError("component_failure data.stage must be a string")
    if not isinstance(reason, str) or not reason:
        raise ProtocolMessageError("component_failure data.reason must be a string")
    if type(code) is not int:
        raise ProtocolMessageError("component_failure data.code must be an integer")
    return {"stage": stage, "reason": reason, "code": code}


def format_component_failure(component: str, failure: dict[str, object]) -> str:
    """Turn machine-readable stage names into a concise operator message."""

    stage = str(failure["stage"]).replace("_", " ")
    reason = str(failure["reason"]).replace("_", " ")
    return f"{component} failed during {stage}: {reason} (code {failure['code']})."
