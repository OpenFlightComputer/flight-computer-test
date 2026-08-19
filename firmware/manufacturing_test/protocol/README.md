# Protocol

The protocol layer will own USB CDC transport, newline framing, JSON parsing and serialization, command receipt, and response/event/debug transmission. It must not know component models, routed pins, or acceptance limits.

