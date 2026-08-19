# Application

This layer owns manufacturing-firmware lifecycle and state. Milestone 4 initializes HAL, delegates board clock setup, verifies `SystemCoreClock`, and enters a stable loop with debugger-visible state and iteration counters.

Protocol/session state and component dispatch will be added in later milestones. Component-specific behavior does not belong here.
