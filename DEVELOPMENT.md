# Development status

## Current milestone

Milestone 1 — Repository skeleton and architecture: **complete in the working tree, pending owner review**.

Stop here until the project owner reviews the changes and separately approves any commit and Milestone 2.

## Completed

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

- All required Milestone 1 directories and boundary files are present; no `identity` test directory exists.
- `board_tester/pyproject.toml` parses and every Python skeleton module imports without bytecode side effects under the available Python 3.14.6 interpreter.
- The exact Python 3.12 lower bound is not installed locally, so minimum-version compatibility was not exercised; the available Python 3.14.6 interpreter satisfies the declared Python 3.12+ requirement.
- CMake is not currently installed or available on `PATH`, so the target-free firmware skeleton could not be configured in this environment. CMake is not required to produce an artifact until Milestone 4.
- Git whitespace validation passes for the complete uncommitted Milestone 1 change set.
- Both test/documentation repository baselines pass Git whitespace checks. Their `main` branches track the transferred organization remotes.
- SSH remote access was verified for all three transferred repositories. The hardware repository's existing uncommitted KiCad work was preserved unchanged.
- KiCad 10.0.4 successfully exported the complete hierarchical schematic as an XML netlist; the documented component and pin mapping was derived from that export and cross-checked against PCB nets.
- Schematic ERC completed and reported 83 pre-existing findings: 78 unspecified-to-bidirectional pin warnings and 5 errors. The errors are four intentionally unused switch mounting/contact pins (SW1/SW2 pins 4 and 5) and one un-driven power-input marker on the SD-card sheet. These remain hardware-repository review items; no suppressions or hardware edits were made here.
- PCB DRC could not complete because `kicad-cli` 10.0.4 terminated with a Swift `Array index out of range` error before producing a report. This is an open tooling/board-validation issue, not a clean DRC result.

## Open issues and assumptions

- Install CMake before the Milestone 4 firmware build foundation. The current Milestone 1 `CMakeLists.txt` is intentionally target-free and remains unexecuted locally because the tool is unavailable.
- Reconcile the formal board revision before creating the Milestone 3 board configuration: the schematic title block says revision `0.1`, while generated production files include names through `flightcomputer_v1.7_*`.
- Choose and document the BMI270 MCU SPI instance. PB3/PB4/PB5 support more than one SPI alternate-function mapping; the routed hardware does not itself select one.
- Confirm whether PC10/PC11 (`RP1_RX`/`RP1_TX`) are intended to use UART4 or USART3 and document signal naming from both MCU and external-device perspectives.
- Confirm the intended timer/output mode for PC6–PC9 ESC signals when motor-interface testing enters scope; it is explicitly outside V1.
- Resolve the discrete LED polarity before Milestone 11. Both the exported schematic netlist and PCB connect D4/D5 pin 2 (`A`) to GND and pin 1 (`K`) toward the MCU through a resistor, which appears reversed for the standard KiCad LED symbol.
- Validate WS2812 input-high margin on hardware. LED1 is powered from +5 V while its data input is driven directly from a 3.3 V MCU through R24, with no level shifter shown.
- Investigate the KiCad CLI DRC crash and obtain a complete DRC report before treating the current PCB as manufacturing-verified.

## Next milestone

Milestone 2 will implement only the initial `fc-test run --config <path>` startup: argument parsing, the required command and option, path-existence validation, and a clear startup summary. It will not interpret configuration semantics, connect hardware, flash firmware, open serial communication, or execute tests.
