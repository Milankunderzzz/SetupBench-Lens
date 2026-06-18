# SetupBench-Lens

SetupBench-Lens is a reproducible benchmark for evaluating preflight detection
of repository setup failures in Node.js, Python, and Docker projects.

The benchmark pins 50 public repositories, executes a declared setup workflow
inside disposable containers, stores redacted evidence in a local SQLite
database, and evaluates a frozen SetupLens commit against independently reviewed
ground truth.

## Study state

- Target sample: 50 repositories (20 Node.js, 20 Python, 10 Docker-required)
- SetupLens candidate commit: `424a3307dffd6e1bfaf9b5caca68046f930c790c`
- Taxonomy and annotation protocol: version 1.0
- Human comparison: pending blinded participant completion
- Release gate: `v0.2.0` remains blocked until ground truth and human comparison are complete

## Reproduce

```powershell
python scripts/freeze_manifest.py
python scripts/clone_repositories.py
python scripts/inventory_workflows.py
```

Execution is intentionally a separate, review-gated step. Review
`config/workflows.csv` before running third-party code:

```powershell
python scripts/run_direct.py --approved
node scripts/run_setuplens.mjs
python scripts/build_database.py
python scripts/validate_dataset.py
python scripts/compute_metrics.py
```

Do not add credentials or mount the Docker socket into benchmark containers.
Raw logs are redacted and remain untracked by Git.

## Primary metrics

Metrics are condition-level and computed only from adjudicated E2/E3 evidence:

- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = 2PR / (P + R)

Accuracy is not reported because the true-negative universe is open-ended.
Confidence intervals are bootstrapped by repository.

## Integrity rules

1. Pass A annotators cannot inspect SetupLens output.
2. Every snapshot is identified by an immutable commit SHA.
3. Every direct command records image digest, timeout, exit code, and redacted log hash.
4. SetupLens rule changes after annotation begins require a new experiment version.
5. Human inspection results must come from real participants; synthetic labels are prohibited.

