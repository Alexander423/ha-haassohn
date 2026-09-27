# Diagnostics and privacy

Download diagnostics in Home Assistant under the integration's device menu. Export
contains known numeric/boolean state, recognized firmware/family, capability
confidence, counters and last successful update. No telemetry or automatic upload
exists. A user may manually attach the JSON to an issue after reviewing it.

The export uses an allowlist rather than copying a config entry and guessing which
keys to redact. Host, PIN, hashes, nonce, serial, arbitrary model strings, network
identifiers, schedule times and error timestamps are excluded. Known mode strings
may be included. Unknown firmware strings are redacted. The manufacturer/family
is inferred only from known naming conventions, not copied as arbitrary text.
Exact public model names from the compatibility matrix and version-shaped
controller/WLAN/bootloader values are included; unrecognized model text is withheld.

The library's `record_unknown=True` option records additional fields in the latest
in-memory snapshot. The integration enables this for diagnostic discovery. It makes
no additional requests and stores no raw payload on disk. Export retains safe
field identifiers and candidate Python types; unknown strings, numbers and objects
are redacted because they could contain credentials/identifiers. Unknown booleans
can be exported. Sensitive-looking keys are omitted. The fixed response-size bound
also bounds this in-memory capture. Raw capture is not automatically safe to share.

Known schedules remain available through the library snapshot but are not an
editable HA calendar. Do not attach unrestricted network captures or raw responses
without removing `meta.sn`, `meta.nonce`, PIN-related headers and network metadata.

The legacy protocol itself is unencrypted HTTP. The actual PIN is not sent; its
challenge signature is sent only to the configured stove. PIN-derived signatures
are still sensitive. No tokens or raw response bodies are logged by this project.
