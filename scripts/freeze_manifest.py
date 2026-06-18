from __future__ import annotations

import datetime as dt
import subprocess

from common import CONFIG, gh_executable, load_json, write_json


SOURCE = CONFIG / "repositories.source.json"
FROZEN = CONFIG / "repositories.frozen.json"


def gh_json(gh: str, endpoint: str):
    completed = subprocess.run(
        [gh, "api", endpoint],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    import json

    return json.loads(completed.stdout)


def main() -> None:
    source = load_json(SOURCE)
    gh = gh_executable()
    frozen = []

    for index, selected in enumerate(source["repositories"], start=1):
        metadata = gh_json(gh, f"repos/{selected['repository']}")
        canonical = metadata["full_name"]
        branch = metadata["default_branch"]
        commit = gh_json(gh, f"repos/{canonical}/commits/{branch}")
        license_info = metadata.get("license") or {}
        row = {
            **selected,
            "repository": canonical,
            "url": metadata["clone_url"],
            "defaultBranch": branch,
            "commitSha": commit["sha"],
            "commitDate": commit["commit"]["committer"]["date"],
            "archived": bool(metadata["archived"]),
            "fork": bool(metadata["fork"]),
            "sizeKiB": int(metadata["size"]),
            "starsAtSelection": int(metadata["stargazers_count"]),
            "licenseSpdx": license_info.get("spdx_id"),
        }
        if row["archived"]:
            raise RuntimeError(f"Archived repository cannot enter the frozen sample: {canonical}")
        frozen.append(row)
        print(f"[{index:02d}/{len(source['repositories'])}] {canonical} {row['commitSha'][:12]}")

    if len(frozen) != source["targetCount"]:
        raise RuntimeError(f"Expected {source['targetCount']} repositories, got {len(frozen)}")
    if len({row["id"] for row in frozen}) != len(frozen):
        raise RuntimeError("Repository IDs are not unique")
    if len({row["commitSha"] for row in frozen}) != len(frozen):
        raise RuntimeError("Unexpected duplicate commit SHA across repositories")

    output = {
        "schemaVersion": source["schemaVersion"],
        "frozenAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sourceSelectionDate": source["selectedAt"],
        "selectionPolicy": source["selectionPolicy"],
        "repositories": frozen,
    }
    write_json(FROZEN, output)
    print(f"Frozen {len(frozen)} repositories in {FROZEN}")


if __name__ == "__main__":
    main()

