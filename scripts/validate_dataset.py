from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess

from common import CONFIG, DATABASE, LOGS, RAW, REPOS, ROOT, load_json, sha256_text, write_json


EXPECTED_SETUPLENS_COMMIT = "424a3307dffd6e1bfaf9b5caca68046f930c790c"
REPORT = ROOT / "qa" / "dataset-integrity.json"


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = load_json(CONFIG / "repositories.frozen.json")
    repositories = manifest["repositories"]
    if len(repositories) != 50:
        errors.append(f"Expected 50 frozen repositories, found {len(repositories)}")
    strata = {name: sum(row["stratum"] == name for row in repositories) for name in ["node", "python", "docker"]}
    if strata != {"node": 20, "python": 20, "docker": 10}:
        errors.append(f"Unexpected strata: {strata}")

    for repository in repositories:
        root = REPOS / repository["id"]
        if not (root / ".git").exists():
            errors.append(f"Missing snapshot: {repository['id']}")
            continue
        actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, encoding="utf-8").strip()
        if actual != repository["commitSha"]:
            errors.append(f"SHA mismatch for {repository['id']}")
        report_path = RAW / f"{repository['id']}-setuplens.json"
        if not report_path.exists():
            errors.append(f"Missing SetupLens report: {repository['id']}")
            continue
        report = load_json(report_path)
        if report.get("experiment", {}).get("setupLensCommit") != EXPECTED_SETUPLENS_COMMIT:
            errors.append(f"SetupLens commit mismatch in {repository['id']}")

    workflows = list(csv.DictReader((CONFIG / "workflows.csv").open(encoding="utf-8", newline="")))
    pending = [row["repository_id"] for row in workflows if row["approval_status"] != "approved"]
    if pending:
        warnings.append(f"{len(pending)} workflows still require human approval")

    secret_markers = [
        re.compile(r"(?i)(password|secret|token|api[_-]?key)\s*[=:]\s*(?!<REDACTED>)[^\s]+"),
        re.compile(r"(?i)(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s]+"),
    ]
    checked_logs = 0
    if LOGS.exists():
        for path in LOGS.glob("*.log"):
            text = path.read_text(encoding="utf-8", errors="replace")
            checked_logs += 1
            if any(pattern.search(text) for pattern in secret_markers):
                errors.append(f"Potential unredacted secret in {path.name}")

    database_counts = {}
    if not DATABASE.exists():
        errors.append("Local SQLite database is missing")
    else:
        connection = sqlite3.connect(DATABASE)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            errors.append(f"SQLite integrity check failed: {integrity}")
        for table in ["repositories", "workflows", "setuplens_scans", "setuplens_findings", "direct_executions", "ground_truth_conditions", "finding_reviews", "condition_matches", "human_trials"]:
            database_counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        connection.close()
        if database_counts.get("repositories") != 50 or database_counts.get("setuplens_scans") != 50:
            errors.append(f"Database coverage mismatch: {database_counts}")

    result = {
        "valid": not errors,
        "releaseReady": not errors and not warnings and database_counts.get("human_trials", 0) > 0,
        "strata": strata,
        "snapshotsChecked": len(repositories),
        "logsChecked": checked_logs,
        "databaseCounts": database_counts,
        "errors": errors,
        "warnings": warnings,
    }
    write_json(REPORT, result)
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

