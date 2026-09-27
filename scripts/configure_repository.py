"""Set real repository metadata before publishing; never publish anything itself."""

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Actual owner/repository")
    parser.add_argument("codeowner", help="Actual GitHub user, without @")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("Expected owner/repository")
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.codeowner):
        parser.error("Invalid GitHub username")
    path = Path(__file__).resolve().parents[1] / "custom_components/haassohn/manifest.json"
    data = json.loads(path.read_text())
    data.update(
        documentation=f"https://github.com/{args.repository}",
        issue_tracker=f"https://github.com/{args.repository}/issues",
        codeowners=[f"@{args.codeowner}"],
    )
    ordered = {key: data[key] for key in ("domain", "name")}
    ordered.update({key: data[key] for key in sorted(data) if key not in ordered})
    path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
