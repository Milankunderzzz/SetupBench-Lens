from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from common import CONFIG, DATABASE, RAW, load_json


ANNOTATIONS = Path(__file__).resolve().parents[1] / "dataset" / "annotations"


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE study_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE repositories (
  repository_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  url TEXT NOT NULL,
  stratum TEXT NOT NULL CHECK (stratum IN ('node','python','docker')),
  subtype TEXT NOT NULL,
  default_branch TEXT NOT NULL,
  commit_sha TEXT NOT NULL,
  commit_date TEXT NOT NULL,
  size_kib INTEGER NOT NULL,
  stars_at_selection INTEGER NOT NULL,
  license_spdx TEXT,
  archived INTEGER NOT NULL CHECK (archived IN (0,1)),
  fork INTEGER NOT NULL CHECK (fork IN (0,1))
);
CREATE TABLE workflows (
  repository_id TEXT PRIMARY KEY REFERENCES repositories(repository_id),
  workflow_source TEXT NOT NULL,
  working_directory TEXT NOT NULL,
  container_image TEXT NOT NULL,
  bootstrap_command TEXT NOT NULL,
  primary_command TEXT NOT NULL,
  health_criterion TEXT NOT NULL,
  timeout_seconds INTEGER NOT NULL,
  approval_status TEXT NOT NULL,
  reviewer_notes TEXT
);
CREATE TABLE setuplens_scans (
  repository_id TEXT PRIMARY KEY REFERENCES repositories(repository_id),
  schema_version TEXT NOT NULL,
  tool_version TEXT NOT NULL,
  setuplens_commit TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  duration_ms INTEGER NOT NULL,
  files_indexed INTEGER NOT NULL,
  truncated INTEGER NOT NULL,
  detected_stacks_json TEXT NOT NULL,
  primary_stack TEXT,
  primary_stacks_json TEXT NOT NULL,
  setup_score INTEGER NOT NULL,
  setup_grade TEXT NOT NULL,
  setup_fail INTEGER NOT NULL,
  setup_warn INTEGER NOT NULL,
  setup_pass INTEGER NOT NULL,
  hygiene_score INTEGER NOT NULL,
  raw_report_path TEXT NOT NULL
);
CREATE TABLE setuplens_findings (
  repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
  finding_id TEXT NOT NULL,
  scope TEXT NOT NULL,
  category TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  evidence TEXT,
  recommendation TEXT,
  weight REAL NOT NULL,
  PRIMARY KEY (repository_id, finding_id)
);
CREATE TABLE direct_executions (
  execution_id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
  execution_kind TEXT NOT NULL,
  image_reference TEXT NOT NULL,
  image_digest TEXT,
  started_at TEXT NOT NULL,
  duration_ms INTEGER NOT NULL,
  timed_out INTEGER NOT NULL CHECK (timed_out IN (0,1)),
  exit_code INTEGER,
  command_text TEXT NOT NULL,
  log_path TEXT NOT NULL,
  log_sha256 TEXT NOT NULL,
  status TEXT NOT NULL
);
CREATE TABLE ground_truth_conditions (
  condition_id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
  execution_id TEXT REFERENCES direct_executions(execution_id),
  failure_code TEXT NOT NULL,
  phase TEXT NOT NULL,
  impact TEXT NOT NULL,
  evidence_level TEXT NOT NULL,
  evidence_location TEXT NOT NULL,
  minimal_fix TEXT NOT NULL,
  statically_observable INTEGER NOT NULL CHECK (statically_observable IN (0,1)),
  annotator_id TEXT NOT NULL,
  review_status TEXT NOT NULL,
  notes TEXT
);
CREATE TABLE finding_reviews (
  review_id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
  finding_id TEXT NOT NULL,
  annotator_id TEXT NOT NULL,
  verdict TEXT NOT NULL,
  false_positive_reason TEXT,
  evidence_level TEXT NOT NULL,
  failure_code TEXT,
  review_status TEXT NOT NULL,
  notes TEXT,
  FOREIGN KEY (repository_id, finding_id) REFERENCES setuplens_findings(repository_id, finding_id)
);
CREATE TABLE condition_matches (
  match_id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
  condition_id TEXT NOT NULL REFERENCES ground_truth_conditions(condition_id),
  review_id TEXT REFERENCES finding_reviews(review_id),
  outcome TEXT NOT NULL CHECK (outcome IN ('true_positive','false_negative','duplicate')),
  rationale TEXT NOT NULL,
  adjudication_status TEXT NOT NULL
);
CREATE TABLE human_trials (
  trial_id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
  participant_id TEXT NOT NULL,
  started_at TEXT NOT NULL,
  duration_seconds REAL NOT NULL,
  conditions_claimed INTEGER NOT NULL,
  true_conditions INTEGER NOT NULL,
  protocol_version TEXT NOT NULL,
  packet_hash TEXT NOT NULL,
  review_status TEXT NOT NULL
);
"""


def main() -> None:
    manifest = load_json(CONFIG / "repositories.frozen.json")
    workflows = {row["repository_id"]: row for row in csv.DictReader((CONFIG / "workflows.csv").open(encoding="utf-8", newline=""))}
    if DATABASE.exists():
        DATABASE.unlink()
    connection = sqlite3.connect(DATABASE)
    connection.executescript(SCHEMA)
    connection.executemany(
        "INSERT INTO study_metadata VALUES (?, ?)",
        [
            ("protocol_version", "1.0"),
            ("taxonomy_version", "1.0"),
            ("setuplens_commit", "424a3307dffd6e1bfaf9b5caca68046f930c790c"),
            ("sample_frozen_at", manifest["frozenAt"]),
        ],
    )

    for repository in manifest["repositories"]:
        connection.execute(
            "INSERT INTO repositories VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                repository["id"], repository["repository"], repository["url"], repository["stratum"],
                repository["subtype"], repository["defaultBranch"], repository["commitSha"],
                repository["commitDate"], repository["sizeKiB"], repository["starsAtSelection"],
                repository["licenseSpdx"], int(repository["archived"]), int(repository["fork"]),
            ),
        )
        workflow = workflows[repository["id"]]
        connection.execute(
            "INSERT INTO workflows VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                repository["id"], workflow["workflow_source"], workflow["working_directory"],
                workflow["container_image"], workflow["bootstrap_command"], workflow["primary_command"],
                workflow["health_criterion"], int(workflow["timeout_seconds"]),
                workflow["approval_status"], workflow["reviewer_notes"],
            ),
        )

        report_path = RAW / f"{repository['id']}-setuplens.json"
        report = load_json(report_path)
        setup = report["scopes"]["setup"]
        connection.execute(
            "INSERT INTO setuplens_scans VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                repository["id"], report["schemaVersion"], report["tool"]["version"],
                report["experiment"]["setupLensCommit"], report["generatedAt"], report["durationMs"],
                report["target"]["filesIndexed"], int(report["target"]["truncated"]), json.dumps(report["stacks"]),
                report.get("primaryStack"), json.dumps(report.get("primaryStacks", [])), setup["score"],
                setup["grade"], setup["summary"]["fail"], setup["summary"]["warn"], setup["summary"]["pass"],
                report["scopes"]["hygiene"]["score"], f"dataset/raw/{report_path.name}",
            ),
        )
        for finding in report["findings"]:
            connection.execute(
                "INSERT INTO setuplens_findings VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    repository["id"], finding["id"], finding["scope"], finding["category"], finding["status"],
                    finding["title"], finding["message"], finding.get("evidence"), finding.get("recommendation"), finding["weight"],
                ),
            )

    executions_path = Path(__file__).resolve().parents[1] / "dataset" / "direct-executions.jsonl"
    if executions_path.exists():
        for line in executions_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            connection.execute(
                "INSERT INTO direct_executions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    item["execution_id"], item["repository_id"], item["execution_kind"],
                    item["image_reference"], item.get("image_digest"), item["started_at"],
                    item["duration_ms"], int(item["timed_out"]), item.get("exit_code"),
                    item["command_text"], item["log_path"], item["log_sha256"],
                    item["status"],
                ),
            )

    annotation_imports = [
        (
            "ground_truth_conditions.csv",
            "INSERT INTO ground_truth_conditions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            lambda row: (
                row["condition_id"], row["repository_id"], row["execution_id"] or None,
                row["failure_code"], row["phase"], row["impact"], row["evidence_level"],
                row["evidence_location"], row["minimal_fix"], int(row["statically_observable"]),
                row["annotator_id"], row["review_status"], row["notes"],
            ),
        ),
        (
            "finding_reviews.csv",
            "INSERT INTO finding_reviews VALUES (?,?,?,?,?,?,?,?,?,?)",
            lambda row: (
                row["review_id"], row["repository_id"], row["finding_id"], row["annotator_id"],
                row["verdict"], row["false_positive_reason"] or None, row["evidence_level"],
                row["failure_code"] or None, row["review_status"], row["notes"],
            ),
        ),
        (
            "condition_matches.csv",
            "INSERT INTO condition_matches VALUES (?,?,?,?,?,?,?)",
            lambda row: (
                row["match_id"], row["repository_id"], row["condition_id"], row["review_id"] or None,
                row["outcome"], row["rationale"], row["adjudication_status"],
            ),
        ),
        (
            "human_trials.csv",
            "INSERT INTO human_trials VALUES (?,?,?,?,?,?,?,?,?,?)",
            lambda row: (
                row["trial_id"], row["repository_id"], row["participant_id"], row["started_at"],
                float(row["duration_seconds"]), int(row["conditions_claimed"]), int(row["true_conditions"]),
                row["protocol_version"], row["packet_hash"], row["review_status"],
            ),
        ),
    ]
    for filename, statement, convert in annotation_imports:
        path = ANNOTATIONS / filename
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if not any(row.values()):
                    continue
                connection.execute(statement, convert(row))
    connection.commit()
    connection.execute("PRAGMA integrity_check").fetchone()
    counts = {
        name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in ["repositories", "workflows", "setuplens_scans", "setuplens_findings", "direct_executions", "ground_truth_conditions", "finding_reviews", "condition_matches", "human_trials"]
    }
    connection.close()
    print(json.dumps({"database": str(DATABASE), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
