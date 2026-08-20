# Development status

## Current milestone

Milestone 6 — USB CDC transport and newline framing: **complete and committed**.

Milestone 7 — protocol foundation, `START_TEST`, metadata, and initial report creation — is next. Its scope requires owner review before implementation.

## Completed

### Milestone 6 — board-tester side

- Added pyserial as the uv-managed serial dependency and locked version 3.5.
- Added ten-second post-reset USB enumeration polling for the firmware's development `CAFE:4001` VID/PID and deterministic zero/one/multiple-device behavior.
- Added `run --port <path>` to select an exact serial device and bypass VID/PID matching when required by the local installation or development identity.
- Added an owned USB CDC connection with finite reads and writes, disabled flow control, actionable errors, partial-write handling, and guaranteed close behavior.
- Added raw-byte LF framing with CRLF acceptance, a 4,096-byte maximum, fragmented and combined input support, ordered oversized-line rejection, and recovery at the following newline.
- Extended `run` to discover and open USB CDC immediately after programming, verification, and reset without sending Milestone 7 messages yet.

### Milestone 6 — firmware side (committed as `3258b72`)

- Added the official pinned STM32CubeF4 USB Device core and CDC class to the manufacturing-firmware build with the required HAL PCD/low-level USB drivers.
- Configured PA11/PA12 for OTG FS, PA9 VBUS sensing, bus-powered descriptors, static USB class storage, and the OTG FS interrupt at priority 6.
- Added CMake-configurable `0xCAFE:0x4001` development-only VID/PID placeholders and explicit warnings that they are unassigned and unsuitable for distribution.
- Added CDC descriptors without a serial-number descriptor; STM32 UID identity remains deferred to Milestone 7.
- Added a 512-byte interrupt-to-main receive ring, two-line receive/transmit queues, asynchronous transmission completion, and observable bounded-drop counters without dynamic allocation.
- Added LF framing with CRLF acceptance, a 4,096-byte maximum, discard-through-newline recovery, and native C tests for split packets, combined lines, maximum length, overflow, and recovery.

### Milestone 5

- Added reusable external-command, firmware-build, programmer-neutral flashing, STM32CubeProgrammer/ST-Link, and build-and-flash workflow boundaries.
- Added `fc-test firmware build` with Release default and optional Debug profile while preserving CMake as the single build definition.
- Added `fc-test firmware flash`, which builds by default and supports an explicit prebuilt ELF or ST-Link serial when deliberate selection is needed.
- Extended `fc-test run` to load configuration, build current firmware, discover one probe, program and verify over SWD, and reset without assuming earlier commands ran.
- Located STM32CubeProgrammer through an explicit environment override, `PATH`, or the documented macOS application locations.
- Added deterministic zero/one/multiple-probe handling, 1 MHz connect-under-reset commands, bounded timeouts, shell-free arguments, and actionable failures without automatic mass erase, option-byte changes, or read-protection removal.
- Added hardware-free tests for build sequencing, artifact validation, probe parsing and selection, shared workflow reuse, programming-before-reset, command construction, and clean error reporting.

### Milestone 4

- Replaced the target-free skeleton with a CMake/Ninja cross-compilation project for STM32F405RGT6 using C11 and ARM hard-float Cortex-M4 settings.
- Pinned official STM32CubeF4 `v1.28.3` as a Git submodule and initialized only the required CMSIS device and HAL driver revisions.
- Added the STM32F405 startup path, 1 MiB Flash/128 KiB SRAM/64 KiB CCM linker map, minimal HAL configuration, core interrupt handlers, and newlib startup hooks.
- Configured the board's 16 MHz HSE through PLLM 16, PLLN 336, PLLP 2, and PLLQ 7 for 168 MHz SYSCLK and the later 48 MHz USB clock.
- Added a stable application loop with debugger-visible boot, ready, and clock-error states without relying on unresolved LED behavior.
- Embedded firmware `0.1.0`, Git revision/dirty state, STM32CubeF4, and ARM compiler metadata without a nondeterministic build timestamp.
- Added Debug and Release presets, IDE compile-command export, ELF/HEX/BIN/map generation, memory-usage output, dependency setup, clock, build, and hardware-validation documentation.

### Milestone 3

