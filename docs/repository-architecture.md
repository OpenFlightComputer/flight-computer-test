# Repository architecture

## Responsibility map

| Area | Owns | Must not own |
| --- | --- | --- |
| `board_tester/fc_test/configuration.py` | Configuration loading, models, and validation | Test execution and hardware access |
| `board_tester/fc_test/external_tools.py` | Shell-free, captured external-command execution | Tool-specific policy or output parsing |
| `board_tester/fc_test/firmware.py` | CMake preset orchestration and firmware-artifact validation | Compiler, linker, or source configuration |
| `board_tester/fc_test/runner.py` | End-to-end sequencing and initialization | Component-specific behavior |
| `board_tester/fc_test/flashing/` | Installing manufacturing firmware | Communication, reports, or test policy |
| `board_tester/fc_test/protocol/` | Connection, framing, and message correlation | Hardware behavior or acceptance limits |
| `board_tester/fc_test/reporting/` | Incremental persistent results | Test execution |
| `board_tester/fc_test/tests/` | Operator interaction, visualization, and acceptance evaluation | Global ordering |
| `firmware/manufacturing_test/protocol/` | USB transport and message encoding | Components and pin knowledge |
| `firmware/manufacturing_test/application/` | Firmware lifecycle, session state, and component registry | Host workflow and reporting |
| `firmware/manufacturing_test/components/` | Component-specific test behavior and measurements | Global ordering and operator interaction |
| `firmware/manufacturing_test/hardware_abstraction/` | Small peripheral-independent access interfaces | Test policy |
| `firmware/manufacturing_test/drivers/` | Device behavior over hardware abstractions | Board routing and board-tester protocol |
| `firmware/manufacturing_test/board_support/` | Routed pins and STM32/board initialization | Acceptance policy |
| `shared/protocol/` | Implementation-independent protocol contract | Computer or firmware implementation |
| `configs/board/` | Physical board description | Test order and limits |
| `configs/test/` | Ordered test policy and limits | Pin mappings |

## Initialization is not a component test

After flashing and connecting, the board tester will send `START_TEST`. The response establishes STM32 UID, MCU and board identity, manufacturing-firmware identity, and supported capabilities. The runner validates and persists this information before it dispatches any configured component test.

Consequently there is no `identity` test package or capability. The first intended component test is `mcu_runtime`, which evaluates actual clock, timebase, and responsiveness behavior rather than rediscovering session metadata.

## Current implementation boundary

The CLI loads configuration and reuses shared services to build current manufacturing firmware, discover one ST-Link, program and verify the ELF through STM32CubeProgrammer, reset the target, discover its USB CDC port, and open a bounded newline-framed byte transport. External commands are never passed through a shell. The firmware initializes USB CDC and handles OTG FS interrupts; the Python side uses pyserial for portable device discovery and serial access. Structured messages, correlation, reporting, and component-test Python modules remain responsibility markers for later milestones. Hardware-free tests cover the tool, programmer, USB discovery, connection, and framing boundaries, while real SWD and USB success are not claimed without a board.
