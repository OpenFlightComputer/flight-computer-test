# Protocol specification

This directory will hold the implementation-independent board-tester/device protocol contract. It is the shared source of message semantics for the board tester and manufacturing firmware, not a place for either implementation.

The normative machine-readable specification is deferred until the protocol milestone. V1 is already constrained to newline-delimited JSON and the `START_TEST`, `RUN_COMPONENT_TEST`, and `STOP_COMPONENT_TEST` lifecycle commands.
