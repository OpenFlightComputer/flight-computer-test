# Board tester

This directory contains the computer-side OpenFlightComputer manufacturing and acceptance-test software.

The package will eventually own configuration loading, tooling checks, firmware flashing, USB protocol communication, operator interaction, test orchestration, and result persistence. Milestone 3 loads and validates board/test configuration semantics and prints the enabled test order; it does not access hardware.

Python versions, dependencies, and the development environment are managed by uv. The committed `.python-version` requests Python 3.12, `pyproject.toml` declares package metadata and compatibility, and `uv.lock` records the resolved environment. These files are complementary parts of one uv workflow rather than separate version managers.

From the repository root, synchronize the uv-managed environment and run the console entry point:

```bash
uv sync --project board_tester
uv run --project board_tester fc-test run --config configs/test/test-config-v001.json
```

The repository also provides a bootstrap that delegates to the same uv project:

```bash
./fc-test run --config configs/test/test-config-v001.json
```

Device UID, MCU identity, board identity, firmware metadata, and capabilities are session-initialization data returned by `START_TEST`. They are validated and recorded before component dispatch and are deliberately not modeled as an `identity` component test.
