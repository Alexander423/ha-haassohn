# Safety contract

This integration sends normal user controls to the stove's existing safety
controller. It is not a combustion controller. No actuator, fan drive, ignition
heater, auger, relay, calibration or combustion parameter is writable.

Only four reviewed commands exist: heating enablement, target temperature, eco
mode, stored weekly-program activation. Exact controller firmware and current
capabilities gate them. The temperature range is 10–30 °C in integer steps; invalid
values are rejected, never clamped. Unknown firmware receives no writes.

Setup/reconfiguration never sends a control command. There is no brute-force
discovery, register enumeration, undocumented empty POST, reset or filling action.
Network requests target only the configured host and fixed status resource.

Writes are serialized with reads, use a fresh nonce, and require readback. A lost
response may mean a command executed. Such a write is not repeated automatically.
Power-off requests the stove's normal shutdown; it does not cut power or force
fans off. Fault acknowledgement remains at the appliance because source code for
an acknowledgement is insufficient evidence that every safety precondition holds.

The user's manual and stove controller remain authoritative. Physical validation
must cover normal shutdown, startup, weekly program interactions, editable flags,
wrong-PIN behavior and recovery on representative hardware before a stable release
is advertised. No real appliance was operated during development.