- Added typed board/test configuration models and dependency-free JSON loading.
- Added strict top-level schema, required-field, UUID v4, supported-test, duplicate-test, enabled-flag, parameter-object, and referenced-file validation with source-oriented errors.
- Resolved the board configuration path relative to the test configuration file rather than the operator's working directory.
- Preserved the exact configured test order while providing a filtered enabled-test view.
- Added the hardware-derived Flight Computer V1 board configuration, recording manufacturing revision 1.7 separately from source schematic revision 0.1 and leaving ambiguous firmware selections explicit.
- Added immutable initial acceptance configuration `test-config-v001.json` without an identity component test.
- Updated the hardware-free CLI summary to show board, revision, MCU, test configuration, UUID, and enabled test order.
- Deferred configuration hashing by owner decision.

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

- Milestone 6 is split deliberately: firmware USB CDC and framing are reviewed before computer-side serial discovery and connection are implemented.
- The default USB VID/PID is a configurable development placeholder, not an identity assigned to OpenFlightComputer. Distributed hardware requires an authorized VID/PID.
- USB callbacks do bounded byte movement only. Newline assembly and outgoing scheduling run from the main application loop rather than the OTG FS interrupt.
- CDC input accepts LF and CRLF, limits a line to 4,096 bytes, and discards a damaged/oversized line until the next LF so partial data cannot be mistaken for a command.
- Computer-side framing remains raw bytes in Milestone 6. UTF-8/JSON messages and correlation belong to Milestone 7 rather than the serial transport.
- `run` waits up to 10 seconds after reset for exactly one `CAFE:4001` device. An exact `--port` override bypasses VID/PID matching; multiple automatic matches require explicit selection.
- pyserial provides portable enumeration and serial I/O, while the project owns selection policy, timeouts, connection lifetime, and framing.

- `firmware build`, `firmware flash`, and `run` call shared Python services rather than invoking one another as subprocesses. CMake remains the only firmware build definition, and Ninja keeps repeated builds incremental.
- Normal `firmware flash` and every `run` build current firmware first. Only the explicit `firmware flash --firmware <ELF>` route bypasses compilation.
- Release is the manufacturing default; Debug is an explicit operator choice. ELF is the canonical programming input because it carries linked addresses.
- V1 automatically accepts exactly one ST-Link. Zero probes fail with connection guidance, multiple probes require `--probe-serial`, and an unknown requested serial lists what was discovered.
- STM32CubeProgrammer is an external official tool invoked without a shell. This project does not implement the ST-Link or SWD wire protocols in Python.
- A nonstandard STM32CubeProgrammer installation can be selected explicitly with `--programmer <path>`; this takes precedence over `STM32CUBE_PROGRAMMER_CLI`, `PATH`, and standard macOS application locations.
- Programming uses SWD connect-under-reset at 1 MHz, verification is mandatory before reset, and potentially destructive recovery or security operations are never automatic.
- CMake describes targets and generates the build graph; Ninja executes it. The canonical build remains IDE-independent.
- Arm GNU Toolchain `15.3.rel1` is the tested complete bare-metal toolchain. Homebrew's similarly named `arm-none-eabi-gcc` formula is compiler-only and lacks newlib, so it is not sufficient for this project.
- STM32CubeF4 is pinned by the repository's submodule pointer rather than downloaded implicitly during every configure. Only the CMSIS STM32F4 device package and STM32F4 HAL driver nested submodules are required.
- The manufacturing firmware version has a single source in CMake. The configured header adds Git, STM32CubeF4, and compiler identities to a retained ELF metadata section.
- HSE failure is a manufacturing fault. Clock initialization stops in an inspectable error state instead of silently hiding the fault with an HSI fallback.
- No status LED is used as a heartbeat because the routed LED polarity still requires hardware confirmation; application state and loop counters can be inspected through a debugger later.
- The uv console command and repository bootstrap are two launch routes, not two CLI implementations. All parsing remains in `fc_test.main`.
- `./fc-test` delegates to `uv run --project board_tester`, ensuring both launch routes use the pinned and locked environment rather than whichever Python happens to be first on `PATH`.
- uv is the sole project-level Python version and environment manager. `.python-version` selects the interpreter, `pyproject.toml` provides standard project/build metadata, and `uv.lock` records uv's resolved environment; setuptools is only the declared package build backend.
- The CLI test-configuration path follows normal filesystem semantics from the operator's working directory; the referenced board path is resolved relative to that test configuration file.
- Milestone 2 validates the supplied CLI path before Milestone 3 loads its JSON contents and resolves the referenced board file.
- Configuration UUID identifies the logical immutable test procedure. Configuration hashes are not currently part of the runtime model and will be introduced later.
- The test array is the sole ordering authority. Disabled definitions remain loaded in their original positions but are omitted from the enabled execution view.
- Test and board configuration fields are intentionally strict at their defined schema boundaries so spelling mistakes fail with useful errors rather than becoming ignored policy.
- Standard `argparse` usage errors return exit code 2; successful help and startup return exit code 0.
- The computer-side software directory is named `board_tester` rather than the ambiguous `host` or `test_station`.
- `identity` is not a test or firmware capability. Session identity is required initialization data and must be persisted before component dispatch.
- The first intended component test is `mcu_runtime`; discrete LED tests use the explicit `status_leds` name.
- Firmware directories use `hardware_abstraction` and `board_support` to distinguish portable access interfaces from routed board definitions.
- At Milestone 1, modules were responsibility markers only and no placeholder claimed unimplemented behavior. Later milestones replace each marker with tested behavior at its boundary.
- The current KiCad working tree is hardware truth for this milestone. It contains uncommitted owner changes, so its file hashes are recorded alongside the Git commit rather than pretending the commit alone identifies the reviewed design.
- Hardware-derived pin mappings are documented separately from firmware choices. An alternate function is listed only when the intended interface selects it unambiguously; ambiguous choices remain open.
- Local test results are ignored by default because they contain physical device identifiers. A tracked placeholder keeps the result directory available once the Milestone 1 skeleton is created.
- The GitHub organization is the stable public project namespace. Repository names follow kebab-case and subsystem responsibility: `flight-computer-hardware`, `flight-computer-test`, and `project-documentation`.
- The hardware repository remains private pending a deliberate publication review; moving it into the organization did not imply approval to publish it.

