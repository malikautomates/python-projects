# Design Notes

**Document status:** Resolved
**Owner:** Repository author

---

## 1. Why rule-based, not ML-based

An LLM- or ML-based classifier would likely out-score a keyword list on ambiguous
phrasing. It was deliberately not used here, for a reason specific to a helpdesk
context: every classification this tool makes has to be **auditable by a
non-programmer**. When a service desk lead asks "why did this ticket get flagged
Low priority?", the answer is a single line in `triage/rules.py` — not a model
weight. That also makes the tool trivially tunable: a new keyword is a one-line
diff, not a retraining run. The tradeoff is accepted explicitly in section 3 below.

## 2. Why SLA windows are priority-based, not category-based

Response-time expectations in a real service desk are almost always driven by
business impact (a locked-out executive vs. a cosmetic UI bug), not by *what
kind* of problem it is. Modeling `SLA_HOURS` against `{"High": 4, "Medium": 24,
"Low": 72}` mirrors that — a Hardware ticket and a Security ticket carry the
same SLA if they carry the same priority. This is a starting table, not a fixed
policy; a real deployment would source it from the service desk's actual
published SLA document rather than from this file.

## 3. Known limitations (documented, not fixed, because they're the correct
tradeoff for this tool's purpose)

- **First-keyword-wins ordering is fixed.** A ticket mentioning both "VPN" and
  "password" always categorizes as `Account & Access` before `Network &
  Connectivity`, because dict iteration order in `CATEGORY_KEYWORDS` is fixed
  and the first match returns immediately. This is intentional (see §1 —
  determinism is the point) but means keyword *order*, not just keyword
  *presence*, is part of the rule set and belongs in code review when it
  changes.

- **Severity isn't inferred from meaning, only from trigger words.** The
  sample dataset includes `T-1033`, "Ransomware warning popped up on shared
  drive access" — a genuinely critical security incident — which this tool
  scores **Medium** priority, because the ticket text contains no keyword from
  `PRIORITY_KEYWORDS["High"]` ("urgent", "down", "critical", etc.). A human
  triager reads that subject line and immediately knows it's not routine; a
  keyword matcher does not. This is the sharpest edge of the rule-based
  approach and the strongest argument for pairing it with human review on
  Security-category tickets specifically, regardless of the priority score it
  produces.

- **No fuzzy matching.** "pasword" (typo) or "can not log in" (unlisted
  phrasing) won't match. A production version would normalize with basic
  stemming/typo-tolerance before matching.

## 4. Why SVG/PNG captures instead of OS screenshots

`scripts/capture_screenshots.py` regenerates every image under `screenshots/`
by calling the same `triage.report` functions the CLI uses, recording the
real Rich console output as SVG, and running the real charting function. This
was chosen over manually taking OS-level screenshots for one reason:
reproducibility. If the sample dataset or the report layout changes, running
one script regenerates every image from the tool's actual current output,
so the README can never silently drift out of sync with the code.
