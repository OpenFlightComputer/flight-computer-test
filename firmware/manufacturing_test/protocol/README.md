# Protocol

This layer owns USB CDC transport and newline framing. It must not know component models, routed pins, or acceptance limits.

`usb_cdc_transport` initializes the official ST USB Device CDC class and provides bounded receive and transmit queues. USB interrupt callbacks only copy packet bytes, re-arm reception, or mark transmission complete. `usb_cdc_transport_process()` runs framing and starts queued transmissions from the normal application loop.

`newline_framer` treats LF as the message boundary, accepts CRLF, permits at most 4,096 bytes before the terminator, and discards an overflowing line until its next LF. It has no USB or STM32 dependency and is tested with the native compiler.

JSON parsing and serialization, command receipt, and response/event/debug message semantics remain deferred to Milestone 7.
