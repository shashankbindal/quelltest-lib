# Product Learnings Log

A running log of external insights — competitor content, community threads,
research, user feedback — translated into concrete actions for Quelltest.
Add new entries at the top. Keep every learning attached to an action;
insights without actions rot.

---

## 001 — "How to Find Edge Cases?" (Medium, @positron25) — 2026-07-18

Source: https://medium.com/@positron25/how-to-find-edge-cases-0c2c2293f5ef

A teach-the-human-skill piece for junior devs: edge-case finding as a
learnable discipline. Core framework: **happy path → list assumptions →
attack assumptions → handle gracefully**, plus classic QA techniques
(boundary value analysis, equivalence partitioning, state-transition
thinking, error injection).

### How it maps to us

| Their manual step | Our automation |
|---|---|
| List assumptions | Spec readers — docstrings, Pydantic, type hints ARE the written-down assumptions |
| Attack assumptions | Gate 5 — violation injected into source, test must fail |
| Boundary value analysis (17/18/65/66) | `BOUNDARY` constraint kind |
| Equivalence classes / valid sets | `ENUM_VALID`, `NOT_NULL`, `TYPE_CHECK` |
| Handle gracefully | WRITTEN tests prove the handling exists |

The article and the product are **complements**: the article teaches people
to write assumptions down; we prove the ones that are written down.

### Learnings → actions

1. **[Content — HIGH] We don't rank for the beginner question.**
   "How to find edge cases" is the entry-level query; our blog is all
   thesis-level (research, agentic verification). Write
   "How to Find Edge Cases in Python (a systematic method)" — teach the
   manual framework genuinely, show the automated version only at the end.
   Teach first, sell last. Likely our most-trafficked page.

2. **[Positioning — HIGH] "List assumptions → attack assumptions" is a
   better narrative spine than "5-gate pipeline."**
   Gate 5 *is* "attack assumptions," mechanized. Use this framing in
   homepage/docs copy: "the edge-case framework you already know, running
   automatically on every commit." Makes the product legible to people who
   learned testing from articles like this one.

3. **[Content + Trust — MEDIUM] Publish our blind spot.**
   Quelltest cannot find *undocumented* assumptions — the manual method
   can. A docs/blog page: "What Quelltest can't do, and the 15-minute
   manual practice that covers the gap." Disarming, honest, on-brand with
   the three-bucket philosophy (never silently pretend coverage).

4. **[Product — BACKLOG] `STATE_TRANSITION` constraint kind.**
   The article's state-transition technique maps to extractable specs:
   docstrings like "raises InvalidStateError if order is already shipped."
   Candidate: new ConstraintKind + docstring pattern in the reader + rule
   + violation injection. File a GitHub issue; not a today-priority.
   (Race conditions / infra error injection remain FLAGGED territory —
   correctly out of scope for auto-generation.)

5. **[Content craft — ONGOING] Lead with a named war story.**
   "The Regex Edge Case That Got Away" is the same device as our
   "I let Claude Code write my tests" post. Every future post opens with
   one concrete, specific failure story before the thesis.

### Template for future entries

```
## NNN — <source title> — YYYY-MM-DD
Source: <url>
<2-3 line summary>
### Learnings → actions
1. [Area — PRIORITY] <learning>. <concrete action>.
```
