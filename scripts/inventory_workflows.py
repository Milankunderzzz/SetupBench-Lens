from __future__ import annotations

import csv
import json
from pathlib import Path

from common import CONFIG, REPOS, load_json


OUTPUT = CONFIG / "workflows.csv"
FIELDS = [
    "repository_id", "commit_sha", "stratum", "workflow_source", "working_directory",
    "container_image", "bootstrap_command", "primary_command", "health_criterion",
    "timeout_seconds", "approval_status", "reviewer_notes",
]


def node_plan(root: Path):
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    scripts = package.get("scripts") or {}
    manager = "npm"
    if (root / "pnpm-lock.yaml").exists():
        manager = "pnpm"
    elif (root / "yarn.lock").exists():
        manager = "yarn"
    elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        manager = "bun"
    if manager == "npm":
        install = "npm ci" if (root / "package-lock.json").exists() else "npm install"
    else:
        install = f"corepack enable && {manager} install --frozen-lockfile"
    test_name = next((name for name in ["test", "check", "lint", "build"] if name in scripts), None)
    command = f"{manager} run {test_name}" if test_name else f"{manager} pack --dry-run"
    return "package.json", "node:22-bookworm", install, command, "primary command exits 0"


def python_plan(root: Path):
    source = next((name for name in ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt"] if (root / name).exists()), "README")
    install = "python -m pip install --disable-pip-version-check -e ."
    if (root / "requirements-dev.txt").exists():
        install = "python -m pip install --disable-pip-version-check -r requirements-dev.txt && " + install
    command = "python -m pytest -q"
    return source, "python:3.12-bookworm", install, command, "test collection and execution exit 0"


def docker_plan(root: Path):
    compose = next((name for name in ["compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml"] if (root / name).exists()), "")
    if compose:
        return compose, "docker:29-cli", "docker compose config", "docker compose build", "Compose config and image build exit 0"
    dockerfile = "Dockerfile" if (root / "Dockerfile").exists() else ""
    return dockerfile or "README", "docker:29-cli", "docker version", "docker build -t setupbench-candidate .", "image build exits 0"


def main() -> None:
    manifest = load_json(CONFIG / "repositories.frozen.json")
    rows = []
    for repository in manifest["repositories"]:
        root = REPOS / repository["id"]
        if repository["stratum"] == "node":
            plan = node_plan(root)
        elif repository["stratum"] == "python":
            plan = python_plan(root)
        else:
            plan = docker_plan(root)
        rows.append({
            "repository_id": repository["id"],
            "commit_sha": repository["commitSha"],
            "stratum": repository["stratum"],
            "workflow_source": plan[0],
            "working_directory": ".",
            "container_image": plan[1],
            "bootstrap_command": plan[2],
            "primary_command": plan[3],
            "health_criterion": plan[4],
            "timeout_seconds": "900",
            "approval_status": "pending_human_review",
            "reviewer_notes": "Heuristic candidate; verify against README before execution.",
        })

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} review-gated workflow candidates to {OUTPUT}")


if __name__ == "__main__":
    main()

