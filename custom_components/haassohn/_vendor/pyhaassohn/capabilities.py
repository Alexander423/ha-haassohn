"""Reviewed protocol registry. Evidence IDs resolve in docs/research.md.

Confidence describes evidence, not a manufacturer guarantee. A field's presence
never grants write permission. All write grants also require a known profile.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import Any

from .exceptions import InvalidValue


class Confidence(StrEnum):
    CONFIRMED_READ = "confirmed_read"
    CONFIRMED_WRITE = "confirmed_write"
    MODEL_SPECIFIC = "model_specific"
    OBSERVED_READ_ONLY = "observed_read_only"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class Field:
    """Wire name, normalized unit/scale and independently reviewed access."""

    key: str
    kind: str
    unit: str | None = None
    scale: float = 1
    confidence: Confidence = Confidence.CONFIRMED_READ
    evidence: tuple[str, ...] = ("IO", "OH", "BR")
    write: bool = False
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    diagnostic: bool = False
    total: bool = False

    def validate_write(self, value: object) -> bool | int | float:
        """Validate without clamping, rounding, or truthiness coercion."""
        if self.kind == "bool" and type(value) is bool:
            return value
        if self.kind == "number" and type(value) in (float, int):
            assert isinstance(value, (float, int))
            if (
                isfinite(value)
                and self.minimum is not None
                and self.maximum is not None
                and self.minimum <= value <= self.maximum
                and (self.step is None or (value - self.minimum) % self.step == 0)
            ):
                return value
        raise InvalidValue("Value does not satisfy the confirmed command constraints")


FIELDS: Mapping[str, Field] = MappingProxyType(
    {
        f.key: f
        for f in (
            Field("prg", "bool", write=True),
            Field(
                "sp_temp",
                "number",
                "°C",
                write=True,
                minimum=10,
                maximum=30,
                step=1,
                evidence=("IO", "OH", "BR", "TEMP"),
            ),
            Field("is_temp", "number", "°C"),
            Field("eco_mode", "bool", write=True, evidence=("OH", "HY", "MAN")),
            Field("wprg", "bool", write=True, evidence=("BR", "HY")),
            Field("mode", "text"),
            Field("ignitions", "number", total=True),
            Field("on_time", "number", "h", total=True),
            Field("consumption", "number", "kg", total=True),
            Field("maintenance_in", "number", "kg", evidence=("OH", "BR", "MAN")),
            Field("cleaning_in", "number", "h", scale=1 / 60),
            Field("room_mode", "bool", evidence=("IO",)),
            Field(
                "tvl_temp",
                "number",
                "°C",
                confidence=Confidence.MODEL_SPECIFIC,
                evidence=("IO",),
                diagnostic=True,
            ),
            Field("ht_char", "number", diagnostic=True),
            Field("zone", "number", diagnostic=True, evidence=("IO",)),
            Field("error", "errors", diagnostic=True),
            Field("weekprogram", "schedule", diagnostic=True),
            Field(
                "pgi",
                "bool",
                confidence=Confidence.OBSERVED_READ_ONLY,
                diagnostic=True,
                evidence=("IO",),
            ),
        )
    }
)

# Exact controller releases from the ioBroker allowlist. Unknown releases remain
# readable; no guessed semver ranges or automatic promotion of new firmware.
KNOWN_FIRMWARE = frozenset(
    {
        "V5.07",
        "V5.10",
        "V5.12",
        "V5.13",
        "V6.01",
        "V6.02",
        "V6.07",
        "V7.01",
        "V7.02",
        "V7.04-oKV",
        "V7.06",
        "V7.07",
        "V7.08",
        "V7.11",
        "V7.13",
    }
)


@dataclass(frozen=True, slots=True)
class Capabilities:
    """Snapshot-derived access, recomputed before every command."""

    readable: frozenset[str]
    writable: frozenset[str]
    known_firmware: bool

    def confidence(self, key: str) -> Confidence:
        if key in self.writable:
            return Confidence.CONFIRMED_WRITE
        if key in self.readable:
            return FIELDS[key].confidence
        return Confidence.UNSUPPORTED if key in FIELDS else Confidence.UNKNOWN

    @property
    def can_set_target_temperature(self) -> bool:
        return "sp_temp" in self.writable


def detect(meta: Mapping[str, Any], values: Mapping[str, Any]) -> Capabilities:
    """Apply controller/firmware and device-provided restrictions."""
    known = meta.get("hw_version") == "KS01" and meta.get("sw_version") in KNOWN_FIRMWARE
    readable = frozenset(key for key, value in values.items() if value is not None)
    writable = {key for key in readable if FIELDS[key].write} if known else set()
    if meta.get("eco_editable") is not True:
        writable.discard("eco_mode")
    # Upstream Homey explicitly rejects target changes during the week program.
    if values.get("wprg") is True:
        writable.discard("sp_temp")
    return Capabilities(readable, frozenset(writable), known)
