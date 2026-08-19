# Development status

## Current milestone

Milestone 2 — Initial CLI startup: **complete**.

Milestone 3 remains pending owner approval before implementation begins.

## Completed

### Milestone 2

- Added the sole V1 command shape: `fc-test run --config <path>`.
- Required both the `run` command and `--config` option through standard-library `argparse` handling.
- Added clear errors for missing paths and paths that are not files without reading or interpreting their contents.
- Routed the validated request from `fc_test.main` to the central runner, which prints only the Milestone 2 startup summary.
- Added the standard `fc-test` console entry point in `pyproject.toml` and an executable repository-root `./fc-test` bootstrap; both invoke the same `fc_test.main:main` implementation.
- Adopted uv as the canonical Python environment manager, pinned Python 3.12, and generated the project lockfile.
- Documented editable installation and repository-local usage.

### Milestone 1

- Added the Python 3.12 `board_tester/fc_test` package skeleton with explicit runner, flashing, protocol, reporting, and component-test boundaries.
- Removed identity from the component-test model. UID, MCU, board, firmware, and capability metadata are part of `START_TEST` session initialization owned by the runner and firmware application layers.
- Added component-test packages named `mcu_runtime`, `status_leds`, `rgb_led`, `imu`, `barometer`, and `sd_card`.
- Added the manufacturing-firmware skeleton with application, protocol, components, hardware abstraction, board support, and driver boundaries.
- Added an intentionally target-free firmware foundation: CMake configures the skeleton but enables no compiler and produces no firmware artifact before Milestone 4.
- Added board/test configuration placeholders and an implementation-independent shared protocol boundary.
- Documented the responsibility map and dependency direction in `docs/repository-architecture.md`.

### Milestone 0

- Confirmed the authoritative hardware working tree at `/Users/jul/Private/projects/flightComputer/flight_computer_pcb/FlightComputer_V1`.
- Inspected the current root schematic, hierarchical sheets, PCB, and an exported KiCad XML netlist without changing the hardware repository.
- Captured the test-relevant component inventory and MCU net mapping in `docs/hardware-reference.md`.
- Checked the exact `OpenFlightComputer` name for a substantial established project/product conflict; none was found.
- Created `flight-computer-test` and `project-documentation` repositories with initial documentation, ignore rules, and contributor guidance.
- Established the `OpenFlightComputer` GitHub organization and transferred the test, documentation, and existing hardware repositories into it.
- Renamed the transferred hardware repository from `flight_computer_pcb` to `flight-computer-hardware` while preserving its private visibility.
- Updated all three local Git remotes to their organization-owned SSH URLs and verified remote access.

## Important decisions

- The uv console command and repository bootstrap are two launch routes, not two CLI implementations. All parsing remains in `fc_test.main`.
- `./fc-test` delegates to `uv run --project board_tester`, ensuring both launch routes use the pinned and locked environment rather than whichever Python happens to be first on `PATH`.
- uv is the sole project-level Python version and environment manager. `.python-version` selects the interpreter, `pyproject.toml` provides standard project/build metadata, and `uv.lock` records uv's resolved environment; setuptools is only the declared package build backend.
- Configuration paths remain relative in the startup display and are resolved by normal filesystem semantics from the operator's working directory; the bootstrap does not change directories.
- Milestone 2 validates only that the supplied path exists and is a file. JSON parsing, schema validation, path resolution between configurations, and hashing remain in Milestone 3.
- Standard `argparse` usage errors return exit code 2; successful help and startup return exit code 0.
- The computer-side software directory is named `board_tester` rather than the ambiguous `host` or `test_station`.
- `identity` is not a test or firmware capability. Session identity is required initialization data and must be persisted before component dispatch.
- The first intended component test is `mcu_runtime`; discrete LED tests use the explicit `status_leds` name.
- Firmware directories use `hardware_abstraction` and `board_support` to distinguish portable access interfaces from routed board definitions.
- Milestone 1 modules are responsibility markers only. No placeholder silently claims that CLI, flashing, transport, reporting, STM32 build, or component behavior works.
- The current KiCad working tree is hardware truth for this milestone. It contains uncommitted owner changes, so its file hashes are recorded alongside the Git commit rather than pretending the commit alone identifies the reviewed design.
- Hardware-derived pin mappings are documented separately from firmware choices. An alternate function is listed only when the intended interface selects it unambiguously; ambiguous choices remain open.
- Local test results are ignored by default because they contain physical device identifiers. A tracked placeholder keeps the result directory available once the Milestone 1 skeleton is created.
- The GitHub organization is the stable public project namespace. Repository names follow kebab-case and subsystem responsibility: `flight-computer-hardware`, `flight-computer-test`, and `project-documentation`.
- The hardware repository remains private pending a deliberate publication review; moving it into the organization did not imply approval to publish it.

