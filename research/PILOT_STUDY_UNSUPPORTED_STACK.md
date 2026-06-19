# Pilot Study: Unsupported Stack Scoring

Status: pre-confirmatory product validation  
Observation date: 2026-06-18  
Protocol update date: 2026-06-19

## Pilot observation

During an external exploratory test, a participant scanned a minimal C++
repository containing a single source file. SetupLens identified no supported
stack but still reported a setup-readiness score of 98/100 (grade A). Most
generic checks passed and the unsupported-stack warning deducted only two
points, so the numeric grade could be mistaken for evidence that the C++
project was ready to run.

This test did not establish whether the C++ program could compile or execute.
It established that the readiness score was not valid when no supported
primary-stack rules had run.

## Tool improvement

Before the confirmatory experiment, SetupLens will distinguish score
eligibility from finding severity. Empty repositories, repositories without a
detectable primary stack, and repositories whose primary stack is unsupported
will return `not_scored` instead of a numeric readiness grade. C++ evidence is
used only to identify an unsupported boundary; SetupLens does not claim to
diagnose C++ setup requirements.

Regression coverage includes:

- a minimal source-only C++ repository;
- an empty repository;
- a non-empty repository with an unknown primary stack;
- terminal and HTML output that must not display a numeric readiness grade for
  an unsupported repository.

Threshold-based CLI and GitHub Action runs fail closed when a readiness score
cannot be calculated.

## Experimental protocol

The external C++ case is pilot evidence, not a confirmatory benchmark sample.
It influenced the scoring contract and is therefore excluded from all reported
precision, recall, and F1 calculations. The 10 designated pilot repositories
are also excluded from confirmatory metrics. Their purpose is to test the
annotation procedure, reveal ambiguous rules, and justify changes before the
experiment is frozen.

The existing 50-repository machine-scan workbook remains exploratory. Its
machine findings are not Ground Truth and are not final paper results.

## Version freeze

The confirmatory SetupLens commit is not frozen yet. The freeze gate is:

1. merge the unsupported-stack scoring correction;
2. pass the complete automated test suite on Windows, Linux, and macOS;
3. rerun the pilot checks and record the resulting report schema;
4. record the immutable SetupLens commit SHA in the benchmark manifest;
5. rerun every eligible holdout repository from that exact commit;
6. prohibit rule, weight, or scoring changes within that experiment version.

Any later tool change requires a new experiment version and a complete rerun;
results from different commits must not be pooled as one confirmatory result.

## Limitations

The current study scope is Node.js, Python, and Docker. C++ is outside the
supported diagnostic and evaluation scope. SetupLens may identify C++ as an
unsupported primary stack, but it cannot determine whether a compiler, CMake,
library, linker, or platform requirement is satisfied. `Not scored` means that
the tool lacks sufficient supported coverage; it does not mean the repository
is broken or ready.

This pilot finding comes from one external C++ example and must not be used to
estimate prevalence, accuracy, or user-time savings.
