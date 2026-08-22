# Board tester

This directory contains the computer-side OpenFlightComputer manufacturing and acceptance-test software.

The package owns configuration loading, tooling checks, firmware building, STM32CubeProgrammer/ST-Link flashing, USB CDC discovery/connection/newline framing, session validation, and incremental result persistence. Component-test orchestration enters in a later milestone.

Python versions, dependencies, and the development environment are managed by uv. The committed `.python-version` requests Python 3.12, `pyproject.toml` declares package metadata and compatibility, and `uv.lock` records the resolved environment. These files are complementary parts of one uv workflow rather than separate version managers.

From the repository root, synchronize the uv-managed environment and run the console entry point:

```bash
uv sync --project board_tester
uv run --project board_tester fc-test run --config configs/test/test-config-v003.json
```

The repository also provides a bootstrap that delegates to the same uv project:

```bash
./fc-test run --config configs/test/test-config-v003.json
```

`run` does not depend on prior build or flash commands. It loads configuration, invokes the canonical CMake Release preset, discovers one ST-Link, programs and verifies the generated ELF, resets the target, waits for its USB CDC port, and opens the transport. The same build and flashing services are independently available as:

```bash
./fc-test firmware build
./fc-test firmware build --profile debug
./fc-test firmware flash
./fc-test firmware flash --probe-serial <serial>
./fc-test firmware flash --programmer /custom/path/STM32_Programmer_CLI
```

`firmware flash --firmware <path.elf>` deliberately bypasses compilation for an explicitly supplied artifact. Otherwise flashing always builds first. Install STM32CubeProgrammer for flashing. Its executable is resolved in this order: the `--programmer <path>` command option, `STM32CUBE_PROGRAMMER_CLI`, `PATH`, then the standard macOS application locations. The `run` command accepts the same `--programmer` option.

After reset, `run` polls for up to 10 seconds for exactly one serial port with the development VID/PID `CAFE:4001`. If the operating system reports an unexpected identity or more than one matching board is connected, select the device path explicitly:

```bash
./fc-test run --config configs/test/test-config-v001.json --port /dev/cu.usbmodem...
```

pyserial owns the portable operating-system serial access. The connection disables software and hardware flow control, closes deterministically, and carries bounded raw LF-terminated byte lines. Before any firmware work, every test type in the selected test configuration must appear in the selected board configuration's `test_capabilities`. The first protocol exchange is `START_TEST`: the tester sends the selected test UUID and creates an `in_progress` result only after a valid response. It then checks the returned MCU and board identity plus whether firmware capabilities include every board capability. A failed handshake creates no report; a compatibility failure updates the newly created report to `failed` and stops before component execution.

Zero probes, ambiguous multiple probes or USB ports, programming failure, verification failure, reset failure, missing tools, serial-open failures, and timeouts produce concise errors without Python tracebacks. Programming uses SWD connect-under-reset at 1 MHz, requires immediate verification, and never automatically mass-erases, changes option bytes, or disables protection.

Device UID, MCU identity, board identity, firmware metadata, and capabilities are session-initialization data returned by `START_TEST`. Firmware version and revision are recorded for traceability, while board identity and required capabilities are validated before component dispatch. Firmware may advertise extra capabilities; it cannot omit one declared by the board. These are deliberately not modeled as an `identity` component test.
