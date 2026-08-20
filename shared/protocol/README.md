# Protocol specification

This directory holds the implementation-independent board-tester/device protocol contract. It is the shared source of message semantics for the board tester and manufacturing firmware, not a place for either implementation.

V1 uses UTF-8, newline-delimited JSON. The current protocol version is `1` and its first command is board-tester initiated `START_TEST`:

```json
{"protocol_version":1,"type":"START_TEST","command_id":1,"test_uuid":"<uuid-v4>"}
```

The device responds with `START_TEST_RESPONSE`, echoes `command_id`, and supplies its factory UID, compiled board/firmware identity, and the executable component capabilities. The tester creates an `in_progress` result only after it has received and validated that response. Malformed or unsupported requests receive an `ERROR` response. `RUN_COMPONENT_TEST` and `STOP_COMPONENT_TEST` are deferred to the lifecycle milestone.
