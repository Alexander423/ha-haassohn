"""Distribution and translation invariants that catch broken user installations."""

import json
from pathlib import Path

from pyhaassohn.capabilities import FIELDS
from pyhaassohn.errors import ERROR_KEYS, describe_error

ROOT = Path(__file__).resolve().parents[1]


def leaves(value, prefix=""):
    if isinstance(value, dict):
        return {leaf for key, child in value.items() for leaf in leaves(child, f"{prefix}.{key}")}
    return {prefix}


def test_translation_parity():
    folder = ROOT / "custom_components/haassohn"
    source = json.loads((folder / "strings.json").read_text(encoding="utf-8"))
    for language in ("en", "de"):
        translated = json.loads(
            (folder / f"translations/{language}.json").read_text(encoding="utf-8")
        )
        assert leaves(source) == leaves(translated)
        assert set(translated["entity"]["sensor"]["reported_error"]["state"]) == (
            set(ERROR_KEYS.values()) | {"unknown_code", "no_entries"}
        )
    for key, definition in FIELDS.items():
        if definition.kind in {"number", "text"}:
            assert key in source["entity"]["sensor"]


def test_exact_bundle():
    source = ROOT / "src/pyhaassohn"
    bundled = ROOT / "custom_components/haassohn/_vendor/pyhaassohn"
    for path in source.iterdir():
        if path.is_file():
            assert (bundled / path.name).read_bytes() == path.read_bytes()


def test_error_keys():
    assert describe_error(18) == "power_interruption"
    assert describe_error(999) == "unknown_code"
    assert describe_error(42) == "maintenance_reset"
