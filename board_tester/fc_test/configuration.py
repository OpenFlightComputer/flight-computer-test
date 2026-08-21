"""Load and validate board-tester configuration files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID


SUPPORTED_TEST_TYPES = frozenset(
    {
        "mcu_runtime",
        "status_leds",
        "status_led_red",
        "status_led_green",
        "rgb_led",
        "imu",
        "barometer",
        "sd_card",
    }
)


class ConfigurationError(ValueError):
    """A configuration file could not be loaded or validated."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


@dataclass(frozen=True, slots=True)
class McuConfiguration:
    """Physical MCU identity from a board configuration."""

    reference: str
    model: str
    schematic_value: str
    package: str


@dataclass(frozen=True, slots=True)
class BoardConfiguration:
    """Validated physical board description."""

    path: Path
    schema_version: int
    name: str
    board_id: str
    revision: str
    source: dict[str, Any]
    mcu: McuConfiguration
    test_capabilities: tuple[str, ...]
    components: dict[str, Any]
    buses: dict[str, Any]
    pins: dict[str, Any]
    known_hardware_constraints: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TestDefinition:
    """One ordered component-test entry."""

    type: str
    enabled: bool
    parameters: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TestConfiguration:
    """Validated test policy and its resolved board reference."""

    path: Path
    schema_version: int
    name: str
    uuid: UUID
    board_config_reference: str
    board_config_path: Path
    tests: tuple[TestDefinition, ...]

    @property
    def enabled_tests(self) -> tuple[TestDefinition, ...]:
        """Return enabled tests without changing their configured order."""

        return tuple(test for test in self.tests if test.enabled)


@dataclass(frozen=True, slots=True)
class LoadedConfigurations:
    """A validated test configuration and its referenced board."""

    test: TestConfiguration
    board: BoardConfiguration


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as configuration_file:
            value = json.load(configuration_file)
    except OSError as error:
        raise ConfigurationError(path, f"cannot read file: {error.strerror}") from error
    except UnicodeDecodeError as error:
        raise ConfigurationError(path, "file is not valid UTF-8") from error
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            path,
            f"invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}",
        ) from error

    if not isinstance(value, dict):
        raise ConfigurationError(path, "top level must be a JSON object")
    return value


def _require_exact_keys(
    value: dict[str, Any],
    *,
    required: set[str],
    path: Path,
    location: str,
) -> None:
    missing = sorted(required - value.keys())
    if missing:
        raise ConfigurationError(
            path, f"{location} is missing required field(s): {', '.join(missing)}"
        )

    unknown = sorted(value.keys() - required)
    if unknown:
        raise ConfigurationError(
            path, f"{location} contains unknown field(s): {', '.join(unknown)}"
        )


def _require_string(
    value: dict[str, Any], field: str, *, path: Path, location: str
) -> str:
    result = value[field]
    if not isinstance(result, str) or not result.strip():
        raise ConfigurationError(path, f"{location}.{field} must be a non-empty string")
    return result


def _require_object(
    value: dict[str, Any], field: str, *, path: Path, location: str
) -> dict[str, Any]:
    result = value[field]
    if not isinstance(result, dict):
        raise ConfigurationError(path, f"{location}.{field} must be a JSON object")
    return result


def _require_schema_version(value: dict[str, Any], *, path: Path) -> int:
    schema_version = value["schema_version"]
    if type(schema_version) is not int or schema_version != 1:
        raise ConfigurationError(path, "schema_version must be the integer 1")
    return schema_version


