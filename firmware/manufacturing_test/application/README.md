# Application

This layer owns manufacturing-firmware lifecycle and state. Milestone 4 initializes HAL, delegates board clock setup, verifies `SystemCoreClock`, and enters a stable loop with debugger-visible state and iteration counters.

In Milestone 7 the application loop consumes completed protocol lines after USB transport processing. `session_protocol` dispatches the first `START_TEST` request, while `session_metadata` reads the STM32's immutable 96-bit factory UID and combines it with compiled board and firmware metadata. No component capability is advertised until its component test is actually implemented.

Protocol/session state and component dispatch will be added in later milestones. Component-specific behavior does not belong here.
