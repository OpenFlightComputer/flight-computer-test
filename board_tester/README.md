# Board tester

This directory contains the computer-side OpenFlightComputer manufacturing and acceptance-test software.

The package will eventually own configuration loading, tooling checks, firmware flashing, USB protocol communication, operator interaction, test orchestration, and result persistence. Milestone 1 establishes only those boundaries; it does not provide an executable CLI or hardware behavior.

Device UID, MCU identity, board identity, firmware metadata, and capabilities are session-initialization data returned by `START_TEST`. They are validated and recorded before component dispatch and are deliberately not modeled as an `identity` component test.

