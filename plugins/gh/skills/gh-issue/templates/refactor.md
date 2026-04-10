## Summary

{One sentence describing what is being refactored and why.}

## Current State

{Describe the existing code structure, its problems, and the specific pain points. Reference file paths and function names.}

## Proposed Changes

{Describe the target state after refactoring. Be specific about structural changes.}

- **Files to modify**: {list with brief description of changes per file}
- **Files to create**: {new files if extracting or splitting}
- **Files to delete**: {files to remove if consolidating}

## Motivation

{Why this refactoring is worth doing now. Quantify if possible: "This module has N duplicate patterns", "Adding a new endpoint requires changing M files", etc.}

## Risk Assessment

- **Behavioral changes**: {Does this refactoring change any external behavior? If yes, describe. If no, state explicitly: "No behavioral changes."}
- **Breaking changes**: {Any API, config, or interface changes that affect consumers.}
- **High-risk areas**: {Parts of the refactoring that are most likely to introduce regressions.}

## Acceptance Criteria

- [ ] All existing tests pass without modification (unless testing internal implementation details)
- [ ] {Specific structural goal, e.g., "X module has a single responsibility"}
- [ ] {Another goal}
- [ ] No behavioral regressions
