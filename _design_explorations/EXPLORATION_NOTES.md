# RiskIntel — Visual Direction Exploration

**Status:** Three directions explored, none selected as final.
**Purpose:** Compare three high-fidelity executions of the frozen architecture, identify the strongest, surface trade-offs, defer the final call to the design lead.
**Architecture:** FROZEN. Only visual execution explored.

---

## Deliverables

| Direction | Path | Description |
|---|---|---|
| A | `_design_explorations/A_pure_editorial/decision-spine.html` | Pure editorial — what the brief literally specifies |
| B | `_design_explorations/B_editorial_spatial/decision-spine.html` | Editorial + spatial confidence — premium SaaS execution |
| C | `_design_explorations/C_industrial_confident/decision-spine.html` | Editorial + industrial confident — Bloomberg-for-credit execution |

All three render the same content (Ramesh Kumar, Person B, "Moderately Ready", 0.68 probability). The same component inventory. The same six principles. The same single accent. Different visual execution.

---

## Direction A — Pure Editorial

**Visual logic:** Literal interpretation of the brief. Hairline structure. Maximal whitespace. Verdict as the only chromatic accent. Everything else is ink-on-paper in mono and body type. Section labels in mono small-caps. The page reads as a printed page, not an app.

**Strengths:**
- Truest to the brief's "Editorial Finance" direction. The Economist, not Stripe Press.
- Accent rationing is automatic — the verdict is the only color moment.
- Most "world-class" by the design lead's criterion: distinctive, calm, non-SaaS.
- Audit footer reads as a colophon, not a status bar.
- Mobile degradation is trivial: just stack, no structural redesign.

**Weaknesses:**
- The 44pt verdict on a 1200px page is small. The product's hero moment doesn't dominate.
- The probability range (mono single line) is hard to scan.
- The driver bars are 1px thin — almost invisible at a glance.
- The "what to do" section is a typographic afterthought.
- "What to do" and "drivers" feel like they could be one block; the separation feels arbitrary.

**Reservations:**
- A page this restrained can read as "underbuilt" or "almost a wireframe" to procurement teams.
- The 3-col driver grid uses a single 1px hairline bar, which is technically a chart but reads as decoration.

---

## Direction B — Editorial + Spatial

**Visual logic:** Same direction (editorial, single-accent, two-tone), but with deliberate typographic scale jumps. A 56px verdict against a 32px name. 12-col spatial grid. The probability becomes a visible track. The drivers become card-like blocks (still no background, but with a top border and a rank number). The audit footer becomes a 2-col grid with a key column. The recommendation column gets left rules.

**Strengths:**
- The verdict dominates the hero. The product has a face.
- The probability range is a real track with a center marker, readable at a glance.
- The driver hierarchy is visible at scan speed: rank, name, value, bar, sign.
- "Largest positive" / "Largest negative" annotations are visible (the M18 redundant signals working as designed).
- The audit footer reads as a record, not a footnote.
- Procurement teams will see a product. Loan officers will see a tool. Both correct.

