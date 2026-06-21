# SetupBench-Lens

I am building SetupBench-Lens as a reproducible benchmark for evaluating
preflight detection of repository setup failures in Node.js, Python, and
Docker projects.

The benchmark pins 50 public repositories, executes a declared setup workflow
inside disposable containers, stores redacted evidence in a local SQLite
database, and evaluates a frozen SetupLens commit against independently reviewed
ground truth.

This repository is a study in progress. It currently demonstrates a
reproducible protocol and an exploratory machine-scan pipeline; it does not yet
demonstrate that SetupLens is faster, more accurate, or more useful than direct
execution or human diagnosis.

## Study state

- Target sample: 50 repositories (20 Node.js, 20 Python, 10 Docker-required)
- Latest public SetupLens release: `v0.1.0` at `b229550b9dadcd701d791409d32737170635e400`
- SetupLens `v0.1.1` maintenance candidate: [PR #9](https://github.com/Milankunderzzz/SetupLens/pull/9) at `491834a5da9bc568b6e7ced1a89beffa8c8e1555`
- Pilot freeze target: `v0.2.0-alpha.1`, blocked until all 10 pilot reviews and the contamination audit are complete
- Validated release target: `v0.2.0`, blocked until confirmatory metrics, human comparison, and external validation are complete
- Exploratory machine-scan commit: `424a3307dffd6e1bfaf9b5caca68046f930c790c`
- Unsupported-stack correction merge commit: `0461ace04a1baf039412934acfed4e033dd07a9d`
- Confirmatory frozen commit: pending completion of the 10-repository pilot and contamination audit
- Taxonomy version: 1.0; annotation protocol: version 1.1
- Completed machine scans: 50, containing 1,025 findings
- Completed direct-execution probes: 2
- Adjudicated ground-truth conditions: 0
- Completed finding reviews: 0
- Human comparison: pending blinded participant completion
- Release gate: `v0.2.0` remains blocked until ground truth and human comparison are complete

I keep the current machine-scan review workbook at
`reports/LensBench_Machine_Scan_Review_2026-06-19.xlsx`. It separates the 50
repository summaries, all raw findings, a machine-positive review queue, 10
pilot repositories, and a deterministic negative-audit sample. Machine output
is not treated as ground truth or as a final paper result.

I record completed checkpoints and explicit pending work in the
[research progress log](research/PROGRESS_LOG.md).
The [tool and experiment version matrix](research/VERSION_MATRIX.md) records
which SetupLens release may be used at each research stage.

## Completed engineering checkpoint

- SetupLens now returns `Unsupported / Not scored` for unsupported, unknown,
  and empty repositories instead of assigning a misleading numeric grade.
- The correction is covered by 44 automated tests and passed all six CI
  combinations used by SetupLens.
- Pilot evidence and confirmatory holdout evidence are explicitly separated.
- The tool repository and benchmark repository have separate responsibilities,
  histories, and release gates.

These are engineering and protocol milestones. They are not substitutes for
Ground Truth or final evaluation metrics.

## Pilot before confirmatory evaluation

I will fully review 10 pilot repositories before scaling the workflow. These
pilot repositories are development data and will be excluded from confirmatory
metrics. I will use them to refine the annotation examples, workflow approval
criteria, and any future scoring changes.

The other 40 repositories remain candidate holdout data until I complete the
contamination audit for repositories previously used during SetupLens rule
development. Reviewing only SetupLens warnings and failures would estimate
precision but not recall, so the review plan also includes independent direct
execution and a negative-result audit.

An external C++ pilot exposed a misleading `98/100 A` result when no supported
primary stack was available. I document the observation and pre-freeze response
in the [unsupported-stack pilot record](research/PILOT_STUDY_UNSUPPORTED_STACK.md).
C++ remains outside the Node.js, Python, and Docker study scope, and the pilot
result is excluded from final metrics.

## Next checkpoint

1. Complete Pass A, Pass B, and Pass C for all 10 pilot repositories.
2. Audit the candidate holdout set for repositories used during rule development.
3. Validate the isolation workflow before additional third-party execution.
4. Freeze one immutable SetupLens commit after pilot-driven changes stop.
5. Rerun eligible holdout repositories and begin adjudicated metric calculation.
6. Collect real external-user and blinded human-comparison evidence without synthetic labels.

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
