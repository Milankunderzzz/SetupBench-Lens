# Tool and Experiment Version Matrix

Last updated: 2026-06-21

I maintain SetupLens product releases separately from SetupBench-Lens
experiment versions. A public release is not automatically eligible for the
paper, and an exploratory scan is not a confirmatory result.

## Current mapping

| SetupLens version | Status | Commit | Research use |
| --- | --- | --- | --- |
| `v0.1.0` | Released | `b229550b9dadcd701d791409d32737170635e400` | Historical public MVP only; not used for confirmatory metrics |
| `v0.1.1` | Release candidate in [SetupLens PR #9](https://github.com/Milankunderzzz/SetupLens/pull/9) | `491834a5da9bc568b6e7ced1a89beffa8c8e1555` (candidate commit) | Maintenance and exploratory validation only; not a frozen experiment version |
| `v0.2.0-alpha.1` | Blocked | To be recorded after the pilot freeze | Frozen build for the 10-repository pilot; pilot data remain excluded from confirmatory metrics |
| `v0.2.0` | Blocked | To be recorded after the release gate passes | Primary validated release for the final holdout evaluation and initial distribution |

The version roadmap is proposed in
[SetupLens PR #8](https://github.com/Milankunderzzz/SetupLens/pull/8). Until that
pull request and the maintenance release are merged, `v0.1.0` remains the
latest public release.

## Freeze rules

1. I record the exact SetupLens tag and full commit SHA in the benchmark
   manifest and local experiment database.
2. I do not pool findings produced by different SetupLens versions in one
   primary metric calculation.
3. The 10 pilot repositories are development data. Results from
   `v0.2.0-alpha.1` cannot contribute to confirmatory TP, FP, FN, precision,
   recall, F1, or timing claims.
4. Any post-freeze rule, weight, score-eligibility, or reporter change creates
   a new experiment version and requires a complete eligible-holdout rerun.
5. A release tag, CLI version, package metadata, GitHub Action reference, and
   published artifact must identify the same source state.

## `v0.2.0-alpha.1` gate

I will create the alpha tag only after:

- all 10 pilot repositories complete Pass A, Pass B, and Pass C;
- the pilot records pass validation;
- the candidate holdout set passes the contamination audit;
- pilot-driven tool changes stop; and
- the immutable SetupLens commit is recorded here and in the manifest.

## `v0.2.0` gate

I will publish the stable release only after:

- eligible holdout repositories are rescanned from the frozen commit;
- adjudicated Ground Truth exists;
- precision, recall, F1, and repository-bootstrap confidence intervals are
  computed;
- direct-execution and real human-comparison evidence is available;
- at least five external users have run the tool;
- at least three externally observed useful findings and one external feedback
  record are documented;
- a 30-second before/after demonstration is ready; and
- initial distribution metadata is aligned across GitHub Release, npm, the
  GitHub Action, and Marketplace preparation.

These gates prevent version numbers from implying evidence that has not yet
been collected.