def load_board_configuration(path: Path) -> BoardConfiguration:
    """Load and validate a physical board configuration."""

    value = _load_json_object(path)
    required = {
        "schema_version",
        "name",
        "board_id",
        "revision",
        "source",
        "mcu",
        "test_capabilities",
        "components",
        "buses",
        "pins",
        "known_hardware_constraints",
    }
    _require_exact_keys(value, required=required, path=path, location="board config")
    schema_version = _require_schema_version(value, path=path)
    name = _require_string(value, "name", path=path, location="board config")
    board_id = _require_string(
        value, "board_id", path=path, location="board config"
    )
    revision = _require_string(
        value, "revision", path=path, location="board config"
    )

    source = _require_object(value, "source", path=path, location="board config")
    source_fields = {
        "manufacturing_revision",
        "schematic_title",
        "schematic_revision",
        "kicad_project",
        "schematic",
        "pcb",
    }
    _require_exact_keys(source, required=source_fields, path=path, location="source")
    for field in source_fields:
        _require_string(source, field, path=path, location="source")
    if source["manufacturing_revision"] != revision:
        raise ConfigurationError(
            path,
            "source.manufacturing_revision must match board config.revision",
        )

    mcu = _require_object(value, "mcu", path=path, location="board config")
    mcu_fields = {"reference", "model", "schematic_value", "package"}
    _require_exact_keys(mcu, required=mcu_fields, path=path, location="mcu")

    test_capabilities = value["test_capabilities"]
    if not isinstance(test_capabilities, list) or not test_capabilities:
        raise ConfigurationError(
            path, "board config.test_capabilities must be a non-empty array"
        )
    if not all(isinstance(capability, str) and capability.strip() for capability in test_capabilities):
        raise ConfigurationError(
            path,
            "board config.test_capabilities must contain only non-empty strings",
        )
    duplicate_capabilities = sorted(
        {
            capability
            for capability in test_capabilities
            if test_capabilities.count(capability) > 1
        }
    )
    if duplicate_capabilities:
        raise ConfigurationError(
            path,
            "board config.test_capabilities contains duplicate value(s): "
            + ", ".join(duplicate_capabilities),
        )
    unsupported_capabilities = sorted(set(test_capabilities) - SUPPORTED_TEST_TYPES)
    if unsupported_capabilities:
        raise ConfigurationError(
            path,
            "board config.test_capabilities contains unsupported value(s): "
            + ", ".join(unsupported_capabilities),
        )

    components = _require_object(
        value, "components", path=path, location="board config"
    )
    buses = _require_object(value, "buses", path=path, location="board config")
    pins = _require_object(value, "pins", path=path, location="board config")
    for field, collection in (
        ("components", components),
        ("buses", buses),
        ("pins", pins),
    ):
        if not collection:
            raise ConfigurationError(path, f"board config.{field} must not be empty")

    constraints = value["known_hardware_constraints"]
    if not isinstance(constraints, list) or not all(
        isinstance(item, str) and item.strip() for item in constraints
    ):
        raise ConfigurationError(
            path,
            "board config.known_hardware_constraints must be an array of "
            "non-empty strings",
        )

    return BoardConfiguration(
        path=path,
        schema_version=schema_version,
        name=name,
        board_id=board_id,
        revision=revision,
        source=source,
        mcu=McuConfiguration(
            reference=_require_string(mcu, "reference", path=path, location="mcu"),
            model=_require_string(mcu, "model", path=path, location="mcu"),
            schematic_value=_require_string(
                mcu, "schematic_value", path=path, location="mcu"
            ),
            package=_require_string(mcu, "package", path=path, location="mcu"),
        ),
        test_capabilities=tuple(test_capabilities),
        components=components,
        buses=buses,
        pins=pins,
        known_hardware_constraints=tuple(constraints),
    )


def load_test_configuration(path: Path) -> TestConfiguration:
    """Load and validate test policy, including its board-config reference."""

    value = _load_json_object(path)
    required = {"schema_version", "name", "uuid", "board_config", "tests"}
    _require_exact_keys(value, required=required, path=path, location="test config")
    schema_version = _require_schema_version(value, path=path)
    name = _require_string(value, "name", path=path, location="test config")

    uuid_text = _require_string(value, "uuid", path=path, location="test config")
    try:
        test_uuid = UUID(uuid_text)
    except ValueError as error:
        raise ConfigurationError(
            path, "test config.uuid must be a valid UUID"
        ) from error
    if test_uuid.version != 4 or str(test_uuid) != uuid_text:
        raise ConfigurationError(
            path, "test config.uuid must be a canonical lowercase UUID v4"
        )

    board_reference = _require_string(
        value, "board_config", path=path, location="test config"
    )
    board_path = (path.parent / board_reference).resolve()
    if not board_path.exists():
        raise ConfigurationError(
            path, f"referenced board configuration does not exist: {board_reference}"
        )
    if not board_path.is_file():
        raise ConfigurationError(
            path, f"referenced board configuration is not a file: {board_reference}"
        )

    tests = value["tests"]
    if not isinstance(tests, list) or not tests:
        raise ConfigurationError(path, "test config.tests must be a non-empty array")

    definitions: list[TestDefinition] = []
    seen_types: set[str] = set()
    for index, definition in enumerate(tests):
        location = f"tests[{index}]"
        if not isinstance(definition, dict):
            raise ConfigurationError(path, f"{location} must be a JSON object")
        _require_exact_keys(
            definition,
            required={"type", "enabled", "parameters"},
            path=path,
            location=location,
        )

        test_type = _require_string(
            definition, "type", path=path, location=location
        )
        if test_type not in SUPPORTED_TEST_TYPES:
            supported = ", ".join(sorted(SUPPORTED_TEST_TYPES))
            raise ConfigurationError(
                path,
                f"{location}.type is unsupported: {test_type}; supported types: "
                f"{supported}",
            )
        if test_type in seen_types:
            raise ConfigurationError(
                path, f"{location}.type is duplicated: {test_type}"
            )
        seen_types.add(test_type)

        enabled = definition["enabled"]
        if not isinstance(enabled, bool):
            raise ConfigurationError(path, f"{location}.enabled must be a boolean")
        parameters = _require_object(
            definition, "parameters", path=path, location=location
        )
        definitions.append(
            TestDefinition(type=test_type, enabled=enabled, parameters=parameters)
        )

    return TestConfiguration(
        path=path,
        schema_version=schema_version,
        name=name,
        uuid=test_uuid,
        board_config_reference=board_reference,
        board_config_path=board_path,
        tests=tuple(definitions),
    )


def load_configurations(test_configuration_path: Path) -> LoadedConfigurations:
    """Load one test configuration and its referenced board configuration."""

    test = load_test_configuration(test_configuration_path)
    board = load_board_configuration(test.board_config_path)
    unsupported_test_types = [
        definition.type
        for definition in test.tests
        if definition.type not in board.test_capabilities
    ]
    if unsupported_test_types:
        raise ConfigurationError(
            test.path,
            "test config defines type(s) not advertised by board "
            f"{board.board_id}: {', '.join(unsupported_test_types)}",
        )
    return LoadedConfigurations(test=test, board=board)
