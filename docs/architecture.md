# Architecture

The independent `src/pyhaassohn` package has no Home Assistant imports. It contains
authentication, bounded HTTP transport, strict codec, immutable snapshots, the
capability registry, client transactions and sanitized diagnostics. A dataclass
profile is unnecessary for every marketing model: all confirmed implementations
use one KS01 JSON dialect with optional fields. Capabilities and an exact firmware
allowlist express the differences without `if model == ...` command branches.

The integration is an adapter around this public API. One typed
`ConfigEntry[HaasSohnCoordinator]` stores runtime data. The coordinator polls all
state once every 30 seconds. Failures make entities unavailable and increase the
interval through 60/120/240/300 seconds, resetting on success. A command publishes
its readback snapshot. No entity polls independently. Since one endpoint returns
everything, separate slow statistics polling would save no requests.

One device contains climate, scalar sensors, meaningful booleans and confirmed
eco/weekly switches. Entity IDs use the persistent entry identity. Current and
target temperatures belong to climate when it exists; read-only firmware gets
temperature sensors instead. Service interval sensors and due flags serve distinct
numeric-history and binary-automation uses. Optional technical fields default to
disabled. Absent fields never display cached defaults as valid measurements.

Entity creation uses capabilities from setup. Runtime write restrictions are
rechecked both by entities and the library, and missing fields become unavailable.
If a firmware upgrade adds new capabilities, reload the integration to discover
new entities. No unknown JSON field is automatically exposed as an entity.

`prg` is heating enablement, not observed combustion. Only `mode=heating` maps to
HEATING; `off` maps to OFF/IDLE according to enablement. Ignition, cooling and unknown
strings have no guessed HVAC action. The raw state sensor remains available.

## Distribution and Core path

The wheel is independently installable. HACS cannot install an unpublished PyPI
dependency, so `scripts/sync_vendor.py` generates an exact private copy under
`custom_components/haassohn/_vendor/pyhaassohn`. `library.py` is the only adapter
import boundary. CI compares every bundled byte to the library source.

For Core submission: publish the independent package under an owned PyPI name,
replace this boundary with normal imports, add its exact requirement to the
manifest, remove `_vendor`, nominate actual code owners, add the brand asset and
HA documentation, and run Core hassfest/quality-scale review. Current tests do not
equal Core acceptance or a manufacturer safety certification. Publishing names,
GitHub ownership and credentials are not assumed.
