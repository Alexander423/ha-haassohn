"""Generate/check the exact HACS copy of the independent library."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "pyhaassohn"
TARGET = ROOT / "custom_components" / "haassohn" / "_vendor" / "pyhaassohn"


def sync(check: bool = False) -> None:
    expected = {path.name: path.read_bytes() for path in SOURCE.iterdir() if path.is_file()}
    actual = {path.name: path.read_bytes() for path in TARGET.glob("*") if path.is_file()}
    if check:
        if actual != expected:
            raise SystemExit("Bundled library differs; run python scripts/sync_vendor.py")
        return
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, content in expected.items():
        (TARGET / name).write_bytes(content)
    for name in actual.keys() - expected.keys():
        (TARGET / name).unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    sync(parser.parse_args().check)
