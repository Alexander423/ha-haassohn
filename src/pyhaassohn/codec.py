"""Strict bounded JSON decoding, with tolerant omission of invalid optional fields."""

import json
import re
from datetime import UTC, datetime
from math import isfinite
from types import MappingProxyType
from typing import Any

from .capabilities import FIELDS, Field, detect
from .exceptions import ProtocolError, UnsupportedDevice
from .models import DeviceInfo, StoveState

MAX_RESPONSE_BYTES = 65536


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ProtocolError("Duplicate JSON field")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ProtocolError("Non-finite JSON number")


def _text(value: object) -> str | None:
    if isinstance(value, str) and 0 < len(value.strip()) <= 128:
        return value.strip()
    return None


def _decode_field(definition: Field, raw: Any) -> Any:
    if definition.kind == "bool":
        return raw if type(raw) is bool else None
    if definition.kind == "number":
        if isinstance(raw, bool) or not isinstance(raw, (float, int, str)):
            return None
        try:
            number = float(raw)
        except (ValueError, OverflowError):
            return None
        if not isfinite(number) or abs(number) > 1e12:
            return None
        if definition.total and number < 0:
            return None
        return number * definition.scale
    if definition.kind == "text":
        return _text(raw)
    if not isinstance(raw, list) or len(raw) > 128:
        return None
    if definition.kind == "errors":
        codes: list[int] = []
        for item in raw:
            if not isinstance(item, dict):
                return None
            code = item.get("nr")
            if isinstance(code, str) and re.fullmatch(r"[0-9]{1,5}", code):
                code = int(code)
            if type(code) is not int or not 0 <= code <= 65535:
                return None
            codes.append(code)
        return tuple(codes)
    slots: list[MappingProxyType[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        # Preserve published schedule shape, without interpreting undocumented day codes.
        allowed = {
            key: value
            for key, value in item.items()
            if key in {"day", "begin", "end", "temp"}
            and type(value) in (str, int, float)
            and len(str(value)) <= 32
        }
        if len(allowed) != 4:
            return None
        slots.append(MappingProxyType(allowed))
    return tuple(slots)


def decode(body: bytes, *, record_unknown: bool = False) -> StoveState:
    """Decode a status response. No raw response or nonce appears in exceptions."""
    if len(body) > MAX_RESPONSE_BYTES:
        raise ProtocolError("Response exceeds size limit")
    try:
        raw = json.loads(body.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ProtocolError("Invalid JSON response") from None
    if not isinstance(raw, dict) or not isinstance(raw.get("meta"), dict):
        raise ProtocolError("Status metadata missing")
    meta = raw["meta"]
    controller, firmware, model = (
        _text(meta.get(key)) for key in ("hw_version", "sw_version", "typ")
    )
    if controller != "KS01" or firmware is None or model is None:
        raise UnsupportedDevice("Unrecognized legacy controller metadata")
    values = {
        key: _decode_field(definition, raw[key]) for key, definition in FIELDS.items() if key in raw
    }
    if not any(values.get(key) is not None for key in ("prg", "is_temp", "mode")):
        raise ProtocolError("Status has no recognizable operating fields")
    serial = _text(meta.get("sn"))
    if serial is not None and (
        serial.lower() in {"unknown", "none", "n/a"} or set(serial) <= {"0", "-", " "}
    ):
        serial = None
    match = re.search(r"\bHSP[\s-]*([0-9]+)\b", model, re.IGNORECASE)
    manufacturer = "Hark" if "ecomat" in model.lower() else "HAAS+SOHN"
    info = DeviceInfo(
        manufacturer,
        model,
        f"HSP {match[1]}" if match else None,
        firmware,
        controller,
        serial,
        _text(meta.get("wifi_sw_version")),
        _text(meta.get("bootl_version")),
        _text(meta.get("wifi_bootl_version")),
    )
    # Unknown data is held only on explicit opt-in and filtered again on export.
    known_meta = {
        "hw_version",
        "sw_version",
        "typ",
        "sn",
        "wifi_sw_version",
        "bootl_version",
        "wifi_bootl_version",
        "nonce",
        "eco_editable",
    }
    unknown = {key: value for key, value in raw.items() if key not in FIELDS and key != "meta"}
    unknown.update({f"meta.{key}": value for key, value in meta.items() if key not in known_meta})
    return StoveState(
        info,
        MappingProxyType(values),
        detect(meta, values),
        datetime.now(UTC),
        MappingProxyType(unknown if record_unknown else {}),
        _text(meta.get("nonce")),
    )
