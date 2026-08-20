"""Validate a started manufacturing-test session against its board configuration."""

from __future__ import annotations

from dataclasses import dataclass

from fc_test.configuration import LoadedConfigurations
from fc_test.protocol.messages import StartTestResponse


@dataclass(frozen=True, slots=True)
class SessionValidation:
    """The outcome of comparing declared board requirements to firmware metadata."""

    board_capabilities: tuple[str, ...]
    firmware_capabilities: tuple[str, ...]
    failures: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Whether the connected firmware can test the selected board."""

        return not self.failures


def validate_session(
    configurations: LoadedConfigurations, response: StartTestResponse
) -> SessionValidation:
    """Compare immutable board identity and required capabilities to the response.

    Firmware version and revision are recorded in the report but are not a
    compatibility policy in this milestone. Firmware may advertise additional
    capabilities; it must advertise every capability the board requires.
    """

    board = configurations.board
    device = response.device
    failures: list[str] = []
    for field, expected, received in (
        ("MCU", board.mcu.model, device.mcu),
        ("board ID", board.board_id, device.board_id),
        ("board name", board.name, device.board_name),
        ("board revision", board.revision, device.board_revision),
    ):
        if expected != received:
            failures.append(f"{field} mismatch: expected {expected}, received {received}")

    missing_capabilities = [
        capability
        for capability in board.test_capabilities
        if capability not in response.capabilities
    ]
    if missing_capabilities:
        failures.append(
            "firmware is missing board capability/capabilities: "
            + ", ".join(missing_capabilities)
        )

    return SessionValidation(
        board_capabilities=board.test_capabilities,
        firmware_capabilities=response.capabilities,
        failures=tuple(failures),
    )