## Validation performed

- The Milestone 6 firmware builds in both Debug and Release with the official pinned USB Device core, CDC class, HAL PCD, and low-level USB driver linked without unresolved symbols.
- Native C tests exercise newline fragmentation across input chunks, multiple lines in one chunk, CRLF handling, the exact 4,096-byte limit, oversized-line rejection, and recovery at the following newline.
- The Release image now uses 18,232 bytes of Flash and 26,372 bytes of statically allocated RAM, including bounded USB queues and the configured heap/stack allowance.
- ELF inspection confirms `OTG_FS_IRQHandler`, the newline framer, USB descriptors, and CDC transport initialization are linked into the manufacturing image.
- All 45 board-tester tests pass under uv-managed Python 3.12, including USB discovery retries and selection, connection closure, fragmented/multiple/oversized framing, read timeout retention, partial writes, CLI/runner integration, and the 31 prior regressions.
- `./fc-test firmware build` successfully configured and incrementally built the real Release firmware from outside the firmware directory, returning the expected absolute ELF path.
- `./fc-test firmware flash` and the integrated `./fc-test run --config configs/test/test-config-v001.json` both built first and then stopped with the same concise missing-STM32CubeProgrammer error and exit code 1, without a traceback or hardware access.
- All 31 standard-library unit tests pass under the uv-managed Python 3.12 environment, including the original configuration/runner regressions and the build/flashing cases.
- Python bytecode compilation succeeds for all board-tester implementation and test modules with warnings treated as errors in the unit suite.
- Clean Debug and Release configurations build with CMake 4.4.2, Ninja 1.13.2, ARM GNU Toolchain 15.3.rel1/GCC 15.3.1, and STM32CubeF4 v1.28.3.
- Both configurations compile project C with strict warnings as errors, link without unresolved symbols, and generate ELF, HEX, BIN, map, and IDE compile-command artifacts.
- Before USB support, the Milestone 4 Release image used 3,508 bytes of Flash and reserved 2,584 bytes of RAM; current Milestone 6 figures are recorded above.
- ELF inspection confirms a 32-bit little-endian ARM hard-float executable, vector table at `0x08000000`, Thumb reset entry at `0x080002e1`, stack top at `0x20020000`, retained firmware metadata, and no unresolved symbols.
- The original 13 configuration/runner tests cover successful initial loading, relative path resolution independent of working directory, ordered enabled/disabled behavior, malformed JSON, UUID version/canonical form, unsupported and duplicate test types, missing board references, unknown fields, unsupported board schema versions, revision consistency, exact CLI output, and clean CLI error reporting.
- At Milestone 3, the repository-root `./fc-test run --config configs/test/test-config-v001.json` command loaded both configurations and printed the six enabled tests without hardware access. Milestone 5 now continues into build and programmer preflight.
- Both initial configuration files parse as valid JSON, and Git whitespace validation passes.
- `uv sync --project board_tester` installed managed Python 3.12.12, created the ignored project environment, built the editable package, and generated the locked environment successfully.
- `uv run --project board_tester fc-test` and the repository-root `./fc-test` bootstrap produced identical startup output for the same valid relative path.
- CLI checks passed for no arguments, an unknown command, missing `--config`, a nonexistent path, a directory path, root help, and `run` help. Usage failures returned exit code 2 and valid/help cases returned 0.
- The exact successful startup output was checked, including blank-line placement and the unchanged relative configuration path.
- All required Milestone 1 directories and boundary files are present; no `identity` test directory exists.
- `board_tester/pyproject.toml` parses and every Python skeleton module imports without bytecode side effects under the available Python 3.14.6 interpreter.
- Milestone 1 imports were initially checked under the available Python 3.14.6 interpreter; Milestone 2 subsequently exercised the declared lower version family with isolated Python 3.12.12.
- Git whitespace validation passes for the complete uncommitted Milestone 1 change set.
- Both test/documentation repository baselines pass Git whitespace checks. Their `main` branches track the transferred organization remotes.
- SSH remote access was verified for all three transferred repositories. The hardware repository's existing uncommitted KiCad work was preserved unchanged.
- KiCad 10.0.4 successfully exported the complete hierarchical schematic as an XML netlist; the documented component and pin mapping was derived from that export and cross-checked against PCB nets.
- Schematic ERC completed and reported 83 pre-existing findings: 78 unspecified-to-bidirectional pin warnings and 5 errors. The errors are four intentionally unused switch mounting/contact pins (SW1/SW2 pins 4 and 5) and one un-driven power-input marker on the SD-card sheet. These remain hardware-repository review items; no suppressions or hardware edits were made here.
- PCB DRC could not complete because `kicad-cli` 10.0.4 terminated with a Swift `Array index out of range` error before producing a report. This is an open tooling/board-validation issue, not a clean DRC result.

