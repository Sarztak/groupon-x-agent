# Sources & File Map

This skill is **derived 1:1** from two source documents. Every doctrine file (`messaging-house.md` and everything under `tov/`) has a `Source:` header pointing at the section and version it derives from. Agent-scaffolding files (under `agent-notes/`) are derived but not 1:1 — they're patterns named for agent use, not parallel doctrine.

When the source documents are updated, this file is the index for what to update where.

---

## Source Documents

### 1. B2C Brand Messaging House (v1, Q4 2025)

**Authority:** Strategic framework. **The Messaging House wins on any conflict** with downstream documents (per the TOV's own statement).

**File location:** `/Users/earcediano/Documents/Brand Strategy/groupon_messaging_house_v1.html`

**Sections:**
- Roof — B2C Brand Promise
- Value Wedge
- Brand Pillars 01, 02, 03 (with RTBs + Example lines)
- Basement — Company belief + Mission
- Audience Architecture (4 segments + strategic context + Gen Z subsegment)
- Voice Guardrails (do/don't, humor dial, channel messaging guide)

### 2. B2C Verbal System (v4.6, April 2026)

**Authority:** Verbal system. Companion to the Messaging House. Defers to the Messaging House on conflicts.

**File location:** `/Users/earcediano/Documents/Brand Strategy/B2C_Groupon_TOV_2.0_2026.html`

**Sections:**
- How to write for B2C (the 4 voice pillars — Unexpected, Curious, Playful, Lived)
- Voice DNA — what never changes (Always/Never + texture dial)
- Audience modulation (4 segments + Gen Z)
- Key messages (brand descriptions)
- Pillar-to-copy translator
- Funnel application
- Channel guide (Organic Social, Display Ads, CRM, SEM, SEO, IMP)

---

## File-to-Source Map

### Doctrine layer

| File | Source | Source section |
|---|---|---|
| `messaging-house.md` | Messaging House v1 | Entire document (roof, value wedge, pillars, basement, audience architecture, voice guardrails) |
| `tov/voice-pillars.md` | TOV v4.6 | "How to write for B2C" — four pillars |
| `tov/voice-dna.md` | TOV v4.6 | "Voice DNA — what never changes" |
| `tov/audience-modulation.md` | TOV v4.6 | "Audience modulation" — including Gen Z subsegment |
| `tov/pillar-translator.md` | TOV v4.6 | "Pillar-to-copy translator" |
| `tov/key-messages.md` | TOV v4.6 | "Key messages" |
| `tov/funnel-application.md` | TOV v4.6 | "Funnel application" |
| `tov/channels/organic-social.md` | TOV v4.6 | "Channel guide — Organic Social & Influencers" |
| `tov/channels/display-ads.md` | TOV v4.6 | "Channel guide — Display Ads" |
| `tov/channels/crm.md` | TOV v4.6 | "Channel guide — CRM" |
| `tov/channels/sem.md` | TOV v4.6 | "Channel guide — SEM" |
| `tov/channels/seo.md` | TOV v4.6 | "Channel guide — SEO" |
| `tov/channels/imp.md` | TOV v4.6 | "Channel guide — IMP" |

### Agent-scaffolding layer (derived, not doctrine)

| File | Derived from | Purpose |
|---|---|---|
| `agent-notes/anti-patterns.md` | TOV "✕ Don't" examples + MH "We never say" | Named anti-patterns for agent recognition |
| `agent-notes/named-patterns.md` | TOV "Techniques that work" sections across channels | Named headline + humor patterns for agent recall |
| `agent-notes/review-rubric.md` | TOV constants + MH voice guardrails | The 7-point checklist for /groupon-review |

---

## Known Terminology Notes

### Pillar #4: "Hands-on" vs "Lived"

- **Messaging House v1** (Q4 2025): uses *"Hands-on"* in the Voice Guardrails section
- **TOV v4.6** (April 2026): renames to *"Lived"*, explicitly described as a clarification: *"'Lived' is shorthand for doing, not having — written in the past tense of participation. The opposite of consumption."*

**This skill uses *"Lived"*** as the primary term because:
1. The TOV is the more recent document
2. The rename is described as a clarification, not a substantive change
3. The TOV's definition is sharper for agent use ("doing, not having")

If a future Messaging House version reverts or supersedes this, update `tov/voice-pillars.md` and this file accordingly.

### "Three Brand Pillars" (Messaging House) vs "Voice Pillars" (TOV)

These are **different things**. Easy to confuse:

- **Brand Pillars** (01, 02, 03) — strategic, from the Messaging House. They're *what Groupon stands for*. Each has RTBs and example lines.
  - 01: Real life, worth leaving for
  - 02: Quality you can actually trust
  - 03: Your city has more than you think

- **Voice Pillars** (Unexpected, Curious, Playful, Lived) — verbal, from the TOV. They're *how Groupon talks*. They describe the texture of language, not what it's about.

The skill uses both. Brand Pillars determine *which one leads* (via the Pillar-to-Copy Translator). Voice Pillars apply to *all copy at all times* — every piece passes all four.

---

## When the Sources Change

### If the Messaging House ships v2:

1. Read the new version
2. Update `messaging-house.md` section by section
3. Update the source version in this file (and in `messaging-house.md`'s header)
4. Update `agent-notes/anti-patterns.md` if "We never say" changed
5. Check `tov/voice-pillars.md` for terminology drift (esp. Pillar #4)
6. Bump skill version in `plugin.json` and `marketplace.json`

### If the TOV ships v5.x:

1. Read the new version
2. For each `tov/*.md` file, update the corresponding section's content
3. Update the source version in this file (and in each affected file's header)
4. Add new approved examples to `evals/golden-set.json`
5. Update `agent-notes/anti-patterns.md` if the "Don't" examples or constants changed
6. Update `agent-notes/named-patterns.md` if new techniques were introduced
7. Bump skill version

### If only a single channel section is revised in the TOV:

1. Update just that file (e.g. `tov/channels/crm.md`)
2. Update its source-section line
3. Update its examples in `golden-set.json`
4. Patch version (e.g. v3.0.0 → v3.0.1)

The point of this two-layer architecture is that doctrine updates are mechanical. If you find yourself interpreting how to apply a source-doc change, something has drifted — the file you're working in might have agent-scaffolding mixed in, and should be cleaned up.
