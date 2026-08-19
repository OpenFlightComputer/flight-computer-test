# Test configurations

Test configurations define an immutable named and UUID-identified test procedure: its referenced board configuration, ordered enabled tests, parameters, and acceptance limits.

`test-config-v001.json` is the initial Flight Computer V1 acceptance procedure. Its board path is resolved relative to the test configuration file, and array order is execution order. Disabled entries remain part of the procedure but are skipped during execution.

Identity metadata is mandatory session initialization and does not appear as an ordered component test. Once a configuration has been used for a meaningful run, create a new version and UUID instead of silently changing it.
