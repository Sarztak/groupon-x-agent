# Agent Notes — Derived Patterns (Not Doctrine)

This folder contains **patterns named for agent use** — recognizable categories that help the model (and human reviewers) move faster when generating or auditing copy.

## What's here is NOT doctrine.

Files in this folder are **derived from** the Messaging House and TOV. They don't introduce new positions or rules. They just give names to patterns the source documents express through example or implication.

If anything in `agent-notes/` ever appears to contradict `messaging-house.md` or `tov/*.md`, the doctrine layer wins. Open a CHANGELOG entry and fix the drift.

## Why this layer exists

The Messaging House and TOV are designed as **strategic and verbal frameworks for humans**. They're descriptive — they describe what the brand believes, what good copy looks like, and why.

The model benefits from **named, recallable patterns** — "the rescue narrative anti-pattern," "the validating-comparison headline pattern," "the held-back-punchline humor mechanism." Naming makes them faster to recognize when reviewing and faster to recall when generating.

That's the only reason this layer exists. It's a memorability aid, not a parallel brand system.

## What's in here

| File | Purpose | Derived from |
|---|---|---|
| `anti-patterns.md` | 15 named anti-patterns with examples and fixes | TOV "✕ Don't" examples + MH "We never say" |
| `named-patterns.md` | Named headline patterns + humor mechanisms | TOV "Techniques that work" across channels |
| `review-rubric.md` | The 7-point checklist used by `/groupon-review` | TOV constants + MH voice guardrails |

## Update rule

When the Messaging House or TOV ships a new version:
1. Update the doctrine layer first (`messaging-house.md` and `tov/`)
2. Then review this folder for drift — has a constant changed? a "Don't" example been retired? a new technique been introduced?
3. Update names and examples here to match
4. **Never add to this folder a pattern that isn't grounded in the doctrine layer.** If you think a new anti-pattern is real, add it to the TOV first.
