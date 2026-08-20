# Application

This layer owns manufacturing-firmware lifecycle and state. Milestone 4 initializes HAL, delegates board clock setup, verifies `SystemCoreClock`, and enters a stable loop with debugger-visible state and iteration counters.

In Milestone 7 the application loop consumes completed protocol lines after USB transport processing. `session_protocol` dispatches the first `START_TEST` request, while `session_metadata` reads the STM32's immutable 96-bit factory UID and combines it with compiled board and firmware metadata. No component capability is advertised until its component test is actually implemented.

Milestone 9 adds one active component-test slot. `session_protocol` dispatches commands while `component_test_runner` calls the active component's short `process` callback once per main-loop iteration. The runner clears the active slot before invoking `stop`, so a stopped test cannot be processed again. Component-specific behavior does not belong here.