## Validation performed

- `uv sync --project board_tester` installed managed Python 3.12.12, created the ignored project environment, built the editable package, and generated the locked environment successfully.
- `uv run --project board_tester fc-test` and the repository-root `./fc-test` bootstrap produced identical startup output for the same valid relative path.
- CLI checks passed for no arguments, an unknown command, missing `--config`, a nonexistent path, a directory path, root help, and `run` help. Usage failures returned exit code 2 and valid/help cases returned 0.
- The exact successful startup output was checked, including blank-line placement and the unchanged relative configuration path.
- All required Milestone 1 directories and boundary files are present; no `identity` test directory exists.
- `board_tester/pyproject.toml` parses and every Python skeleton module imports without bytecode side effects under the available Python 3.14.6 interpreter.
- Milestone 1 imports were initially checked under the available Python 3.14.6 interpreter; Milestone 2 subsequently exercised the declared lower version family with isolated Python 3.12.12.
- CMake is not currently installed or available on `PATH`, so the target-free firmware skeleton could not be configured in this environment. CMake is not required to produce an artifact until Milestone 4.
- Git whitespace validation passes for the complete uncommitted Milestone 1 change set.
- Both test/documentation repository baselines pass Git whitespace checks. Their `main` branches track the transferred organization remotes.
- SSH remote access was verified for all three transferred repositories. The hardware repository's existing uncommitted KiCad work was preserved unchanged.
- KiCad 10.0.4 successfully exported the complete hierarchical schematic as an XML netlist; the documented component and pin mapping was derived from that export and cross-checked against PCB nets.
- Schematic ERC completed and reported 83 pre-existing findings: 78 unspecified-to-bidirectional pin warnings and 5 errors. The errors are four intentionally unused switch mounting/contact pins (SW1/SW2 pins 4 and 5) and one un-driven power-input marker on the SD-card sheet. These remain hardware-repository review items; no suppressions or hardware edits were made here.
- PCB DRC could not complete because `kicad-cli` 10.0.4 terminated with a Swift `Array index out of range` error before producing a report. This is an open tooling/board-validation issue, not a clean DRC result.

## Open issues and assumptions

- Homebrew Python was upgraded from 3.14.6 to 3.14.7, but `pyexpat`, `venv`, and pip bootstrapping still fail on macOS 26.2 because the bottle expects an Expat symbol absent from that OS release. This is a known Homebrew/macOS issue; macOS 26.3 or later is the supported system-level fix. The uv-managed project environment is unaffected.
- Install CMake before the Milestone 4 firmware build foundation. The current Milestone 1 `CMakeLists.txt` is intentionally target-free and remains unexecuted locally because the tool is unavailable.
- Reconcile the formal board revision before creating the Milestone 3 board configuration: the schematic title block says revision `0.1`, while generated production files include names through `flightcomputer_v1.7_*`.
- Choose and document the BMI270 MCU SPI instance. PB3/PB4/PB5 support more than one SPI alternate-function mapping; the routed hardware does not itself select one.
- Confirm whether PC10/PC11 (`RP1_RX`/`RP1_TX`) are intended to use UART4 or USART3 and document signal naming from both MCU and external-device perspectives.
- Confirm the intended timer/output mode for PC6–PC9 ESC signals when motor-interface testing enters scope; it is explicitly outside V1.
- Resolve the discrete LED polarity before Milestone 11. Both the exported schematic netlist and PCB connect D4/D5 pin 2 (`A`) to GND and pin 1 (`K`) toward the MCU through a resistor, which appears reversed for the standard KiCad LED symbol.
- Validate WS2812 input-high margin on hardware. LED1 is powered from +5 V while its data input is driven directly from a 3.3 V MCU through R24, with no level shifter shown.
- Investigate the KiCad CLI DRC crash and obtain a complete DRC report before treating the current PCB as manufacturing-verified.

## Next milestone

Milestone 3 will implement board/test configuration loading, referenced board-path resolution, UUID and basic schema validation, deterministic SHA-256 hashes, ordered enabled-test preservation, and the initial hardware-derived configuration files. It will not flash firmware, connect hardware, open serial communication, or execute component tests.
