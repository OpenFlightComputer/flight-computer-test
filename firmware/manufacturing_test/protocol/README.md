# Protocol

This layer owns USB CDC transport and newline framing. It must not know component models, routed pins, or acceptance limits.

`usb_cdc_transport` initializes the official ST USB Device CDC class and provides bounded receive and transmit queues. USB interrupt callbacks only copy packet bytes, re-arm reception, or mark transmission complete. `usb_cdc_transport_process()` runs framing and starts queued transmissions from the normal application loop.

`newline_framer` treats LF as the message boundary, accepts CRLF, permits at most 4,096 bytes before the terminator, and discards an overflowing line until its next LF. It has no USB or STM32 dependency and is tested with the native compiler.

Milestone 7 adds `json_protocol`, which uses the vendored MIT-licensed [jsmn](https://github.com/zserge/jsmn) tokenizer with a fixed 16-token buffer and no dynamic allocation. Milestone 9 adds strict `RUN_COMPONENT_TEST` and `STOP_COMPONENT_TEST` command shapes plus bounded lifecycle messages. USB callbacks still only move bytes; application-loop code reads completed lines, parses JSON, and queues response lines.

JSON parsing and serialization, command receipt, and response/event/debug message semantics remain deferred to Milestone 7.
