# Compatibility evidence, not a hardware certification

All rows below use legacy JSON over HTTP. IO identifies KS01 with the firmware
allowlist; model names are user reports, not unique firmware fingerprints. Serial
and raw `meta.typ` are used for identification, not a guessed model from firmware.
All local fixtures are **synthetic**. No physical stove has been tested by this
project, including the user's WLAN APP V1.2.5 stove.

Read set R: available valid fields listed in [protocol.md](protocol.md), not a claim
that every model supplies every field. Write set W: power and integer 10–30 °C
target, plus eco only when editable and stored weekly-program activation when
present. Power/target have IO/OH/BR evidence; eco OH/HY, weekly BR/HY. Exact
firmware plus current fields governs availability; model reports do not establish
every write on every model. No unrestricted firmware ranges are allowed.

| Manufacturer | Family | Reported model | Controller | Firmware report | Reads | Writes evidence | Local test status / source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HAAS+SOHN | HSP 2 | 2.17 Premium | KS01 | V5.13, V7.01 | R | IO power/target; optional W as above | Synthetic family; IO |
| HAAS+SOHN | HSP 2 | 2.17 Premium III | KS01 | V7.02 | R | IO power/target; optional W | Synthetic profile; IO |
| HAAS+SOHN | HSP 6 | Pallazza III | KS01 | V5.07 (README says VV5.07) | R | IO power/target; optional W | Synthetic family; IO |
| HAAS+SOHN | HSP 6 | Pallazza III 519.08 | KS01 | V5.12 | R | IO power/target; optional W | Synthetic family; IO |
| HAAS+SOHN | HSP 6 | Pallazza III 534.08 | KS01 | V6.02 | R | IO power/target; optional W | Synthetic family; IO |
| HAAS+SOHN | HSP 6 | Helena RLU | KS01 | V7.07 | R | IO power/target; optional W | Synthetic family; IO |
| HAAS+SOHN | HSP 6 | Pelletto IV Grande 434.08 | KS01 | V7.08, V7.11 | R | IO power/target; OH also reports 434.08 | Synthetic family; IO/OH |
| HAAS+SOHN | HSP 6 | Pelletto IV 419.08 | KS01 | V7.08, V7.13 | R | IO power/target; optional W | Synthetic profile; IO |
| HAAS+SOHN | HSP 6 | WT RLU | KS01 reported | not specified | R if KS01 response | None until controller firmware is allowlisted | No model fixture; IO |
| HAAS+SOHN | HSP 7 | Diana Plus RLU | KS01 | V7.06 | R | IO power/target; optional W | Synthetic family; IO |
| HAAS+SOHN | HSP 7 | Diana | KS01 | V7.04-oKV (README shorthand V7.04) | R | IO power/target; OH eco | Synthetic profile; IO/OH |
| HAAS+SOHN | HSP 7 | unspecified variant | KS01 | V6.07 | R | IO power/target; optional W | Synthetic family; IO |
| HAAS+SOHN | HSP 8 | Catania II 444.08-ST | KS01 | V5.10 | R | IO power/target; optional W | Synthetic profile; IO |
| Hark | not established | Ecomat 6 | KS01 | V6.01 from IO changelog | R | IO power/target; optional W | Synthetic profile; IO |
| HAAS+SOHN | HSP 1 | HSP1 II | unknown | unknown | not protocol-confirmed | none claimed | WLAN manual only |
| HAAS+SOHN | HSP 2 | Premium II | unknown | unknown | not protocol-confirmed | none claimed | WLAN manual only |
| HAAS+SOHN | HSP 8 | Lucca II | unknown | unknown | not protocol-confirmed | none claimed | WLAN manual only |

Unknown KS01 firmware is accepted **read-only**. Non-KS01 controllers or responses
without recognizable status are rejected. Fumis WiRCU is a distinct generation;
its brand compatibility does not imply support here. The [source ledger](research.md)
contains immutable upstream revisions and the manufacturer references.
