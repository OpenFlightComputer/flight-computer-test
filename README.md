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

Board configuration describes physical hardware. Test configuration holds a UUID, references a board configuration, and defines ordered tests, parameters, and acceptance limits. Configuration hashing is deliberately deferred.

## Current state

Milestone 6 is complete and committed. `run` now continues from SWD reset into bounded USB CDC discovery and connection, and raw newline framing is ready for the Milestone 7 message protocol. Physical flashing and USB enumeration remain unverified because STM32CubeProgrammer and hardware are not currently available.

See [DEVELOPMENT.md](DEVELOPMENT.md) for the handoff state, [ROADMAP.md](ROADMAP.md) for planned milestones, [docs/repository-architecture.md](docs/repository-architecture.md) for responsibility boundaries, and [docs/hardware-reference.md](docs/hardware-reference.md) for the reviewed hardware interface.

## Usage

The board tester uses [uv](https://docs.astral.sh/uv/) as its sole Python version and environment manager. uv selects Python from the committed `.python-version`, synchronizes the environment from `pyproject.toml`, and locks the result in `uv.lock`. `pyproject.toml` is standard Python project/package metadata and build configuration, not a competing version-management tool.

Synchronize the uv-managed development environment, then run the standard console entry point:

```bash
uv sync --project board_tester
uv run --project board_tester fc-test firmware build
uv run --project board_tester fc-test run --config configs/test/test-config-v001.json
```

Or use the repository-local bootstrap, which delegates to the same uv project and console entry point:

```bash
./fc-test run --config configs/test/test-config-v001.json
```

Build and flash can also be invoked independently:

```bash
./fc-test firmware build
./fc-test firmware build --profile debug
./fc-test firmware flash
./fc-test firmware flash --probe-serial <serial>
./fc-test firmware flash --programmer /custom/path/STM32_Programmer_CLI
./fc-test run --config configs/test/test-config-v001.json --port /dev/cu.usbmodem...
```

`firmware flash` and `run` build current Release firmware before flashing unless an explicit prebuilt ELF is supplied to `firmware flash`. Both flashing routes accept `--programmer <path>` when STM32CubeProgrammer is installed in a nonstandard location. After reset, `run` waits up to 10 seconds for the development USB identity `CAFE:4001`; use `--port <path>` to select a particular serial port or bypass VID/PID matching. All routes reuse the same Python build and programming services; they do not invoke one another as nested CLI commands.

## Supported hardware

- Board: Flight Computer V1, manufacturing revision 1.7 from schematic revision 0.1
- MCU: STM32F405RGT6
- Sensors: BMI270 and BMP388
- Storage: microSD
- Host links: ST-Link/SWD for programming and USB-C/USB CDC for the test protocol
