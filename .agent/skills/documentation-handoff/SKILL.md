---
name: documentation-handoff
description: Use at the end of every implementation phase, after making significant changes, or when preparing work for another agent or developer.
---

# Documentation and Handoff Skill

## Purpose

Preserve context across agentic build sessions by documenting what changed, how to run it, and what remains.

## When to Use

Use after:

- completing a phase.
- adding a feature.
- fixing a bug.
- changing architecture.
- adding tests.
- stopping due to a blocker.

## Required Handoff Format

Write a concise handoff note with:

```text
## Completed
- [what was implemented]

## Files Changed
- [file path]: [summary]

## How to Run
```bash
[commands]
```

## Checks Performed
- [tests or manual checks]

## Known Limitations
- [limitations]

## Next Recommended Step
- [next action]
```

## Rules

- Be specific.
- Do not claim tests passed if they were not run.
- If something failed, state the error and likely cause.
- If a dependency is required, document it.
- If a phase boundary says stop, stop and report.

## Done Criteria

- Handoff note is written.
- Run commands are included.
- Known limitations are clear.
- Next step is unambiguous.
