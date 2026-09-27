"""Build a deterministic custom_components installation archive, without secrets."""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from sync_vendor import sync

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    sync(check=True)
    component = ROOT / "custom_components" / "haassohn"
    version = json.loads((component / "manifest.json").read_text())["version"]
    target = ROOT / "dist" / f"haassohn-{version}.zip"
    target.parent.mkdir(exist_ok=True)
    paths = [
        p
        for p in component.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".json", ".typed"}
    ]
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        content = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in paths}
        content.update(
            {
                f"custom_components/haassohn/{name}": (ROOT / name).read_bytes()
                for name in ("LICENSE", "NOTICE")
            }
        )
        for name, body in sorted(content.items()):
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, body)
    print(target)


if __name__ == "__main__":
    main()
