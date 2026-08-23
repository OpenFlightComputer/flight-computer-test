# Test configurations

Test configurations define an immutable named and UUID-identified test procedure: its referenced board configuration, ordered enabled tests, parameters, and acceptance limits.

`test-config-v004.json` is the current complete Flight Computer V1 acceptance procedure. Its board path is resolved relative to the test configuration file, and array order is execution order. Disabled entries remain part of the procedure but are skipped during execution. Versions 001 through 003 remain unchanged as historical procedures and are superseded by version 004.

Identity and MCU-runtime readiness are mandatory session initialization and do not appear as ordered component tests. Once a configuration has been used for a meaningful run, create a new version and UUID instead of silently changing it.
