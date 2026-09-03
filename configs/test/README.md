# Test configurations

Test configurations define an immutable named and UUID-identified test procedure: its referenced board configuration, ordered enabled tests, parameters, and acceptance limits.

`test-config-v006.json` is the current Flight Computer V1 acceptance procedure. It contains only the four tests that passed on assembled revision-0.1 hardware: RGB LED, IMU, barometer, and microSD. The red and green status LEDs are absent because their board polarity is confirmed broken. Version 005 remains the exact procedure used by the recorded successful bring-up run, where those entries were disabled. Versions 001 through 005 remain unchanged as historical procedures and are superseded by version 006.

The board path is resolved relative to the test configuration file and array order is execution order. Test implementations for corrected future hardware may remain in the tester even when they are absent from the current V1 procedure.

Identity and MCU-runtime readiness are mandatory session initialization and do not appear as ordered component tests. Once a configuration has been used for a meaningful run, create a new version and UUID instead of silently changing it.
