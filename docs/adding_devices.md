# Adding a device or firmware

1. Identify the WLAN generation and controller. An APP version alone is not the
   controller firmware. Fumis, serial UART and KS01 WLAN evidence are different.
2. Start with read-only diagnostics. Never probe arbitrary paths/registers or
   commands. Record source revision, exact model/controller/firmware, optional
   fields and whether the result is synthetic, observed or physically tested.
3. Compare field types and units with independent implementations and the correct
   manufacturer's manual. Preserve ambiguity instead of assigning a convenient
   name. Add evidence to `docs/research.md` and the compatibility matrix.
4. For new writable behavior, establish the payload, allowed range/enum, firmware
   scope, device flags and normal-user semantics. Source-code presence alone is
   insufficient for actuator/reset controls. Add a capability rule, not a raw-write
   escape hatch. Review safety before adding firmware to the allowlist.
5. Add synthetic fixtures clearly labelled as such, plus tests for denied values,
   unsupported firmware, state restrictions, failed acknowledgement, redaction and
   cancellation. Actual sanitized captures must identify provenance without secrets.
6. Add translated entity descriptions only when the feature has a clear HA meaning.
   Run tests/lint/type checks, regenerate the bundled library, and keep release
   hardware-test claims separate from emulator results.

If a serial is missing, the persisted local UUID is stable only for that config
entry. Do not replace it with a host or PIN hash. Reconfiguration retains existing
entity IDs, even when a serial becomes available later.
