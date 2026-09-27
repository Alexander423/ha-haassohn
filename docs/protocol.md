# Legacy WLAN protocol

Evidence IDs refer to [research.md](research.md). This is a reverse-engineered
contract, not a manufacturer protocol specification. No numeric register scan,
enumeration, UDP broadcast or cloud endpoint is used.

## Transport and authentication

HTTP port 80, UTF-8 JSON, fixed resource `/status.cgi`. Status is one complete
snapshot including metadata, measurements and counters. Reads have no PIN
header. A write POST contains exactly one reviewed field. The header is:

```text
X-HS-PIN = lowercase_hex(MD5(nonce + lowercase_hex(MD5(PIN))))
```

PIN remains a four-character ASCII string (leading zeroes matter). Nonce is
`meta.nonce` from an immediately preceding GET. IO/OH/BR/HY confirm this formula.
MD5 is a legacy protocol requirement, not encryption. Requests use no redirects,
environment proxies, cookies, backend URL or cloud connection. HY demonstrates
operation without the other sources' app/backend headers. Real hardware still
needs to verify this minimal header set across WLAN module revisions.

Only HTTP 200 is accepted. 401/403 maps to authentication rejection; other statuses
are protocol errors. Public sources do not establish a universal wrong-PIN status
across firmware. A 200 with unchanged/mismatched state is not called successful
authentication. There is no documented safe login endpoint. Setup verifies
reachability, decoding and identity, not the PIN. This deliberate deviation from
the original request avoids changing a combustion appliance during setup.

Each transaction is serialized: GET → validate current capabilities → POST → GET
readback. No POST is retried automatically, including after timeout, cancellation,
stale nonce, malformed acknowledgement or reset. A mismatch raises
`CommandNotConfirmed`; the caller must inspect state before another command.
HTTP request total timeout defaults to 10 seconds; decoded body limit is 64 KiB.
No device timestamp is trusted as a response sequence number. A fresh request and
fresh challenge reduce stale-state risk, but no protocol transaction ID exists.

## Field registry

All identifiers are JSON keys, not numeric registers. `src/pyhaassohn/capabilities.py`
is the executable registry. Optional missing/invalid fields become unavailable;
they never silently become zero/false. Numeric strings from Java-era representations
are accepted only for numbers; booleans must be JSON booleans. Writes accept native
booleans or finite numeric values only, never strings/coercion.

| Key | Type | Normalization | Access/evidence | Meaning / limits |
| --- | --- | --- | --- | --- |
| `prg` | boolean | identity | read/write IO/OH/BR/HY | Heating enabled, not physical flame state |
| `sp_temp` | number | °C | read/write IO/OH/BR/TEMP | 10–30, whole degrees; no write while `wprg=true` |
| `is_temp` | number | °C | read IO/OH/BR | Current room temperature |
| `eco_mode` | boolean | identity | read/write OH/HY | Write requires `meta.eco_editable=true` |
| `wprg` | boolean | identity | read/write BR/HY | Activate already stored schedule |
| `mode` | string | preserve | read IO/OH/BR | Confirmed codes: off, start, heating; preserve others without invented meaning |
| `ignitions` | number | count | read IO/OH/BR | Cumulative ignitions |
| `on_time` | number | hours | read IO/OH/BR | Cumulative operating hours |
| `consumption` | number | kg | read IO/OH/BR | Cumulative pellet consumption |
| `maintenance_in` | number | kg | read OH/BR/MAN | Pellets until service; NOT time |
| `cleaning_in` | number | minutes / 60 → hours | read IO/OH/BR | Remaining cleaning interval |
| `room_mode` | boolean | identity | read IO | Mode indicator; no confirmed setter |
| `tvl_temp` | number | °C | model-specific IO | Water jacket target; meaning not independently confirmed |
| `ht_char` | number | raw | read IO/OH/BR | Heating curve; no confirmed network setter |
| `zone` | number | raw | read IO | Operating zone; no exhaustive enum |
| `weekprogram` | array | immutable slots | read IO/OH/BR | `day`, `begin`, `end`, `temp`; no assumed timezone/day encoding |
| `error` | array | tuple of numeric `nr` | read IO/OH/BR | Reported error entries, timestamps omitted from export |
| `pgi` | boolean | raw | observed read-only IO | Unknown semantics; diagnostics only |

Metadata keys confirmed in IO/OH/BR: `hw_version` (controller), `sw_version`
(controller firmware), `bootl_version`, `wifi_sw_version`, `wifi_bootl_version`,
`sn` (serial), `typ` (model/type), `language`, `nonce`, `eco_editable`, `ts`, `ean`,
`rau`, `wlan_features`. IO additionally observes `itemid`, `backend_interval`,
`backend_max_diff`. Unknown semantics remain unknown; none are writable.
APP V1.2.5 may describe the WLAN application, not controller V5/V6/V7 firmware.
No independent `APP version`, hardware revision or numeric protocol version is
invented. `legacy-status-json` is this library's descriptive protocol name.

## Confidence and unsupported operations

`CONFIRMED_READ`, `CONFIRMED_WRITE`, `MODEL_SPECIFIC`, `OBSERVED_READ_ONLY`,
`UNKNOWN`, `UNSUPPORTED` distinguish evidence. Presence alone grants no write.
Write gates require KS01, exact IO firmware allowlist, a valid current field,
and applicable flags. These are upstream implementation reports, not our physical
verification. See [compatibility](compatibility.md).

No confirmed legacy HTTP fields were found for measured flue/combustion/return
temperatures, Wi-Fi RSSI, adjustable fan level, manual filling, cleaning/service
reset, heat-curve writes or schedule editing. Manufacturer local menu functions
do not establish network encodings. No number/select/button platform is included
without a supported operation. `seen_error` remains a research lead, not a control.

## Identity and privacy

Use `KS01:<serial>` when a nonempty, non-placeholder serial is returned. No serial:
persist a random config-entry UUID; address is only a duplicate-setup heuristic.
This survives reconfiguration but cannot detect that two aliases point at the
same anonymous stove or verify a replacement at that address. Once a serial is
known, a changed/missing serial prevents further commands. Network identity cannot
be cryptographically proven by this unauthenticated legacy GET.
