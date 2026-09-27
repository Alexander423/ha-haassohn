# Research record

Reviewed 2026-09-27. Protocol facts were extracted from executable source, not
inferred from marketing names. No appliance was contacted. The supplied task
document ends at the heading `28`; no additional requirements were present.

## Reproducible source references

| ID | Source and revision | Files inspected / relevance |
| --- | --- | --- |
| IO | [ioBroker](https://github.com/marvingrieger/ioBroker.haassohn/tree/d98bf97e56c77bd50ef35a0058113a96d61c105f) | Complete `main.js`, device objects and firmware allowlist in `io-package.json`; README model reports. MIT. |
| OH | [openHAB binding](https://github.com/openhab/openhab-addons/tree/7a4884321cf0e26802a093848cdc50f009bdd061/bundles/org.openhab.binding.haassohnpelletstove) | All seven Java files, channel XML, configuration, README; GET/POST, eco, units and 30-second refresh. EPL-2.0. |
| BR | [hsp-mqtt-bridge](https://github.com/dwyschka/hsp-mqtt-bridge/tree/27fe145376996a72e36a3f9f577987d3c2b8f588) | All four Go sources: `stove.go`, `structs.go`, `main.go`, `mqtt.go`; serial, schedules, weekly activation, attempted error acknowledgement. No source copied. |
| HY | [Homey](https://github.com/shaarkys/com.haassohn.pellets/tree/563e1fd7166447dbfb33fbc20dffa3d070a3f02e) | Complete HTTP library, driver, device and app TypeScript; eco-editable flag, weekly-program temperature restriction, response cleanup. |
| TG | [Telegraf](https://github.com/darnt/telegraf-haassohn/tree/3f17b530f7ffdda2c1b7a46cf6c567757345715a) | Full config: serial telemetry at 19200 baud. Its additional temperature/actuator fields are NOT evidence for WLAN JSON fields. |
| UART | [Serial MQTT implementation](https://github.com/vandenberghev/haaspelletstove2mqtt/tree/8f10d0e102ca941d8dbc099d405fa3045c3ff038) | Both complete Python files inspected. Same serial distinction; no WLAN HTTP encodings for its extra measurements. |
| MAN | [Manufacturer general pellet manual](https://www.haassohn.com/files/product-assets/asset-0553908000000-4.pdf) | Printed pages 15–16 and 20–22: maintenance in kg, local user functions, fault table. |
| TEMP | [Manufacturer pellet manual](https://www.haassohn.com/files/product-assets/asset-0553208000000-2.pdf) | Section 7.3: 10–30 °C, one-degree user setpoint increments; independently matches BR climate limits. |
| WLAN | [Archived manufacturer WLAN manual, 2015-05-26](https://www.libble.de/haas-sohn-wlan-modul---hsp/p/1048714/) | Names HSP1 II, HSP2 Premium II, HSP6 Pallazza III, HSP8 Lucca II. This is product evidence, not an API interoperability test. |
| FUMIS | [HA Fumis documentation](https://www.home-assistant.io/integrations/fumis/) | WiRCU uses MAC/PIN identification and a different integration. The HAAS+SOHN brand alone does not establish legacy compatibility. |

The GitHub repository search for `haassohn` also found
`kt5f5zdvkv-lab/homeassistant-haassohn`, which was empty at inspection. Broader
searches included Haas Sohn, HSP pellet/WLAN/WiFi/protocol/API, HSP2/6/7/8, APP PIN,
pellet stove protocol and haassohnpelletstove. Broad HSP queries contain many
unrelated projects; they are not evidence. Research checkouts stay in ignored
`.research/`, not the distributable integration.

## Cross-checks and decisions

* IO/OH/BR/HY agree on HTTP `GET /status.cgi`, JSON names and the nested MD5
  signature. Every GET implementation is unauthenticated. None demonstrates a
  safe authentication-only request. We do not invent `POST {}` or rewrite the
  current temperature as a login probe. PIN verification at initial setup is an
  explicitly unmet protocol requirement, explained in the UI.
* Power and setpoint writes have three implementations. Eco is implemented in
  OH and HY, with the editable flag conservatively enforced. Weekly activation
  is in BR and HY. Schedule editing has no adequately validated encoder here.
* IO calls `maintenance_in` minutes; OH, BR and the manufacturer support kg.
  `cleaning_in` is minutes on the wire; normalize to hours. HY displays a derived
  percentage, which is not a raw sensor and is not adopted.
* `tvl_temp` is labelled **water jacket target** by IO. It must not be called
  measured flow, return, boiler or exhaust temperature. It is diagnostic,
  disabled by default, and never writable.
* HY's pellet-remaining estimate is locally calculated, not an API measurement.
  Serial telemetry in TG is not exposed through `status.cgi` by any reviewed
  implementation. No such fields are fabricated.
* BR has `seen_error` but lacks status validation and physical precondition
  enforcement. It is not a confirmed safe reset API. No reset button is shipped.
* Fault arrays may contain history/information. Their presence is not proof of
  an active fault. Preserve codes; do not invent severity or active-state flags.
* IO logs PIN hashes; OH logs authentication headers and has a suspicious header
  whose name is the digest. Those behaviors are not copied. BR lacks HTTP error
  checks, and some sources infer heating from request intent. We validate the
  response and retain physical-state uncertainty.

## Home Assistant references checked before implementation

* [Config flows, reconfigure and reauth](https://developers.home-assistant.io/docs/core/integration/config_flow/)
* [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data/)
* [Climate semantics](https://developers.home-assistant.io/docs/core/entity/climate/)
* [Typed runtime data](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/)
* [Diagnostics](https://developers.home-assistant.io/docs/core/integration/diagnostics/)
* [Quality scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)

PyPI reported HA 2026.9.4 requiring Python >=3.14.2. The standalone library also
supports Python 3.13. This project does not claim an awarded Core quality tier.
