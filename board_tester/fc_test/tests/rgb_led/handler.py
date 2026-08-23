"""Operator-confirmed WS2812 RGB LED test."""

from fc_test.protocol.component_session import stop_component_test
from fc_test.protocol.messages import ComponentTestCompletion, ComponentTestEvent
from fc_test.tests.rgb_led.colours import colour_to_rgb
from fc_test.tests.base import ComponentTestHandler, ComponentTestResult, prompt_yes_no


class RgbLedTestHandler(ComponentTestHandler):
    def __init__(self, input_reader=input, output=print) -> None:
        self._input = input_reader
        self._output = output
        self._colour = "turquoise"
        self._rgb = colour_to_rgb(self._colour)

    def run(self, connection, *, command_id: int, definition, workflow) -> ComponentTestResult:
        self.begin(definition)

        def confirm() -> ComponentTestCompletion:
            passed = prompt_yes_no(
                f"Is the RGB LED illuminated {self._colour}?",
                input_reader=self._input,
                output=self._output,
            )
            stop_component_test(
                connection,
                command_id=command_id + 1000,
                test_type=definition.type,
            )
            status = "passed" if passed else "failed"
            return ComponentTestCompletion(command_id, definition.type, status)

        red, green, blue = self._rgb
        completion = workflow(
            connection,
            command_id=command_id,
            test_type=definition.type,
            parameters={"red": red, "green": green, "blue": blue},
            on_event=self.handle_event,
            on_started=confirm,
        )
        return self.finish(completion)

    def begin(self, definition) -> None:
        colour = definition.parameters.get("colour", "turquoise")
        self._colour = colour
        self._rgb = colour_to_rgb(colour)

    def handle_event(self, event: ComponentTestEvent) -> None:
        self._output(f"RGB LED: {event.event}")

    def finish(self, completion: ComponentTestCompletion) -> ComponentTestResult:
        red, green, blue = self._rgb
        return ComponentTestResult(
            completion.status,
            {
                "colour": self._colour,
                "rgb": {"red": red, "green": green, "blue": blue},
                "operator_response": completion.status,
            },
        )
