# Contributor guidance

This repository contains manufacturing and acceptance-test software for OpenFlightComputer hardware. It does not contain operational flight-control firmware.

Work milestone by milestone. Read `DEVELOPMENT.md` before making changes, update it when a milestone ends, and stop for owner approval before beginning the next milestone.

Keep these boundaries explicit:

- KiCad and manufacturing outputs in the hardware repository are hardware truth.
- Board configuration describes physical hardware.
- Test configuration defines ordered policy and acceptance limits.
- The host owns orchestration, operator interaction, validation, and reporting.
- Manufacturing firmware owns low-level access and component-test execution.
- Component tests depend on small hardware abstractions rather than scattered STM32 HAL calls.

Do not guess routed pins or silently modify a historical test configuration. Do not add flight firmware, GUI work, CI/CD, binary protocol encoding, DFU, a custom bootloader, automated fixtures, or speculative MCU/board support unless the active milestone explicitly requires it.

Preserve result traceability to the STM32 UID, exact board/test configuration hashes, test UUID, firmware version/commit, and timestamps. Prefer simple, deterministic, inspectable behavior.
