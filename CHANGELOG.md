# Changelog

## 0.1.1 — Read-state fixes

- Fix the stove-state text sensor being rejected by Home Assistant as numeric.
- Recognize hyphenated HSP family names such as HSP-6, enabling the reported-error
  description sensor without changing existing device or entity identities.
- Include the public HSP-6 model label in sanitized diagnostics.
- Add regressions for text-state updates and model spelling variants.
- Document initial read-only hardware observations; physical commands remain untested.

## 0.1.0 — Initial development release

- Local asynchronous KS01/status.cgi client with explicit firmware capabilities.
- Home Assistant UI setup, reconfiguration, reauthentication and sanitized diagnostics.
- Climate, sensors, binary sensors and supported eco/weekly-program switches.
- German and English translations; bundled client with no separate installation.
- Signed, serialized commands with fresh status and readback, without write retries.
- Emulator-based library and Home Assistant tests; hardware validation pending.

This release is intended for supervised initial testing. See
[compatibility](docs/compatibility.md) and [validation](docs/validation.md).
