# Board configurations

Board configurations describe physical hardware: board identity and revision, MCU, installed components, buses, routed pins, and `test_capabilities`. They are derived from hardware truth and remain separate from test policy.

`test_capabilities` is the complete set of supported tester component-test types for that board. The selected test configuration may use any subset, but every configured test type must be declared here before the tester builds or flashes firmware. After `START_TEST`, firmware must advertise at least this same set; extra firmware capabilities are allowed.

`flightcomputer-v1.json` describes manufacturing revision 1.7. That manufacturing release was generated from the KiCad schematic whose title block remains at revision 0.1, so both values are recorded explicitly rather than treating them as contradictory revisions.

Configuration and hardware-source hashing is deliberately deferred. Firmware choices that cannot be established from routing alone, such as the BMI270 SPI instance, remain explicitly unresolved.
