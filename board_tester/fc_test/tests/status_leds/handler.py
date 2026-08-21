"""Operator-confirmed discrete status-LED tests."""

from fc_test.protocol.component_session import run_component_test, stop_component_test
from fc_test.protocol.messages import ComponentTestCompletion, ComponentTestEvent
from fc_test.tests.base import ComponentTestHandler, ComponentTestResult


class StatusLedTestHandler(ComponentTestHandler):
    def __init__(self, colour: str, input_reader=input, output=print) -> None:
        self._colour = colour
        self._input = input_reader
        self._output = output

    def run(self, connection, *, command_id: int, definition, workflow) -> ComponentTestResult:
        def confirm() -> ComponentTestCompletion:
            while True:
                answer = self._input(f"Is the {self._colour} status LED illuminated? [Y/n]: ").strip().lower()
                if answer in {"", "y", "n"}:
                    break
                self._output("Please enter Y or n.")
            stop_component_test(connection, command_id=command_id + 1000, test_type=definition.type)
            return ComponentTestCompletion(command_id, definition.type, "passed" if answer != "n" else "failed")
        completion = run_component_test(connection, command_id=command_id, test_type=definition.type, on_event=self.handle_event, on_started=confirm)
        return self.finish(completion)

    def begin(self, definition) -> None: pass
    def handle_event(self, event: ComponentTestEvent) -> None: pass
    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        return ComponentTestResult(completion.status, {"colour": self._colour, "operator_response": completion.status})
