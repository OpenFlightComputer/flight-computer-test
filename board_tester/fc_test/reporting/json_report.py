"""Atomic creation of local, UID-traceable board-test reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from fc_test.configuration import LoadedConfigurations
from fc_test.protocol.messages import StartTestResponse


class ReportError(RuntimeError):
    """A board-test report could not be created safely."""


def default_results_directory() -> Path:
    """Return the ignored repository-local directory for device-identifying reports."""

    return Path(__file__).resolve().parents[3] / "results"


def create_initial_report(
    configurations: LoadedConfigurations,
    response: StartTestResponse,
    *,
    results_directory: Path | None = None,
    now: datetime | None = None,
) -> Path:
    """Persist the session metadata only after a valid START_TEST response."""

    timestamp = now or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("report timestamp must be timezone-aware")
    timestamp = timestamp.astimezone(UTC)
    directory = results_directory or default_results_directory()
    filename_timestamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    report_path = directory / (
        f"{filename_timestamp}_{response.device.uid}_{configurations.test.uuid}.json"
    )
    temporary_path = report_path.with_suffix(".json.tmp")
    report = {
        "schema_version": 1,
        "status": "in_progress",
        "started_at": timestamp.isoformat().replace("+00:00", "Z"),
        "test_configuration": {
            "uuid": str(configurations.test.uuid),
            "name": configurations.test.name,
            "path": str(configurations.test.path),
        },
        "board_configuration": {
            "id": configurations.board.board_id,
            "name": configurations.board.name,
            "revision": configurations.board.revision,
            "path": str(configurations.board.path),
        },
        "device": {
            "uid": response.device.uid,
            "mcu": response.device.mcu,
            "board_id": response.device.board_id,
            "board_name": response.device.board_name,
            "board_revision": response.device.board_revision,
        },
        "firmware": {
            "version": response.firmware.version,
            "git_revision": response.firmware.git_revision,
        },
        "capabilities": list(response.capabilities),
        "results": [],
    }

    try:
        directory.mkdir(parents=True, exist_ok=True)
        if report_path.exists():
            raise ReportError(f"report already exists: {report_path}")
        with temporary_path.open("x", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2, sort_keys=True)
            report_file.write("\n")
            report_file.flush()
        temporary_path.replace(report_path)
    except OSError as error:
        raise ReportError(f"could not create report {report_path}: {error}") from error
    return report_path
