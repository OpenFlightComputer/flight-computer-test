# OpenFlightComputer Hardware Test

`flight-computer-test` will be the computer-controlled manufacturing and acceptance-test framework for custom OpenFlightComputer PCBs. Its first supported target is the current STM32F405RGT6 flight computer with a BMI270 IMU, BMP388 barometer, microSD, USB-C, discrete status LEDs, and a WS2812 RGB LED.

This repository is intentionally separate from operational flight-control firmware. The board tester will eventually flash dedicated manufacturing firmware over ST-Link/SWD, communicate with it over USB CDC using newline-delimited JSON, run tests in configuration order, guide operator interactions, and persist traceable results under the STM32 factory UID.

## Project context

The [OpenFlightComputer GitHub organization](https://github.com/OpenFlightComputer) separates hardware, hardware testing, flight firmware, simulation, the drone platform, and project-wide documentation. This repository owns only hardware-test orchestration, manufacturing-test firmware, the board-tester/device protocol, test configuration, and reports. System-level context belongs in the sibling [project-documentation](https://github.com/OpenFlightComputer/project-documentation) repository, while the authoritative KiCad design belongs in [flight-computer-hardware](https://github.com/OpenFlightComputer/flight-computer-hardware).

## Intended architecture

The board tester owns the workflow:

```text
test and board configurations
            |
            v
board-tester runner -> ST-Link flashing -> USB CDC -> manufacturing firmware
        |                                                   |
        v                                                   v
operator interaction and reports                  component tests -> hardware
```

The planned firmware dependency direction is protocol, application/core, component tests, hardware abstraction/drivers, then STM32F405 and board support. Only one component test will be active at a time in V1.

The V1 protocol will use board-tester-initiated `START_TEST`, `RUN_COMPONENT_TEST`, and `STOP_COMPONENT_TEST` commands. Responses correlate through command IDs; asynchronous functional events and non-functional debug messages remain separate.

Board configuration will describe physical hardware. Test configuration will hold a UUID, reference a board configuration, and define ordered tests, parameters, and acceptance limits. Every result will capture SHA-256 hashes of both exact files.

## Current state

Milestone 2 is complete in the working tree: the board tester accepts only `run --config`, validates that the supplied path is a file, and prints a startup summary. It does not read configuration contents or access hardware.

See [DEVELOPMENT.md](DEVELOPMENT.md) for the handoff state, [ROADMAP.md](ROADMAP.md) for planned milestones, [docs/repository-architecture.md](docs/repository-architecture.md) for responsibility boundaries, and [docs/hardware-reference.md](docs/hardware-reference.md) for the reviewed hardware interface.

## Usage

The board tester uses [uv](https://docs.astral.sh/uv/) as its sole Python version and environment manager. uv selects Python from the committed `.python-version`, synchronizes the environment from `pyproject.toml`, and locks the result in `uv.lock`. `pyproject.toml` is standard Python project/package metadata and build configuration, not a competing version-management tool.

Synchronize the uv-managed development environment, then run the standard console entry point:

```bash
uv sync --project board_tester
uv run --project board_tester fc-test run --config configs/test/<test-config>.json
```

Or use the repository-local bootstrap, which delegates to the same uv project and console entry point:

```bash
./fc-test run --config configs/test/<test-config>.json
```

Both routes call `fc_test.main:main` in the locked uv environment. An actual test configuration will be added in Milestone 3.

## Supported hardware

- Board: current Flight Computer V1 design; formal revision identifier still needs reconciliation
- MCU: STM32F405RGT6
- Sensors: BMI270 and BMP388
- Storage: microSD
- Host links: ST-Link/SWD for programming and USB-C/USB CDC for the test protocol
