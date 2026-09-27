"""Allowlist export; credentials and arbitrary strings never pass through."""

import re
from dataclasses import asdict
from typing import Any

from .capabilities import FIELDS
from .client import HaasSohnClient

_SAFE_KEY = re.compile(r"[a-z][a-z0-9_.]{0,63}\Z")
_SENSITIVE = re.compile(
    r"pin|nonce|token|secret|auth|pass|serial|\bsn\b|host|ip|mac|ssid|address", re.I
)

# Exact public model labels only; arbitrary metadata strings are not safe exports.
_PUBLIC_MODELS = frozenset(
    {
        "HSP 2.17 PREMIUM",
        "HSP 2.17 PREMIUM III",
        "HSP 6 PALLAZZA III",
        "HSP 6 PALLAZZA III 519.08",
        "HSP 6 PALLAZZA III 534.08",
        "HSP 6 HELENA RLU",
        "HSP 6 PELLETTO IV Grande 434.08",
        "HSP 6 PELLETTO IV 419.08",
        "HSP 6 WT RLU",
        "HSP 7 DIANA Plus RLU",
        "HSP 7 DIANA",
        "HSP 8 CATANIA II 444.08-ST",
        "Hark Ecomat 6",
    }
)


def _version(value: str | None) -> str | None:
    if value is None:
        return None
    return value if re.fullmatch(r"V[0-9.]+(?:-oKV)?", value) else "[redacted]"


def export_diagnostics(client: HaasSohnClient) -> dict[str, Any]:
    """Return manually shareable data; never include config entry data or raw metadata."""
    state = client.state
    stats = asdict(client.stats)
    if stats["last_success"] is not None:
        stats["last_success"] = stats["last_success"].isoformat()
    if state is None:
        return {"communication": stats}
    # Device supplied strings could contain arbitrary private information. Export
    # only recognized family/controller/firmware, not model text or device serial.
    info = state.info
    device = {
        "manufacturer": info.manufacturer,
        "model": info.model if info.model in _PUBLIC_MODELS else "[unrecognized model]",
        "family": info.family,
        "controller": info.controller,
        "protocol": info.protocol,
        "firmware": _version(info.firmware),
        "wifi_version": _version(info.wifi_version),
        "boot_version": _version(info.boot_version),
        "wifi_boot_version": _version(info.wifi_boot_version),
    }
    values = {
        key: value
        for key, value in state.values.items()
        if type(value) in (float, int, bool) or value is None
    }
    if "error" in state.values:
        values["error"] = state.values["error"]
    if state.values.get("mode") in {"off", "start", "heating"}:
        values["mode"] = state.values["mode"]
    unknown = {}
    for key, value in state.unknown.items():
        if not _SAFE_KEY.fullmatch(key) or _SENSITIVE.search(key):
            continue
        # Raw unknown strings/objects/numbers can be identifiers or credentials.
        # Booleans alone are safe enough to retain; numeric values are withheld.
        unknown[key] = {
            "candidate_type": type(value).__name__,
            "raw": value if type(value) is bool else "[redacted]",
        }
    return {
        "device": device,
        "state": values,
        "capabilities": {key: state.capabilities.confidence(key).value for key in FIELDS},
        "unknown": unknown,
        "communication": stats,
        "authentication_verified": client.authentication_verified,
        "received_at": state.received_at.isoformat(),
    }
