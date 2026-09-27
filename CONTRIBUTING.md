# Contributing

Please discuss new protocol operations in an issue before implementing them.
Read [development](docs/development.md), [protocol](docs/protocol.md),
[research](docs/research.md) and [safety](docs/safety.md).

Use a branch and pull request. Keep changes focused, include regression tests for
behavior changes and run the checks documented in the development guide. Changes
to `src/pyhaassohn` require `python scripts/sync_vendor.py`; never edit the bundled
copy independently. CI checks both copies and enforces 95% coverage.

State whether evidence comes from source research, an emulator or physical
hardware. Unknown firmware must remain read-only until reviewed evidence supports
writes. Do not add speculative controls or automatically retry commands.

Share only sanitized diagnostics. Never attach PINs, host addresses, serial
numbers, authentication material or raw request/response captures. For security
reports, see [SECURITY.md](SECURITY.md).

Contributions are licensed under the project's MIT license.
