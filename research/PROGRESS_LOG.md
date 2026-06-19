# Research Progress Log

## 2026-06-19: Experiment-readiness checkpoint

### Completed work

I completed four pieces of work needed before the pilot experiment can
continue:

1. **Corrected misleading unsupported-stack scoring.** SetupLens no longer
   reports a numeric readiness grade for an empty repository, an unknown
   primary stack, or an unsupported primary stack. The external C++ example
   now reports `Unsupported / Not scored` instead of `98/100 A`.
2. **Separated pilot and holdout evidence.** The external C++ case and the 10
   designated pilot repositories are development evidence. They are excluded
   from confirmatory TP, FP, FN, precision, recall, F1, and timing results.
3. **Defined the version-freeze boundary.** The confirmatory experiment must
   use one immutable SetupLens commit. Any later rule, weight, score-eligibility,
   or reporter change creates a new experiment version and requires a complete
   holdout rerun.
4. **Separated tool and research ownership.** SetupLens contains product code,
   tests, reporters, and user documentation. SetupBench-Lens contains the
   protocol, benchmark snapshots, annotation records, Ground Truth, and
   analysis outputs.

### Verification evidence

- SetupLens PR #5, `Avoid scoring unsupported repositories`, was merged on
  2026-06-19 (Asia/Shanghai).
- SetupLens merge commit: `0461ace04a1baf039412934acfed4e033dd07a9d`.
- All six CI combinations passed: Windows, Linux, and macOS on Node.js 18 and
  Node.js 22.
- The SetupLens suite contains 44 passing tests, including source-only C++,
  empty-repository, and unknown-stack regressions.
- CLI threshold mode returns exit code 2 when readiness is not scorable.

### Pull-request status

- SetupLens PR #5: merged.
- SetupBench-Lens PR #2, `Document my unsupported-stack pilot finding`: open
  as a draft and not yet merged.

### Not completed yet

- The 10 pilot repositories have not completed full Pass A, Pass B, and Pass C
  review.
- The final confirmatory SetupLens commit has not been frozen.
- Holdout scans, Ground Truth, precision, recall, F1, confidence intervals, and
  human-comparison results remain pending.
- No claim of product effectiveness is made from this checkpoint alone.
