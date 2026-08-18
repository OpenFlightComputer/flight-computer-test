# Development status

## Current milestone

Milestone 0 — Environment, repositories, and hardware reference: **complete locally**.

Stop here until the project owner approves Milestone 1.

## Completed

- Confirmed the authoritative hardware working tree at `/Users/jul/Private/projects/flightComputer/flight_computer_pcb/FlightComputer_V1`.
- Inspected the current root schematic, hierarchical sheets, PCB, and an exported KiCad XML netlist without changing the hardware repository.
- Captured the test-relevant component inventory and MCU net mapping in `docs/hardware-reference.md`.
- Checked the exact `OpenFlightComputer` name for a substantial established project/product conflict; none was found.
- Created local `flight-computer-test` and `project-documentation` repositories with initial documentation, ignore rules, and contributor guidance.

## Important decisions

- The current KiCad working tree is hardware truth for this milestone. It contains uncommitted owner changes, so its file hashes are recorded alongside the Git commit rather than pretending the commit alone identifies the reviewed design.
- Hardware-derived pin mappings are documented separately from firmware choices. An alternate function is listed only when the intended interface selects it unambiguously; ambiguous choices remain open.
- Local test results are ignored by default because they contain physical device identifiers. A tracked placeholder keeps the result directory available once the Milestone 1 skeleton is created.
- Public GitHub repositories were not created because `gh auth status` reports that the saved token for `juweske` is invalid.

## Validation performed

- Both local repositories pass `git show --check` after the final amend and have clean working trees.
- KiCad 10.0.4 successfully exported the complete hierarchical schematic as an XML netlist; the documented component and pin mapping was derived from that export and cross-checked against PCB nets.
- Schematic ERC completed and reported 83 pre-existing findings: 78 unspecified-to-bidirectional pin warnings and 5 errors. The errors are four intentionally unused switch mounting/contact pins (SW1/SW2 pins 4 and 5) and one un-driven power-input marker on the SD-card sheet. These remain hardware-repository review items; no suppressions or hardware edits were made here.
- PCB DRC could not complete because `kicad-cli` 10.0.4 terminated with a Swift `Array index out of range` error before producing a report. This is an open tooling/board-validation issue, not a clean DRC result.

## Open issues and assumptions

- Reconcile the formal board revision before creating the Milestone 3 board configuration: the schematic title block says revision `0.1`, while generated production files include names through `flightcomputer_v1.7_*`.
- Choose and document the BMI270 MCU SPI instance. PB3/PB4/PB5 support more than one SPI alternate-function mapping; the routed hardware does not itself select one.
- Confirm whether PC10/PC11 (`RP1_RX`/`RP1_TX`) are intended to use UART4 or USART3 and document signal naming from both MCU and external-device perspectives.
- Confirm the intended timer/output mode for PC6–PC9 ESC signals when motor-interface testing enters scope; it is explicitly outside V1.
- Resolve the discrete LED polarity before Milestone 11. Both the exported schematic netlist and PCB connect D4/D5 pin 2 (`A`) to GND and pin 1 (`K`) toward the MCU through a resistor, which appears reversed for the standard KiCad LED symbol.
- Validate WS2812 input-high margin on hardware. LED1 is powered from +5 V while its data input is driven directly from a 3.3 V MCU through R24, with no level shifter shown.
- Investigate the KiCad CLI DRC crash and obtain a complete DRC report before treating the current PCB as manufacturing-verified.
- Re-authenticate GitHub CLI and create/push `flight-computer-test` and `project-documentation` remotes when desired.

## Next milestone

Milestone 1 will add the documented repository skeleton only: host package boundaries, firmware architectural directories, shared protocol/config/docs/results directories, and placeholder module documentation. It will not implement USB, flashing, sensors, configuration semantics, or test execution.
