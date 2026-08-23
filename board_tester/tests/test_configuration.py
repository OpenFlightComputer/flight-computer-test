from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path

from fc_test.configuration import (
    ConfigurationError,
    load_board_configuration,
    load_configurations,
    load_test_configuration,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CURRENT_TEST_CONFIG = REPOSITORY_ROOT / "configs/test/test-config-v004.json"


class ConfigurationLoadingTests(unittest.TestCase):
    def test_current_configurations_load_with_expected_identity_and_order(self) -> None:
        configurations = load_configurations(CURRENT_TEST_CONFIG)

        self.assertEqual(configurations.board.name, "Flight Computer V1")
        self.assertEqual(configurations.board.revision, "1.7")
        self.assertEqual(configurations.board.mcu.model, "STM32F405RGT6")
        self.assertEqual(
            configurations.board.test_capabilities,
            (
                "status_led_red",
                "status_led_green",
                "rgb_led",
                "imu",
                "barometer",
                "sd_card",
            ),
        )
        self.assertEqual(
            configurations.test.name, "Flight Computer V1 Complete Acceptance"
        )
        self.assertEqual(
            str(configurations.test.uuid), "642e3504-c499-409c-858f-ac6b5e2850cf"
        )
        self.assertEqual(
            [test.type for test in configurations.test.enabled_tests],
            [
                "status_led_red",
                "status_led_green",
                "rgb_led",
                "imu",
                "barometer",
                "sd_card",
            ],
        )

    def test_board_reference_is_resolved_relative_to_test_config(self) -> None:
        with tempfile.TemporaryDirectory() as other_directory:
            with chdir(other_directory):
                configuration = load_test_configuration(CURRENT_TEST_CONFIG)

        self.assertEqual(
            configuration.board_config_path,
            (REPOSITORY_ROOT / "configs/board/flightcomputer-v1.json").resolve(),
        )

    def test_rgb_configuration_selects_turquoise(self) -> None:
        configuration = load_test_configuration(CURRENT_TEST_CONFIG)
        rgb_test = next(test for test in configuration.tests if test.type == "rgb_led")

        self.assertEqual(rgb_test.parameters, {"colour": "turquoise"})

    def test_rgb_configuration_rejects_unknown_colours(self) -> None:
        with self._configuration_tree() as paths:
            test_value = self._valid_test_value()
            test_value["tests"] = [
                {
                    "type": "rgb_led",
                    "enabled": True,
                    "parameters": {"colour": "ultraviolet"},
                }
            ]
            self._write_json(paths.test, test_value)

            with self.assertRaisesRegex(ConfigurationError, "CSS3 name"):
                load_test_configuration(paths.test)

    def test_disabled_test_is_preserved_but_excluded_from_enabled_tests(self) -> None:
        with self._configuration_tree() as paths:
            test_value = self._valid_test_value()
            test_value["tests"][1]["enabled"] = False
            self._write_json(paths.test, test_value)

            configuration = load_test_configuration(paths.test)

        self.assertEqual(
            [test.type for test in configuration.tests], ["imu", "sd_card"]
        )
        self.assertEqual([test.type for test in configuration.enabled_tests], ["imu"])

    def test_invalid_json_reports_line_and_column(self) -> None:
        with self._configuration_tree() as paths:
            paths.test.write_text('{"schema_version": 1,', encoding="utf-8")

            with self.assertRaisesRegex(
                ConfigurationError, r"invalid JSON at line 1, column 22"
            ):
                load_test_configuration(paths.test)

    def test_uuid_must_be_canonical_uuid_v4(self) -> None:
        with self._configuration_tree() as paths:
            test_value = self._valid_test_value()
            test_value["uuid"] = "00000000-0000-1000-8000-000000000000"
            self._write_json(paths.test, test_value)

            with self.assertRaisesRegex(ConfigurationError, "UUID v4"):
                load_test_configuration(paths.test)

    def test_unknown_test_type_is_rejected(self) -> None:
        with self._configuration_tree() as paths:
            test_value = self._valid_test_value()
            test_value["tests"][0]["type"] = "identity"
            self._write_json(paths.test, test_value)

            with self.assertRaisesRegex(
                ConfigurationError, r"tests\[0\]\.type is unsupported: identity"
            ):
                load_test_configuration(paths.test)

    def test_duplicate_test_type_is_rejected(self) -> None:
        with self._configuration_tree() as paths:
            test_value = self._valid_test_value()
            test_value["tests"][1]["type"] = "imu"
            self._write_json(paths.test, test_value)

            with self.assertRaisesRegex(ConfigurationError, "is duplicated: imu"):
                load_test_configuration(paths.test)

    def test_missing_board_reference_is_rejected(self) -> None:
        with self._configuration_tree() as paths:
            test_value = self._valid_test_value()
            test_value["board_config"] = "missing.json"
            self._write_json(paths.test, test_value)

            with self.assertRaisesRegex(
                ConfigurationError, "referenced board configuration does not exist"
            ):
                load_test_configuration(paths.test)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        with self._configuration_tree() as paths:
            test_value = self._valid_test_value()
            test_value["priority"] = 1
            self._write_json(paths.test, test_value)

            with self.assertRaisesRegex(
                ConfigurationError, r"contains unknown field\(s\): priority"
            ):
                load_test_configuration(paths.test)

    def test_board_requires_supported_schema_version(self) -> None:
        with self._configuration_tree() as paths:
            board_value = self._valid_board_value()
            board_value["schema_version"] = 2
            self._write_json(paths.board, board_value)

            with self.assertRaisesRegex(ConfigurationError, "integer 1"):
                load_board_configuration(paths.board)

    def test_board_revision_must_match_manufacturing_revision(self) -> None:
        with self._configuration_tree() as paths:
            board_value = self._valid_board_value()
            board_value["revision"] = "1.1"
            self._write_json(paths.board, board_value)

            with self.assertRaisesRegex(
                ConfigurationError, "manufacturing_revision must match"
            ):
                load_board_configuration(paths.board)

    def test_board_capabilities_must_be_known_and_unique(self) -> None:
        with self._configuration_tree() as paths:
            board_value = self._valid_board_value()
            board_value["test_capabilities"] = ["imu", "imu", "future_test"]
            self._write_json(paths.board, board_value)

            with self.assertRaisesRegex(
                ConfigurationError, "contains duplicate value\\(s\\): imu"
            ):
                load_board_configuration(paths.board)

    def test_test_types_must_be_advertised_by_board_before_building(self) -> None:
        with self._configuration_tree() as paths:
            board_value = self._valid_board_value()
            board_value["test_capabilities"] = ["imu"]
            self._write_json(paths.board, board_value)

            with self.assertRaisesRegex(
                ConfigurationError,
                "not advertised by board example-board: sd_card",
            ):
                load_configurations(paths.test)

    @staticmethod
    def _valid_test_value() -> dict[str, object]:
        return {
            "schema_version": 1,
            "name": "Example acceptance",
            "uuid": "3e50168d-a4db-4a90-b05d-0ed03819e49f",
            "board_config": "board.json",
            "tests": [
                {"type": "imu", "enabled": True, "parameters": {}},
                {"type": "sd_card", "enabled": True, "parameters": {}},
            ],
        }

    @staticmethod
    def _valid_board_value() -> dict[str, object]:
        return {
            "schema_version": 1,
            "name": "Example board",
            "board_id": "example-board",
            "revision": "1.0",
            "source": {
                "manufacturing_revision": "1.0",
                "schematic_title": "Example",
                "schematic_revision": "0.1",
                "kicad_project": "example.kicad_pro",
                "schematic": "example.kicad_sch",
                "pcb": "example.kicad_pcb",
            },
            "mcu": {
                "reference": "U1",
                "model": "STM32F405RGT6",
                "schematic_value": "STM32F405RGTx",
                "package": "LQFP-64",
            },
            "test_capabilities": ["imu", "sd_card"],
            "components": {"imu": {}},
            "buses": {"imu_spi": {}},
            "pins": {"PB3": {}},
            "known_hardware_constraints": [],
        }

    @staticmethod
    def _write_json(path: Path, value: dict[str, object]) -> None:
        path.write_text(json.dumps(value), encoding="utf-8")

    class _ConfigurationPaths:
        def __init__(self, root: Path) -> None:
            self.board = root / "board.json"
            self.test = root / "test.json"

    class _ConfigurationTree:
        def __init__(self, test_case: "ConfigurationLoadingTests") -> None:
            self.test_case = test_case
            self.temporary_directory: tempfile.TemporaryDirectory[str] | None = None

        def __enter__(self) -> "ConfigurationLoadingTests._ConfigurationPaths":
            self.temporary_directory = tempfile.TemporaryDirectory()
            paths = ConfigurationLoadingTests._ConfigurationPaths(
                Path(self.temporary_directory.name)
            )
            self.test_case._write_json(
                paths.board, self.test_case._valid_board_value()
            )
            self.test_case._write_json(paths.test, self.test_case._valid_test_value())
            return paths

        def __exit__(self, *_args: object) -> None:
            assert self.temporary_directory is not None
            self.temporary_directory.cleanup()

    def _configuration_tree(self) -> "ConfigurationLoadingTests._ConfigurationTree":
        return self._ConfigurationTree(self)


if __name__ == "__main__":
    unittest.main()
