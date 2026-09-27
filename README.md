# HAAS+SOHN Local

[![Checks](https://github.com/Alexander423/ha-haassohn/actions/workflows/ci.yml/badge.svg)](https://github.com/Alexander423/ha-haassohn/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Deutsche Installationsanleitung](docs/installation.de.md) · [Releases](https://github.com/Alexander423/ha-haassohn/releases)

An asynchronous Python library (`pyhaassohn`) and a Home Assistant custom integration
(`haassohn`) for older **KS01 / status.cgi** pellet-stove WLAN modules. Communication
is direct over the local network. No MQTT, Node.js, bridge, Supervisor, add-on or
cloud account is required; Home Assistant Container is supported.

**Development release.** Protocol evidence comes from independently reviewed
implementations and manuals. Tests use synthetic emulators; this project has not
yet been validated on physical hardware. It is not an official HAAS+SOHN or Home
Assistant Core integration. See [compatibility](docs/compatibility.md) for precise
model/firmware reports and [research](docs/research.md) for source revisions.

## Functions

* Climate: heating on/off, room temperature and target (10–30 °C, 1 °C steps).
* Eco mode when the controller declares it editable; stored weekly program activation.
* Operating state, ignition count, operating hours, pellet consumption, cleaning
  interval, maintenance remaining and optional diagnostic fields.
* One device per stove, UI setup, IP/PIN reconfiguration, auth rejection handling,
  English/German UI, automatic recovery/backoff and sanitized diagnostics.
* Unknown KS01 firmware stays read-only. Unsupported generations are rejected.

The compatibility evidence includes HSP2 Premium, HSP6 Pallazza/Helena/Pelletto,
HSP7 Diana, HSP8 Catania and Hark Ecomat 6. A WLAN **APP V1.2.5** display is not enough
to determine the controller's V5/V6/V7 firmware or guarantee compatibility.
Newer Fumis WiRCU modules use a different protocol.

## Install locally

Use Home Assistant 2026.9 or newer. Copy the complete
`custom_components/haassohn` directory, including `_vendor`, into your HA
configuration directory's `custom_components` folder and restart HA. The bundled
library is generated from the independent package; no PyPI publication is needed.
For an archive, run `python scripts/package_integration.py` and extract
`dist/haassohn-0.1.0.zip` into the configuration directory.

Go to **Settings → Devices & services → Add integration → HAAS+SOHN**. Enter the
local host/IP without URL scheme or port and the four-digit APP PIN shown by the
stove. A leading zero is significant. No YAML is required. Setup performs only a
read; the protocol provides no proven, non-mutating way to validate the PIN. A wrong
PIN is reported on a rejected control command, not inferred from a successful read.

Use **Reconfigure** to change IP or PIN without recreating devices/entities. A
returned serial must match the existing stove. If the protocol supplies no usable
serial, a random persistent identity is used; duplicate detection across host
aliases is then limited. Reserve a DHCP address if appropriate for your network.

## HACS

1. Open **HACS → menu → Custom repositories**.
2. Add `https://github.com/Alexander423/ha-haassohn` with type **Integration**.
3. Find **HAAS+SOHN Local**, download it and restart Home Assistant.
4. Open **Settings → Devices & services → Add integration → HAAS+SOHN**.
5. Enter the stove's local IP address and four-digit APP PIN.

Requires Home Assistant **2026.9 or newer**. This is a development release for
initial hardware testing; see [validation](docs/validation.md). If selecting a
prerelease in HACS, enable **Show beta versions** in the download dialog. You can
also select the default branch. This repository is not in HACS's default store.

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Alexander423&repository=ha-haassohn&category=integration)

## Standalone library

Install from the local source checkout with `python -m pip install .` or install
the built wheel. Get connection information from your application's secret storage:

```python
from pyhaassohn import HaasSohnClient


async def inspect_stove(host: str, pin: str):
    async with HaasSohnClient(host, pin) as stove:
        state = await stove.get_state()
        return state.info, state.values, stove.capabilities
```

No raw-write API is offered. Use `set_power`, `set_target_temperature`, `set_eco_mode`
or `set_week_program`; every call validates current capabilities, types and values.

## Troubleshooting and limits

An unavailable device is retried automatically, initially after 30 seconds and up
to 5 minutes after repeated failures. Check network reachability and the configured
host. Authentication rejection opens reauthentication. A failed command may already
have executed: inspect the stove state before repeating it.

No climate controls on unknown firmware is intentional. Target changes are disabled
while weekly programming is active. Firmware updates that add optional fields need
an integration reload to create new entities. Diagnostics explain detected capabilities.
Error entries may be history, so their presence is not labelled an active fault.
Only confirmed `heating`/`off` states are mapped to HVAC actions; ignition/cooling
remain visible in the stove-state sensor.

Schedule editing, fan/actuator adjustment, manual filling and error/maintenance
resets are not exposed without a validated safe network contract. No exhaust or
water measurements are invented from serial-only telemetry. Optional `tvl_temp`
means the reported water-jacket **target**, and is disabled by default.

## Privacy, safety and contributing

The integration makes no external requests during normal operation and sends no
telemetry. Status uses legacy unencrypted HTTP; only the configured stove receives
the PIN-derived command signature. Diagnostics omit PIN, nonce, serial and host.
No real network address/PIN belongs in code, fixtures, issues or logs.

Read [safety](docs/safety.md), [protocol](docs/protocol.md),
[architecture](docs/architecture.md), [development](docs/development.md),
[adding devices](docs/adding_devices.md) and [diagnostics](docs/diagnostics.md).
Contributions should provide evidence and tests, not speculative writable fields.
Original implementation: MIT; upstream research attribution: [NOTICE](NOTICE).
Executed checks and outstanding release work: [validation record](docs/validation.md).

