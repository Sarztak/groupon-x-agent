# Review Rubric — The 7-Point Checklist (Derived)

> **Layer:** Agent scaffolding — derived from doctrine.
> **Derived from:** TOV v4.6 "Voice DNA" constants + Messaging House v1 "We say / We never say"
> **Used by:** `/groupon-review` slash command

This is the rubric applied during copy review. It distills the doctrine into seven binary-or-tri-state questions that can be answered against any piece of copy.

---

## The Checklist

### 1. Immediately clear?

**The test:** Read the first line in isolation. Can someone understand what they're getting?

**Pass:** The reader knows the offer or experience in the first 2 seconds.
**Partial:** The offer is clear but buried — the first line is decoration.
**Fail:** The reader has no idea what's being offered after reading the entire piece.

**Why it matters:** Users scan. Personality that front-runs clarity is personality wasted.

---

### 2. Sounds like a person?

**The test:** Remove the brand name. Could a friend have said this?

**Pass:** The line reads like something a sharp friend would text — observed, specific, not effortful.
**Partial:** Sounds like a brand trying to sound human.
**Fail:** Sounds like committee output — corporate, formal, distant.

**Why it matters:** Groupon's voice is "well-informed friend, not brand."

---

### 3. Passes "we add, we don't fix"? ⭐ THE PRIMARY TEST

**The test:** Does the copy frame the reader's current state as deficient or in need of rescue?

**Pass:** The reader's life is assumed to be good. Groupon is the addition.
**Partial:** Doesn't explicitly diminish the reader, but implies they should be doing something different.
**Fail:** Explicitly positions the reader as bored, lacking, or in need of saving. (E.g. "Your boring Saturday called.")

**Why it matters:** This is the #1 voice principle in the TOV. A fail here outranks every other check — copy that fails this is rewrite-only.

---

### 4. Moment of interest?

**The test:** Is there one line, detail, or angle that earns attention?

**Pass:** At least one specific noun, twist, or observation that wouldn't appear in generic deals copy.
**Partial:** Specificity exists but it's generic-flavored ("real reviews" without quantification, "highly rated" without a star).
**Fail:** Could be copy-pasted into any aggregator with no edits.

**Why it matters:** Without a moment of interest, the copy is forgettable — and forgettable copy is invisible.

---

### 5. Nothing wasted?

**The test:** Can anything be removed without loss of meaning?

**Pass:** Every word earns its space. Cutting anything removes information.
**Partial:** 10-20% of the copy could be trimmed.
**Fail:** Over a third of the copy is filler.

**Why it matters:** Discipline. Over-writing is a sign of uncertainty. Tight copy signals confidence.

---

### 6. Works without design?

**The test:** Strip the imagery, the layout, the bold styling. Does the copy still land?

**Pass:** Reads cleanly as plain text. Standalone clarity.
**Partial:** Works with imagery but loses some impact without.
**Fail:** Depends on design to make sense.

**Why it matters:** Across channels, copy needs to survive contexts the design hasn't been built for (UAC rotation, push truncation, screen-reader interpretation, dark mode).

---

### 7. Survives the brand-drift test?

**The test:** Cover the Groupon logo. Could a competitor (Travelzoo, LivingSocial, Yelp Deals, RetailMeNot) run this line with no edits?

**Pass:** The line names something specifically Groupon — a merchant, a moment, a phrasing tied to one of the three brand pillars.
**Partial:** Mostly Groupon-flavored but has 1-2 lines that could drift.
**Fail:** Brand-interchangeable. Could be any deals site.

**Why it matters:** Specificity is what makes copy un-copyable. A line a competitor can steal is a line that doesn't build Groupon's equity.

---

## Scoring

Count the Yes answers (Partial counts as 0.5):

- **6.5–7 / 7 = Ship it.**
- **4.5–6 / 7 = Minor revision.** Specific issues to address but the bones are right.
- **0–4 / 7 = Rewrite.** Don't patch — start over with the principles in mind.

**Special rule:** A fail on #3 (we add, we don't fix) is **rewrite-only**, regardless of the total score.

---

## Sequence to Apply

When reviewing:

1. **Detect channel and segment first** — texture targets and pillar expectations depend on this. Don't score without context.
2. **Run #3 first** — the rescue-narrative check. If it fails, stop scoring and go straight to rewrite. The other checks are moot if the foundational voice principle is broken.
3. **Then #7** — the brand-drift test. Second most important; if a competitor could run it, the copy hasn't earned its space.
4. **Then #1, #4, #5, #6** — clarity and craft.
5. **Then #2** — the "friend test." This is the most subjective check and benefits from coming last when you have full context on the copy.
6. **Finally, identify any named anti-patterns** (see `anti-patterns.md`).
7. **Compose the verdict + rewrite** following the `/groupon-review` output format.

---

## Anti-Pattern Cross-Reference

Each anti-pattern in `anti-patterns.md` corresponds to one or more checklist failures:

| Anti-pattern | Most likely fails |
|---|---|
| Overwritten copy | #5 (nothing wasted) |
| Obvious jokes / stacked puns | #4 (genuine interest) + #2 (sounds like a person) |
| Random weirdness | #1 (clear) + #4 (interest with substance) |
| Clickbait phrasing | #2 (sounds like a person) + #7 (brand drift) |
| Inspirational fluff | #4 (moment of interest) + #7 (brand drift) |
| Trying to sound young | #2 (sounds like a person) |
| Explaining the joke | #5 (nothing wasted) |
| Exclamation points | #5 (nothing wasted) + #2 (sounds like a person) |
| Generic superlatives | #4 (moment of interest) + #7 (brand drift) |
| Corporate phrasing | #2 (sounds like a person) + #7 (brand drift) |
| **Rescue narrative** | **#3 — primary** |
| Brand-as-protagonist | #2 + #3 |
| Aggregator voice | #7 (brand drift) — primary |
| Generic aggregator hooks | #4 + #7 |
| Digital-coded hooks | #4 (Lived pillar failure) |
