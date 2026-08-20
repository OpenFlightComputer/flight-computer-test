# Components

Each component package exposes a `start`, non-blocking `process`, event, and `stop` lifecycle to the static application registry and uses hardware abstractions or device drivers for low-level access. `process` may report that it is still running, emit a named event, pass, or fail; it must return promptly so the main loop can handle USB commands. Components do not own global test ordering, operator interaction, or report files.

The production registry is intentionally empty until a real component test is implemented. It is the sole source for both runnable test lookup and the capability list returned by `START_TEST`.
