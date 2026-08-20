# Protocol specification

This directory holds the implementation-independent board-tester/device protocol contract. It is the shared source of message semantics for the board tester and manufacturing firmware, not a place for either implementation.

V1 uses UTF-8, newline-delimited JSON. The current protocol version is `1` and its first command is board-tester initiated `START_TEST`:

```json
{"protocol_version":1,"type":"START_TEST","command_id":1,"test_uuid":"<uuid-v4>"}
```

The device responds with `START_TEST_RESPONSE`, echoes `command_id`, and supplies its factory UID, compiled board/firmware identity, and the executable component capabilities. The tester creates an `in_progress` result only after it has received and validated that response. Malformed or unsupported requests receive an `ERROR` response. The firmware lifecycle uses `RUN_COMPONENT_TEST` with a lowercase underscore-separated `test_type`, and `STOP_COMPONENT_TEST` while one test is active. It returns `TEST_STARTED`, zero or more `TEST_EVENT` messages, then `TEST_COMPLETED`; stopping returns `TEST_STOPPED`. Each lifecycle message carries the correlated command ID and test type. The board-tester-side orchestration for these messages remains deferred.
