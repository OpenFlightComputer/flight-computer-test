# Roadmap

Development proceeds one accepted milestone at a time. The current status is recorded in `DEVELOPMENT.md`.

## V1 milestones

1. Repository skeleton and architecture
2. Minimal `fc-test run --config <path>` startup
3. Configuration loading, validation, ordered tests, and UUID checks
4. Buildable STM32F405 manufacturing-firmware foundation
5. ST-Link/SWD flashing through STM32CubeProgrammer CLI
6. USB CDC transport and newline framing
7. Protocol foundation, `START_TEST`, metadata, and initial report creation
8. Capability and session validation
9. Generic component start/event/stop lifecycle
10. Discrete status LED tests
11. WS2812 configurable-colour operator test
12. BMI270 communication, stationary, and movement tests
13. BMP388 functional and plausibility tests
14. microSD write/read/checksum/cleanup test
15. Complete one-command V1 acceptance workflow

## Near term

- All onboard V1 component tests
- Stronger configuration validation
- Refined result schemas
- Automated board-tester unit tests

## Later

- USB DFU manufacturing-firmware flashing
- Automatic flight-firmware flashing after PASS
- Multimeter-guided GPIO and oscilloscope-assisted tests
- ESC/motor output validation
- Alternative sensors, PCB revisions, and MCU families including STM32H7
- Automated fixtures
- Web UI
- CI/CD
- Generated board-tester/firmware protocol bindings
- Configuration authoring tools
- Deterministic board/test configuration hashing and result traceability
- Historical result analysis and cross-run regression comparison

## Long term

Reuse the framework for newer flight computers and other OpenFlightComputer electronics such as ESC, sensor, and embedded subsystem boards.