**Weaknesses:**
- The 12-col grid is the largest design commitment. Mobile collapse is non-trivial.
- The driver "card with rank" is closer to SaaS pattern than the brief wants. Still no background fill (so it's a row, not a card), but the rank number and top border are weightier than Direction A.
- More type sizes in use. Risk of typographic drift.

**Reservations:**
- The "premium SaaS" execution is exactly what the brutal review warned against. But the brief's "Editorial Finance" is itself a premium aesthetic; the question is which premium.

---

## Direction C — Editorial + Industrial Confident

**Visual logic:** Same direction, but with technical-manual structure. 2px black borders. 6-cell table-like metadata strip. Numbered section headers ("02 / Drivers"). Probability as a 28px number on its own line. Drivers as gridded blocks with borders, like a parts catalog. Recommendations as numbered cards with inverted-rank number. Audit footer as a 2-col table with a dark inverted header bar.

**Strengths:**
- Maximum information density. The user reads everything in one viewport, two.
- The "number labels" (01, 02, 03, 04) make the document structure scannable.
- The audit footer is the most defensible to a regulator. Looks like a docket entry.
- The decision reads as serious. The aesthetic matches the gravity.
- Officer in the field with intermittent connectivity: dense page, small payload.

**Weaknesses:**
- The borders are too many. Two pixels of black between every block becomes visual noise.
- The "numbered section" treatment is closer to legal-form than to financial publication.
- The driver blocks with all-borders are functionally a table, but a table the architecture explicitly forbade.
- Mobile: the grid breaks at 1024px. Tablet is awkward.
- The "premium" register is a Bloomberg Terminal, not a Stripe Press. Procurement teams will see an internal tool.

**Reservations:**
- Drift toward the clinical-dashboard register the brief explicitly rejected.
- The numbered sections (02, 03, 04) are a 1990s technical-manual pattern. The brief forbids LLM-trained filler; this is the structural-manual equivalent.

---

## Side-by-Side Comparison

| Dimension | A: Pure Editorial | B: Editorial + Spatial | C: Industrial Confident |
|---|---|---|---|
| Verdict dominance | Moderate (44pt) | High (56pt) | Moderate (42pt) |
| Color rationing | ~3% | ~6% | ~4% |
| Information density | Low (visible) | High (readable) | Maximum (scannable) |
| Procurement appeal | Low | High | Moderate |
| Officer appeal | High (calm) | High (clear) | Moderate (dense) |
| Mobile degradation | Trivial | Moderate | Hard |
| Brief fidelity | Maximum | High | Moderate |
| Distinctive risk | High (risks "underbuilt") | Moderate | Moderate (risks "clinical") |
| Audit-footer strength | High (colophon) | High (record) | Maximum (docket) |

---

## Recommendation

**Direction B is the strongest execution of the brief.**

Direction A is the most faithful to the brief, but at the cost of visual presence. The product is consequential; the page should look consequential. A is a wireframe with hair.

Direction C is the most information-dense, but crosses into Bloomberg territory. The borders are too many. The numbered sections are anachronistic. The brief is editorial, not industrial.

Direction B keeps the brief's two-tone, single-accent discipline, but commits to the verdict as a hero. The 12-col grid is the right spatial commitment. The probability track and the driver bars work at scan speed. The audit footer is a record, not a footnote. The aesthetic is "The Economist with a credit analyst's notebook," not "terminal."

**B is the build target. A is the constraint that keeps B honest. C is the warning about what happens if spatial confidence is overcorrected into density.**

---

## What This Exploration Did Not Change

- The architecture is frozen. No component was added, removed, or modified.
- The token system is frozen. The same burnt sienna accent, the same off-white paper, the same ink, the same mono body. Type scale unchanged.
- The principles are frozen. Same dignity-preserving register. Same forbidden patterns. Same single-accent rationing.
- The decision spine content is identical. Same applicant, same numbers, same verdict.

The only thing that changed: the visual execution of the same architecture, content, and tokens. Three different ways to render the same product.

---

## Open Questions for the Design Lead

1. **Verdict size:** 44pt (A) vs 56pt (B) vs 42pt (C). B is the recommendation, but 44pt (A) is closer to the architecture's `type.display.size` token. Does the architecture need a 56pt "hero" tier, or is B's 56pt a one-off deviation that should be tokenized?
2. **Section numbering:** C uses 02/03/04. B uses section-label-as-eyebrow. A uses section-label-as-eyebrow. C's approach is more information-architectural. Does the brief want numbering or not?
3. **Driver bar weight:** A uses 1px. B uses 2px with a 4px indicator. C uses 3px with a 5px indicator. The architecture's tokens do not specify this. Resolution: add a `--bar-track-width` and `--bar-indicator-width` token family.
4. **Probability range as a track:** B and C include a visible track. A renders the range as text only. The architecture's §10 specifies `ProbabilityRange` as a track. B and C are conformant. A is non-conformant. A is editorial restraint over contractual correctness; resolve by aligning A to the contract.

---

## Build Signal

None of these is final. All three are built and render. The architecture is unchanged. The tokens are unchanged. The decision to pick A, B, or C (or a hybrid) belongs to the design lead. Until that decision, all three stand as parallel artifacts.

If a hybrid is chosen, the recommended composition is: B's hero and probability track, A's restrained driver treatment, C's audit footer structure, and B's recommendation treatment. That hybrid is the strongest possible execution of the brief.
