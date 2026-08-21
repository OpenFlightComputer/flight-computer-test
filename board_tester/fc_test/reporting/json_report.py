"""Atomic creation of local, UID-traceable board-test reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from fc_test.configuration import LoadedConfigurations
from fc_test.protocol.messages import StartTestResponse
from fc_test.session_validation import SessionValidation


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
        _write_report(report, report_path, temporary_path, mode="x")
    except OSError as error:
        raise ReportError(f"could not create report {report_path}: {error}") from error
    return report_path


def record_session_validation(
    report_path: Path,
    validation: SessionValidation,
    *,
    now: datetime | None = None,
) -> None:
    """Persist the board-to-firmware compatibility result in an initial report."""

    timestamp = now or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("report timestamp must be timezone-aware")
    timestamp_text = timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")
    temporary_path = report_path.with_suffix(".json.tmp")

    try:
        with report_path.open("r", encoding="utf-8") as report_file:
            report = json.load(report_file)
        if not isinstance(report, dict):
            raise ReportError(f"report is not a JSON object: {report_path}")

        report["session_validation"] = {
            "status": "passed" if validation.passed else "failed",
            "validated_at": timestamp_text,
            "board_capabilities": list(validation.board_capabilities),
            "firmware_capabilities": list(validation.firmware_capabilities),
            "failures": list(validation.failures),
        }
        if validation.passed:
            report.pop("failure", None)
        else:
            report["status"] = "failed"
            report["completed_at"] = timestamp_text
            report["failure"] = {
                "stage": "session_validation",
                "message": "; ".join(validation.failures),
            }
        _write_report(report, report_path, temporary_path, mode="w")
    except (OSError, json.JSONDecodeError) as error:
        raise ReportError(f"could not update report {report_path}: {error}") from error


def record_component_result(
    report_path: Path,
    *,
    test_type: str,
    status: str,
    details: dict[str, object],
    now: datetime | None = None,
) -> None:
    """Append one terminal component result and finalize a failed run promptly."""

    timestamp = now or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("report timestamp must be timezone-aware")
    timestamp_text = timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")
    temporary_path = report_path.with_suffix(".json.tmp")
    try:
        with report_path.open("r", encoding="utf-8") as report_file:
            report = json.load(report_file)
        if not isinstance(report, dict) or not isinstance(report.get("results"), list):
            raise ReportError(f"report has invalid result structure: {report_path}")
        report["results"].append(
            {"type": test_type, "status": status, "completed_at": timestamp_text,
             **details}
        )
        if status != "passed":
            report["status"] = "failed"
            report["completed_at"] = timestamp_text
        _write_report(report, report_path, temporary_path, mode="w")
    except (OSError, json.JSONDecodeError) as error:
        raise ReportError(f"could not update report {report_path}: {error}") from error


def finalize_component_run(report_path: Path, *, now: datetime | None = None) -> None:
    """Mark a run passed after every configured component test passed."""

    timestamp = now or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("report timestamp must be timezone-aware")
    timestamp_text = timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")
    temporary_path = report_path.with_suffix(".json.tmp")
    try:
        with report_path.open("r", encoding="utf-8") as report_file:
            report = json.load(report_file)
        if not isinstance(report, dict):
            raise ReportError(f"report is not a JSON object: {report_path}")
        if any(result.get("status") != "passed" for result in report.get("results", [])):
            return
        report["status"] = "passed"
        report["completed_at"] = timestamp_text
        _write_report(report, report_path, temporary_path, mode="w")
    except (OSError, json.JSONDecodeError) as error:
        raise ReportError(f"could not update report {report_path}: {error}") from error


def _write_report(
    report: dict[str, object], report_path: Path, temporary_path: Path, *, mode: str
) -> None:
    with temporary_path.open(mode, encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2, sort_keys=True)
        report_file.write("\n")
        report_file.flush()
    temporary_path.replace(report_path)
