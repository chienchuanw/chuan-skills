## Summary

{One sentence describing the performance issue and where it occurs.}

## Current Performance

{Quantify the problem with metrics. Specify how the measurement was taken.}

- **Metric**: {what was measured}
- **Current value**: {measured value with units}
- **Target value**: {acceptable threshold}
- **Measurement method**: {how the metric was captured, e.g., benchmark script, profiler, production monitoring}

## Affected Code Path

{Trace the slow path through the codebase. List file paths, function names, and the call chain.}

1. {Entry point: file:line -- function name}
2. {Next call: file:line -- function name}
3. {Bottleneck: file:line -- function name}

## Root Cause Analysis

{If the cause is known, explain it. If suspected, state it as a hypothesis. Include evidence from profiling, logging, or code analysis. Write "Investigation needed" if the cause is unknown.}

## Proposed Optimization

{Describe the optimization strategy:}

- **Approach**: {algorithmic change, caching, batching, lazy loading, etc.}
- **Expected improvement**: {quantified estimate if possible}
- **Trade-offs**: {memory vs speed, complexity vs performance, etc.}

## Acceptance Criteria

- [ ] {Metric} improves from {current} to at or below {target}
- [ ] No regressions in correctness (existing tests pass)
- [ ] {Additional condition}
- [ ] Benchmark added to track this metric going forward
