# Validation record — 2026-09-27

This records executed checks, not future CI promises or physical compatibility.

| Check | Result |
| --- | --- |
| Independent library / transport / distribution metadata tests | 138 passed, Python 3.13.14, Windows |
| Library combined line + branch coverage | 99.60%; all 390 executable lines covered |
| Home Assistant integration tests | 32 passed, HA 2026.9.4, Python 3.14.7, Linux |
| Integration combined line + branch coverage | 98.39% |
| Real HA service → HTTP emulator → readback | Passed, including wrong-PIN command rejection and diagnostics |
| Ruff check and formatting | Passed |
| Strict mypy, standalone package | Passed, 10 modules |
| Strict mypy, integration boundary/platforms | Passed, 11 modules, Python 3.14 target |
| Bundled library byte comparison | Passed |
| Official hassfest from HA 2026.9.4 | Passed: 1 integration, 0 invalid |
| Python wheel / source distribution | Built locally |
| Custom integration ZIP | Built locally; includes private library, translations and license |

The independent suite also ran successfully on Python 3.14.7. Vendored code is
excluded from HA coverage because the exact same bytes are measured by the
independent suite; the end-to-end test exercises the bundled import path.

The upstream HA harness cannot execute natively on Windows because it imports
`fcntl`. Linux tests used an isolated Ubuntu 24.04 root filesystem inside the
existing WSL environment, with real Python 3.14.7 and the official HA harness.
No stubbed Home Assistant classes or fake POSIX modules were used. Normal tests
mock only the appliance boundary; the end-to-end test uses actual loopback HTTP.
The emulator is synthetic, not a physical reference implementation.

## Outstanding release validation

* No physical appliance has been tested. WLAN APP V1.2.5 compatibility remains
  unverified. Establish controller firmware and read response shape first.
* Repository metadata points to `Alexander423/ha-haassohn`.
* HACS action is configured in CI; repository-dependent remote validation has not
  run. No HACS listing, PyPI publication or Core submission occurred.
* The researched protocol provides no proven non-mutating initial PIN check.
  Setup makes no write solely to validate a PIN; the UI explains this limitation.
* Schedule editing, actuator/fan adjustment, cleaning/service resets, measured
  combustion/flow/return temperatures and RSSI remain documented research gaps.

CI enforces a 95% coverage floor independently for the library and HA adapter.
Physical compatibility claims must remain separate from emulator results.
