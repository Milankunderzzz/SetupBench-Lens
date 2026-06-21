# SetupBench-Lens Confirmatory Protocol

Version: 1.1
Decision date: 2026-06-19

## Research questions

- RQ1: Which setup-failure conditions occur in the selected repositories?
- RQ2: What condition-level precision, recall, and F1 does SetupLens achieve?
- RQ3: How does preflight diagnosis compare with direct execution and blinded human inspection?
- RQ4: How do results differ across Node.js, Python, and Docker-required workflows?

## Unit of analysis

The primary unit is an atomic setup condition at a pinned repository commit.
Multiple messages that require the same minimal fix are one condition. Messages
requiring different fixes are separate conditions.

## Three-pass annotation

### Pass A: independent ground truth

The annotator reads documentation and executes the approved workflow without
seeing SetupLens output. Failures are diagnosed in a disposable copy until an
atomic cause and minimal fix are supported by E2 or E3 evidence.

### Pass B: finding review

The frozen SetupLens commit scans the untouched snapshot. Each setup `fail` and
`warn` is independently labelled as true positive, false positive, conditional,
out of scope, or not assessable.

### Pass C: missed-condition review

Every E2/E3 Pass A condition without a matching SetupLens finding is a false
negative. Static-observable and execution-only misses are reported separately.

## Comparator definitions

- Direct execution: conditions exposed by the declared workflow before manual
  diagnostic investigation. Measure first-failure latency, exposed condition
  count, and time to an actionable atomic diagnosis.
- Human inspection: a blinded participant receives the pinned snapshot and
  task packet, but no SetupLens report. Measure conditions found, correctness,
  and elapsed time. Real participant records are mandatory.
- SetupLens: one scan from the frozen commit, evaluated against adjudicated
  condition-level ground truth.

Direct execution and human inspection are not assumed to produce the same type
of output as SetupLens. Precision/recall are computed only where a comparator
produces atomic diagnostic claims that can be matched to ground truth; time and
coverage are reported separately.

## Evidence levels

- E3: command, exit code, redacted output, and successful fix confirmation.
- E2: deterministic artifact contradiction or missing required path.
- E1: inferred candidate only.
- E0: no auditable evidence.

Primary metrics include only E2/E3 in-scope conditions. E1 and E0 appear in
sensitivity tables and never inflate true-positive counts.

## Execution isolation

Third-party code executes only in disposable Docker containers. Repositories are
copied to an ephemeral volume; no host secrets or Docker socket are mounted.
Containers use `--cap-drop ALL`, `no-new-privileges`, PID, CPU, memory, and time
limits. Docker-required projects use a disposable Docker-in-Docker daemon with
no host filesystem mounts.

## Review and release gate

All blockers, all SetupLens failures, and at least 20% of warnings require two
independent reviews. Disagreements retain both labels and an adjudication. The
SetupLens `v0.2.0` release is prohibited until dataset validation passes, human
comparison data exist, and the exact experiment commit is recorded.
The authoritative mapping between tool releases and experiment use is recorded
in `research/VERSION_MATRIX.md`. The `v0.2.0-alpha.1` build is pilot-only and
cannot contribute to confirmatory metrics. The stable `v0.2.0` release remains
prohibited until every gate in that matrix is satisfied.

## Pilot calibration and scoring freeze

I will complete full Pass A, Pass B, and Pass C review for 10 pilot repositories
before starting confirmatory evaluation. I will exclude these repositories from
the final confirmatory metrics and use them only to refine the protocol,
examples, rules, and scoring design.

Exploratory external tests exposed two distinct product issues. An unsupported
primary stack can receive a misleading numeric readiness grade, and a supported
project can receive a high score while a required dependency remains absent.
The first issue requires an explicit `unsupported` or `not scored` state. The
second requires stronger dependency evidence; increasing warning weights alone
would not establish that the project can run.

I will not tune weights from one or two examples. Any scoring change must be
justified by the pilot evidence, recorded in a new experiment version, frozen
before confirmatory scans, and evaluated on repositories that did not influence
the change. Reviewing machine-positive findings alone is insufficient for
recall because it cannot reveal false negatives; Pass A and Pass C remain
mandatory for every repository included in the primary recall result.

The unsupported-stack observation, product response, exclusion decision,
freeze gate, and C++ limitation are recorded in
`research/PILOT_STUDY_UNSUPPORTED_STACK.md`. The external C++ example and all
10 pilot repositories are development evidence and cannot contribute TP, FP,
FN, precision, recall, F1, or confirmatory timing results.

The confirmatory commit remains unset until the scoring correction is merged
and all pilot checks pass. Once recorded, every holdout scan must use that exact
commit. Any subsequent rule, weight, eligibility, or reporter change creates a
new experiment version and requires a complete holdout rerun.
