# Repository architecture

## Responsibility map

| Area | Owns | Must not own |
| --- | --- | --- |
| `board_tester/fc_test/configuration.py` | Configuration loading, models, and board/test capability preflight | Test execution and hardware access |
| `board_tester/fc_test/session_validation.py` | Board-to-firmware identity and capability compatibility | Report persistence or component execution |
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

Before flashing, the board tester requires every test type in the selected test configuration to appear in the selected board configuration's explicit `test_capabilities`. After flashing and connecting, it sends `START_TEST`. The response establishes STM32 UID, MCU and board identity, manufacturing-firmware identity, and supported capabilities. The runner records the response, then confirms the identity and that firmware capabilities are a superset of the board capabilities before it dispatches any configured component test.

Consequently there is no `identity` or `mcu_runtime` component test. Successfully reaching `START_TEST_RESPONSE` already proves that clock initialization completed, USB is operational, and the main loop is processing commands. The board advertises the two independently executable status LED tests as `status_led_red` and `status_led_green`; there is no aggregate `status_leds` capability.

## Current implementation boundary

The CLI loads configuration and completes the board/test preflight before reusing shared services to build current manufacturing firmware, discover one ST-Link, program and verify the ELF through STM32CubeProgrammer, reset the target, discover its USB CDC port, exchange `START_TEST`, create an initial local report, and validate the returned board identity and firmware capabilities. A session-validation failure is persisted and stops the workflow. A valid session then executes each enabled test through the correlated start/event/completion/stop protocol, incrementally records component-specific details, finalizes the report, and prints a full summary.

External commands are never passed through a shell. The firmware's USB callbacks perform bounded byte movement only; its main loop frames and parses JSON, services the single active component state machine, and queues responses. Python uses pyserial for portable device access and small per-component handlers for prompts and presentation. Hardware-free tests cover configuration, tooling, framing, protocol, session validation, handlers, reports, firmware state-machine boundaries, WS2812 encoding, and SD CSD parsing. Real SWD, USB, and component behavior are not claimed without a board.
