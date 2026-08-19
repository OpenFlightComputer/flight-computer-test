# Repository architecture

## Responsibility map

| Area | Owns | Must not own |
| --- | --- | --- |
| `board_tester/fc_test/configuration.py` | Configuration loading, models, and validation | Test execution and hardware access |
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

The CLI and configuration subsystem are implemented without hardware dependencies. Firmware directories and the flashing, protocol, reporting, and component-test Python modules remain responsibility markers; later milestones will populate those boundaries one vertical slice at a time.