## Open issues and assumptions

- `0xCAFE:0x4001` is only a configurable local-development USB identity and may collide with other devices. OpenFlightComputer needs an authorized VID/PID before distributing USB-enabled hardware.
- USB enumeration, VBUS sensing through the board divider, endpoint transfer, disconnect/reconnect behavior, and host compatibility cannot be accepted until hardware is available.
- STM32CubeProgrammer is not installed on this Mac, and no ST-Link or Flight Computer board is available. Discovery, real programming, verification, and reset therefore remain hardware/tool acceptance items despite full mocked boundary coverage.
- Homebrew Python was upgraded from 3.14.6 to 3.14.7, but `pyexpat`, `venv`, and pip bootstrapping still fail on macOS 26.2 because the bottle expects an Expat symbol absent from that OS release. This is a known Homebrew/macOS issue; macOS 26.3 or later is the supported system-level fix. The uv-managed project environment is unaffected.
- Hardware is not currently available. HSE startup, 168 MHz operation, application-loop execution, and SWD flashing remain on-board validation items rather than claimed results.
- Choose and document the BMI270 MCU SPI instance. PB3/PB4/PB5 support more than one SPI alternate-function mapping; the routed hardware does not itself select one.
- Confirm whether PC10/PC11 (`RP1_RX`/`RP1_TX`) are intended to use UART4 or USART3 and document signal naming from both MCU and external-device perspectives.
- Confirm the intended timer/output mode for PC6–PC9 ESC signals when motor-interface testing enters scope; it is explicitly outside V1.
- Resolve the discrete LED polarity before Milestone 11. Both the exported schematic netlist and PCB connect D4/D5 pin 2 (`A`) to GND and pin 1 (`K`) toward the MCU through a resistor, which appears reversed for the standard KiCad LED symbol.
- Validate WS2812 input-high margin on hardware. LED1 is powered from +5 V while its data input is driven directly from a 3.3 V MCU through R24, with no level shifter shown.
- Investigate the KiCad CLI DRC crash and obtain a complete DRC report before treating the current PCB as manufacturing-verified.

## Next milestone

After review and commit of the board-tester half, Milestone 7 will define structured protocol messages, implement `START_TEST`, validate and persist the initial device metadata, and create the initial report. End-to-end USB acceptance still requires a board.
