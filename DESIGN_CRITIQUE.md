# RiskIntel — Design Critique

**Version:** 1.0
**Status:** Pre-build gate review
**Inputs read:**
- `DESIGN_BRIEF.md` v1.0
- `FRONTEND_ARCHITECTURE.md` v1.0
- Brutal Review of `FRONTEND_ARCHITECTURE.md` (internal, undated)

**Author:** Principal Product Designer
**Role of this document:** Not a rewrite. Not a refactor. A gate decision: what survives, what changes, what dies, what is missing.

---

## Executive Summary

The architecture inherits a strong design brief and weakens it. The brief established the editorial-finance direction, the two-tone color system, the dignity-preserving register, and the audit-first stance. The architecture accepts these as doctrine but applies them inconsistently at the screen level. The result is a document that reads as anti-SaaS in its principles and as pro-SaaS in its composition.

**Strongest decisions (must survive):**
- The decision spine as the architectural anchor (§3.5).
- The audit footer as a non-negotiable global element (§3.13, §10.3.5).
- The "rule of three" on first paint: identity, verdict slot, audit footer (§0).
- The typing of loading as a typographic statement, not a spinner (§8).
- The closed component library with explicit state discipline (§5.5).
- The performance budgets as CI gates (§13).
- The empty-state and error-state catalogs that forbid illustrations and marketing copy (§7.3, §9.3).
- The two-tone color rationing with `--accent` at ≤ 8% of any screen (DESIGN_BRIEF §2).

**Weakest decisions (must change before build):**
- The `TopBar + LeftRail` chrome is a 2014 SaaS pattern applied to a product that claims to be anti-dashboard.
- The history view is specified as a "filter bar + table + pagination" composition, which is the canonical admin console.
- The "modal route" concept is a terminological dodge that hides modal behavior behind a URL change.
- The decision spine's information hierarchy is described in prose, not in layout — two engineers will build two different products.
- The settings page exists as a top-level nav item with three sub-pages, which is the canonical SaaS settings dropdown.
- The accessibility spec is incomplete: keyboard model lacks arrow keys, skip links, focus restoration, error announcement.
- The audit footer in mono at 12pt is approximately 4.2:1 contrast, below WCAG AA — the most important content fails its own floor.
- The escalation feature ships with optimistic UI on a consequential action.

**Highest risk of AI-generated SaaS sameness:**
1. The `AppShell` (top bar + left rail + content + footer). The single biggest contributor to "this looks like every other B2B product."
2. The `HistoryTable` (filter bar + table + pagination + sparkline). A reading list pretending to be a console.
3. The settings nav with three sub-routes. The canonical SaaS settings dropdown.
4. The empty-state paragraphs and toast-for-system-events pattern. LLM-trained filler.
5. The driver list rendered as cards. The "card grid" reflex.

The architecture is not broken. It is not even weak in most places. It is **a few decisions away from world-class** and **a few decisions away from a Linear-clone that nobody remembers.** The next pass must resolve those decisions in the editorial-finance direction the brief chose.

---

## Keep

Every decision below must survive into v1 unchanged. The list is exhaustive. Any modification to these items requires a new architecture review.

### K1. The "rule of three" on first paint
Identity + verdict slot + audit footer, on every page, on every connection. Non-negotiable.

### K2. The decision spine as the architectural anchor
Every architectural path serves the decision spine. The decision spine is the product. All other screens are degraded forms of it.

### K3. The audit footer as a global element
Always rendered. Never collapsed. Never behind a tap. Never a modal. The product's promise to the borrower and the regulator.

### K4. Two-tone color rationing with single accent
`--ink`, `--paper`, `--accent: #9A5A1F`. Semantic color only on the verdict. `≤ 8%` of any screen is accent. Monochrome + accent on all charts.

### K5. No spinners, no skeletons, no carousels, no modals
Loading is typographic. Empty states are typographic. There are no carousel patterns and no modal dialogs. The architecture's forbidden-component list is correct.

### K6. Performance budgets as CI gates
Lighthouse CI enforces the budgets in §13. Regressions are build errors. This is the only way the 30-second decide-stage budget is defensible.

### K7. The closed component library with state discipline
Every component has 9 documented states. A component is not "done" until every state is designed. This prevents the "designed later" drift that kills design systems.

### K8. The type generation from OpenAPI
Generated types, not manual. A type mismatch is a build error. This is the only way the frontend stays in contract with the backend.

### K9. The decision spine's content block order
Identity → verdict → confidence → drivers → recommendations → archetype → breakdown → audit. Inherited from DESIGN_BRIEF §3. The order is correct; the architecture only fails to specify the layout.

### K10. The error envelope contract
The backend's `ErrorEnvelope` shape is the only error shape the frontend handles. Contract violations surface as a generic 500. This is correct.

### K11. The privacy stance on marketing copy
The product does not onboard. The product does not market to its own users. The product does not have a "remember me" toggle. All correct.

### K12. The keyboard model exists
Even in its incomplete form, §4.6 commits to keyboard navigation. This is the right commitment; it needs to be completed (see M3).

### K13. The loading-state time budgets
Per-operation budgets in §8.4. These are the right numbers and they are correct.

### K14. The forbidden visualization list
Pie, donut, radar, 3D, gauge, heatmap, stacked area, Sankey, animated chart, geo map. All forbidden for the stated reasons. The list is correct.

### K15. The typographic empty state stance
No illustrations, no "oops," no "looks like you're new here." The stance is correct; the implementation has paragraph-bloat (see M6).

### K16. The decision spine's primary actions
Approve, Decline, Escalate. Three buttons below the verdict. Not a modal. This is the correct decision register.

### K17. The data-sourcing discipline
Every component is wired to a typed API contract. No component is allowed to invent a value. This is the right discipline.

### K18. The optimistic-UI ban on consequential actions
§8.2 implicitly bans optimistic UI by listing "Submitting…" as a state. The escalation feature violates this (see M8). The principle is right; the application is wrong.

### K19. The deep-zoom touch target
56×56px minimum on touch. Not 44pt, not 48dp. The metric conversion is exact. The decision is correct.

### K20. The signed-out, hard-stop session expiry
"Session expired. Sign in to continue." One message, one button. No retention, no "stay signed in," no marketing footer. Correct.

---

## Modify

For each item: the problem, the evidence, the risk, the recommendation, and the implementation impact. Modifications do not require a new architecture review; they are scoped to the section cited.

### M1. The application chrome is a 2014 SaaS pattern

**Problem:** `AppShell` is `TopBar + LeftRail + Content + Footer`. This is the GitHub, Linear, Notion, Salesforce, Asana, Jira pattern. The brief establishes that RiskIntel is anti-dashboard; the chrome is a dashboard.

**Evidence:** §10.3.1, §10.3.6, §10.3.7. Desktop = top bar (56px) + left rail (240px) + content + audit footer. Tablet = top bar (56px) + hamburger drawer + content. Mobile = top bar (48px) + bottom bar (56px) + content.

**Risk:** Procurement teams and loan officers will recognize this as a "B2B product" and not as a "decision-support surface." The brief's differentiator (editorial finance, anti-dashboard) is invisible in the chrome. The product looks like every competitor.

**Recommendation:** Replace the persistent left rail with **context-anchored navigation** that orbits the decision spine, not floats beside it.
- The user enters at `/assess/new` and is in a flow. The only persistent chrome is the top bar (containing product monogram, section name, user identity, connection indicator) and the audit footer.
- Section navigation becomes a 32px collapsed micro-rail on the left, expanding to 240px on hover. This is the Linear pattern, not the Salesforce pattern.
- On the decision spine, navigation collapses to a single breadcrumb at the top: `History / Ramesh Kumar — RI-...-B-00012`. The user is in the decision. The chrome is a footnote.
- On mobile, section nav lives in the top bar's user-identity dropdown, not as a 56px bottom bar. The bottom bar is removed. The verdict owns the entire viewport.

**Implementation impact:** Section §3.13, §4.1, §4.2, §10.3.1, §10.3.6, §10.3.7. Components: `LeftRail` and `BottomBar` are deleted from §5.3. `TopBar` is rewritten. ~12 hours of design + ~24 hours of frontend work. No backend change.

### M2. The decision spine's information hierarchy is described, not specified

**Problem:** §3.5 lists eight content blocks in order. The order is correct (inherited from the brief). But the architecture does not specify the **layout grid** for the decision spine: column count, gutter width, vertical rhythm between blocks, z-axis (which block reads "above" which), the relative type sizes of secondary blocks (confidence, drivers, recommendations), or the rules for the breakdown's domain sections.

**Evidence:** §3.5 is a bulleted list. §6.2.1, §6.2.2, §6.2.3, §6.2.4 specify visualizations but not their placement within the page.

**Risk:** Two engineers, given §3.5, will build two different decision spines. The "hero screen" will not be visually consistent across implementations. The brief's hierarchy will be honored in principle and violated in execution.

**Recommendation:** Add a §3.5.1 "Decision spine layout grid" that specifies:
- 12-column desktop grid, 8-column tablet, 4-column mobile.
- Gutter: 32px desktop, 24px tablet, 16px mobile.
- Type scale assignment per block: verdict 44pt desktop / 30pt tablet / 30pt mobile; confidence 17pt; drivers 15pt with 22pt for the section heading; recommendations 15pt; archetype 14pt; breakdown 14pt with 17pt for the section heading; audit footer 14pt mono.
- Vertical rhythm: 64px between major blocks, 32px between a block and its label, 16px between a label and its content.
- Z-axis: identity and verdict are above the content blocks; the audit footer is below all content.
- Sticky elements: verdict is not sticky (the user reads it once); the metadata strip in the identity block is sticky at the top of the viewport on scroll-down.
- The breakdown's domain sections: 5 named sections (Financial Health, Risk Tier, Archetype, Recommendations, Audit Metadata) with the rules of which fields go where.

**Implementation impact:** New section §3.5.1. ~6 hours of design. ~16 hours of frontend work to convert the specification into layout primitives. No backend change.

### M3. The keyboard model is incomplete

**Problem:** §4.6 specifies Tab, Shift-Tab, Enter, Escape, Cmd-K, Cmd-Enter. It does not specify arrow-key navigation within radio groups and selects, skip links, focus restoration on modal close, focus announcement on form errors, or the keyboard model for the in-page anchors (§4.3).

**Evidence:** §4.6, §4.3.

**Risk:** Screen reader users and keyboard-only users cannot navigate the form, cannot reach the audit footer without tabbing through the entire top bar, cannot tell why focus jumped to the first invalid field. The product is AA in name only.

**Recommendation:** Add a §4.6.1 "Keyboard model — complete" specifying:
- **Arrow keys** navigate within radio groups, custom selects, and the in-page anchor list.
- **Skip links**: "Skip to main content," "Skip to audit footer," "Skip to verdict." Visible on focus, hidden otherwise.
- **Focus restoration**: when a modal route closes, focus returns to the element that opened it. Document the behavior with a state machine.
- **Focus announcement on form errors**: when a form submit fails, the first invalid field receives focus AND a live region announces "N validation errors. First: [field name], [error message]."
- **In-page anchor keyboard model**: arrow keys (or `j`/`k`) move between anchors; `Enter` scrolls to the active anchor; `Escape` clears the active anchor.
- **Cmd-K is removed** (see M5).

**Implementation impact:** §4.6 rewrite. ~4 hours of design. ~16 hours of frontend work. No backend change.

### M4. The audit footer fails its own accessibility floor

**Problem:** §10.3.5 specifies the audit footer in mono at 12pt equivalent in `--ink` at 60% alpha on `--paper`. This is approximately 4.2:1 contrast, below WCAG AA's 4.5:1 for body text. The product's most important content fails its own accessibility floor.

**Evidence:** §10.3.5, §14 (color contrast table says 4.5:1 for body).

**Risk:** The product's most defensible content — the audit trail — is unreadable to users with low vision. A regulator with reduced vision cannot read the audit footer. The architecture contradicts itself.

**Recommendation:** Change the audit footer to:
- **14pt** mono (one tick above body) instead of 12pt.
- **`--ink` at 80% alpha** instead of 60% alpha on `--paper`.
- Result: ~5.4:1, comfortably above AA, visible at arm's length.
- The 12pt-mono-footer is a 2010s SaaS look. The audit footer should be readable without effort, because the borrower and the regulator will read it under stress.

**Implementation impact:** §10.3.5, §14. ~2 hours of design. ~4 hours of frontend work. No backend change.

### M5. The Cmd-K palette is a 2022 cliché

**Problem:** §4.6 and §5.2 specify a Cmd-K command palette. Cmd-K is Linear's identity, now copied by every B2B product since 2022. The architecture specifies it for search-by-name-or-ID, which is what an address bar or a search field does.

**Evidence:** §4.6, §5.2, §10.3.8.

**Risk:** The product looks like a Linear clone. The brief's differentiator is invisible in the navigation surface.

**Recommendation:** Replace the Cmd-K palette with a **search field in the breadcrumb area, top-right**. Plain text input, two-character debounce, result list as a dropdown under the field. Keyboard shortcut: `/` to focus the field (the convention from documentation sites, not from chat apps). The palette is deleted.

**Implementation impact:** §4.6, §5.2, §10.3.8. Delete `CommandPalette` from the component inventory. ~4 hours of design. ~12 hours of frontend work. No backend change.

### M6. Empty states are paragraphs, not lines

**Problem:** The empty-state catalog (§9.2) has paragraphs like "No assessments in this date range. Adjust the filters or run a new assessment." This is two lines where one would do. The brief is anti-empty-state-marker; the architecture prescribes empty-state copy that fills the space empty states should not fill.

**Evidence:** §9.2, all 8 entries.

**Risk:** The empty state occupies visual real estate disproportionate to its information content. The product's anti-marketing stance is undermined by verbose empty states.

**Recommendation:** Each empty state is a single line, in 17pt body, set in `--ink` at 60% alpha, on `--paper`. A CTA, if needed, is a single text link below, in `--accent`. Two lines maximum.

```
No assessments in this date range.
Adjust filters ↑
```

**Implementation impact:** §9.2, all 8 entries. ~2 hours of design. ~4 hours of frontend work. No backend change.

### M7. The history view is a table with a filter bar and a sparkline

**Problem:** §3.7 specifies history as "filter bar (date range, type, verdict, applicant name) + tabular list + pagination." §6.2.5 adds a "HistoryTrend" sparkline. This is the canonical admin console. The brief says history is a chronological reading list, not a dashboard.

**Evidence:** §3.7, §5.2 (`HistoryTable`, `FilterBar`, `HistoryRow`), §6.2.5 (`HistoryTrend`).

**Risk:** The product's main browsing surface looks like every internal bank CMS. Procurement teams and analysts will not see a differentiator. Officers will revert to the CMS they already have.

**Recommendation:**
- Delete `FilterBar` and `HistoryTable` from the component inventory.
- Replace history with a **chronological reading list**: a single-column list of decisions, each row a typographic block (name, date, verdict band, one-line top driver). No table. No filter bar.
- Filtering happens via the search field in the breadcrumb area (replaces Cmd-K per M5). Real-time, two-character debounce.
- Pagination: a "Load 20 more" button at the bottom of the list. No infinite scroll. No page numbers.
- Delete `HistoryTrend` (the sparkline). It is a vestigial BI component. If the institution-wide view is needed, it is a separate admin-only page in a future version.

**Implementation impact:** §3.7, §5.2, §6.2.5. Delete 3 components, add `HistoryList` and `HistoryItem`. ~8 hours of design. ~24 hours of frontend work. No backend change.

### M8. The escalation feature ships with optimistic UI on a consequential action

**Problem:** §1.4 says escalation is "stubbed locally with optimistic UI." Optimistic UI on a consequential action — escalation triggers a downstream workflow — is dangerous. The officer clicks Escalate, the UI shows "Pending Review," the server returns 500, the escalation is lost.

**Evidence:** §1.4, §11.2 (`POST /api/escalations` is "assumed"), §17 (open question #4).

**Risk:** The officer thinks they escalated; the audit log says they did not. The action has audit consequences; the UI hides the consequences; the institution's compliance posture is exposed.

**Recommendation:** No optimistic UI on consequential actions. The escalation panel:
- Shows a "Submitting…" state (typographic, in the submit button) until the server confirms.
- The audit log entry is rendered after the server confirms.
- If the server errors, the panel shows the error inline, the action is not "completed," and the officer can retry.
- The architecture must commit to this: optimistic UI is forbidden for any action that produces an audit log entry.

**Implementation impact:** §1.4, §11.2. ~2 hours of design. ~4 hours of frontend work. No backend change (escalation backend is already out of scope for v1 — see R2).

### M9. The drivers and recommendations lists overlap

**Problem:** §3.5 lists "Top drivers" and "Recommendations" as two separate content blocks. The driver list tells the officer **why** the verdict is what it is. The recommendations tell the officer **what to do.** In practice, an officer skims the decision and reads one of them. The other is dead weight.

**Evidence:** §3.5, blocks 4 and 5; §5.2 (`DriverList`, no separate `RecommendationsList` — currently mixed).

**Risk:** Two lists with overlapping content. Officer reads one, ignores the other. The page is denser than it needs to be.

**Recommendation:** Merge drivers and recommendations. Each driver IS a recommendation.
- "Income imputed as ₹4,200/mo from monthly expenses" (a driver) becomes "Verify income before final decision" (a recommendation).
- The merged list is **the action list** — what the officer does next, grounded in the model output.
- The full breakdown (separate section) explains the mechanism. The drivers explain the action. One list, not two.

**Implementation impact:** §3.5, §5.2. ~3 hours of design. ~6 hours of frontend work. No backend change.

### M10. The intake type selector uses two cards

**Problem:** §3.2 specifies `/assess/new` as "two cards. Card A: name, key fields preview. Card B: name, key fields preview. No images on the cards — typographic only." A typographic card is still a card. Two cards side by side is a card pattern.

**Evidence:** §3.2.

**Risk:** The first screen the officer sees is a card grid, which is the canonical SaaS pattern. The product's differentiator is invisible from the first interaction.

**Recommendation:** Replace the two cards with a single row of two typographic text links, in display 30pt, separated by a hairline. Below each, a one-line description in 15pt body. No card. No rectangle. No border.

```
Person A — documented borrower        Person B — new-to-credit borrower
Salaried or self-employed, with       Micro-enterprise, partial documentation,
full credit history.                  thin file.
Start →                                Start →
```

**Implementation impact:** §3.2, §5.3 (delete `IntakeTypeSelector` organism, add a typographic nav component). ~2 hours of design. ~4 hours of frontend work. No backend change.

### M11. The mobile bottom bar steals the verdict's space

**Problem:** §10.3.7 specifies a 56px bottom bar on mobile. On a 375px-wide phone with a 30pt verdict, 56px bottom bar, 48px top bar, and ~40px safe areas, the actual content area is ~190px tall. The verdict is visible, but the decision spine's body is not.

**Evidence:** §10.3.7, §10.3.1, §10.3.2.

**Risk:** The decision spine is the product. On mobile, the product is unreadable. The architecture's "mobile is read-mostly" stance is undermined by a chrome that takes more space than the content.

**Recommendation:**
- The bottom bar is removed. Section nav on mobile lives in the top bar's user-identity dropdown. Three taps max to any destination.
- On the decision spine specifically, the top bar auto-hides on scroll-down and re-appears on scroll-up. The verdict owns the screen when the user is reading.
- The mobile verdict type is increased to 30pt (matches current) and the content area below the verdict gets a 64px top padding (visual breathing room) instead of a 56px chrome bar.

**Implementation impact:** §10.3.1, §10.3.6, §10.3.7, §10.3.2. ~6 hours of design. ~16 hours of frontend work. No backend change.

### M12. The "Available on desktop" pattern is condescending

**Problem:** §10.6 says some features show "Available on desktop" on mobile. This is the LLM-recommended pattern for shipping a desktop-only feature. It tells the user to go away.

**Evidence:** §10.6.

**Risk:** The user in the field, on a phone, is told the product does not work for them. The product loses the field officer as a user.

**Recommendation:** Remove the "Available on desktop" pattern. For each feature in §10.6, the architecture commits to one of:
- **Build the mobile version.** The mobile version may be read-only, may have less functionality, but it must not be a "go away" message.
- **Don't ship the feature at all in v1** if the mobile version cannot be built (see R2 and R3).

**Implementation impact:** §10.6, removal. ~2 hours of design. ~4 hours of frontend work. No backend change.

### M13. The confidence range belongs in the breakdown, not the hero

**Problem:** §3.5 block 3 puts the confidence frame (band, probability range, override flags) in the hero area, directly below the verdict. The officer reads the band, not the number. The probability range is audit-grade information that belongs in the breakdown.

**Evidence:** §3.5.

**Risk:** The hero area competes with itself. The verdict says "Moderately Ready." The confidence frame says "68%, range 61–74%." The officer's eye jumps between them. The verdict is no longer the largest type on the page in cognitive terms.

**Recommendation:** The confidence frame moves below the breakdown, in a dedicated section. The hero area shows:
1. Applicant identity
2. **Verdict** (largest type)
3. **Override flags as a tag row** (if any) — the only thing from the confidence frame in the hero
4. Drivers + recommendations (merged, per M9)

The full confidence frame (band, probability range) is rendered in a "Decision metadata" section below the breakdown, in a typographic row in mono.

**Implementation impact:** §3.5, §5.2. ~3 hours of design. ~6 hours of frontend work. No backend change.

### M14. The applicant identity is missing a metadata strip

**Problem:** §3.5 places the audit footer at the page bottom. On a long decision spine, the bottom is below the fold. The officer has to scroll to verify the model version. The audit footer's value is that the officer can copy the correlation ID in 2 seconds. If it is below the fold, it takes 6.

**Evidence:** §3.5, §10.3.5.

**Risk:** The audit footer is below the fold on the most important screen of the product. The product's defensibility surface is the last thing the officer sees.

**Recommendation:** Add a **metadata strip** in the applicant identity block at the top of the decision spine:
- A typographic row in mono, 14pt (per M4), in `--ink` at 80% alpha on `--paper`.
- Content: timestamp, model version, decision version, schema version, correlation ID. Truncated where needed; full version on hover. The correlation ID is copyable on hover via a copy button.
- The full audit footer remains at the page bottom, with extended lineage.
- The metadata strip is also rendered in privacy mode (per M15) with the correlation ID preserved.

**Implementation impact:** §3.5, §5.2. ~3 hours of design. ~6 hours of frontend work. No backend change.

### M15. The applicant identity exposes PII in public contexts

**Problem:** §3.5 places the applicant's name, age, business, and loan request in the page header on every page. Any screen the officer views in a public space (a branch, a meeting, a regulator's office) exposes the borrower's data. The architecture does not specify a privacy mode.

**Evidence:** §3.5, §3.13 (global elements — applicant identity is not in the list, but is on every page).

**Risk:** The product exposes borrower PII by default. An officer reviewing a decision in a regulator's office has no way to redact the borrower's identity without closing the tab.

**Recommendation:** Add a privacy mode:
- A toggle in the top bar (a single icon, "Show full" / "Hide details").
- In privacy mode, the applicant identity is replaced with a typographic monogram ("R.K."), the age with a band ("35–45"), the business with a category ("Services"), the loan request with a band ("₹50,000–₹100,000").
- The audit footer retains the full correlation ID (the officer can defend the decision with it; the borrower's identity is not required for defense).
- Privacy mode is the officer's choice. It is not auto-triggered by location.

**Implementation impact:** New section in §3.13. ~4 hours of design. ~12 hours of frontend work. No backend change.

### M16. The history scope is not specified

**Problem:** §1.3 and §3.7 do not specify whether history is personal, team-wide, or institution-wide. Each scope has different trust implications. The regulator's question becomes: "why does a junior officer see the chief credit officer's decisions?"

**Evidence:** §1.3, §3.7, §11.2.

**Risk:** The default scope is undefined. The implementation will pick one. If it picks the wrong one, the institution's internal hierarchy is violated.

**Recommendation:** History is **team-wide** by default. A `Cmd-Shift-I` keyboard shortcut toggles to institution-wide (with a confirmation modal — this is a permission elevation, not a UI state).

**Implementation impact:** §1.3, §3.7. ~2 hours of design. ~8 hours of frontend work (the toggle is a permission-gated UI affordance). No backend change.

### M17. The horizontal-scroll table is hostile on mobile

**Problem:** §10.3.4 specifies horizontal-scroll tables for the full breakdown on mobile, with a sticky first column. On a 375px phone, the user scrolls sideways to read numbers.

**Evidence:** §10.3.4.

**Risk:** The full breakdown is unreadable on mobile. The officer cannot defend a decision from their phone.

**Recommendation:** On mobile, the full breakdown is rendered as a stacked list, not a table. Each input is a row: field name (left, 50%), value (right, mono, right-aligned), contribution (below in 12pt). The user scrolls vertically through inputs, not horizontally through columns. The table is a desktop affordance.

**Implementation impact:** §10.3.4. ~4 hours of design. ~12 hours of frontend work. No backend change.

### M18. The forbidden color signals on the contribution chart

**Problem:** §6.2.1 uses `--accent` and `--negative` (oxblood) to distinguish the largest positive and largest negative drivers. This is a color-only signal for non-colorblind users. For deuteranopic and protanopic users, the chart shows two values distinguished only by color.

**Evidence:** §6.2.1.

**Risk:** Color-blind users cannot read the largest positive vs. largest negative distinction in the contribution chart.

**Recommendation:** The distinction is made by **three redundant signals**: position in the ranked list (top vs. bottom), sign indicator in mono (`+` and `−` prefixes, not minus-glyph), and color (accent vs. oxblood) as a redundant signal. None of the three alone is the primary signal; all three together.

**Implementation impact:** §6.2.1. ~2 hours of design. ~4 hours of frontend work. No backend change.

### M19. The driver list is rendered as cards

**Problem:** §5.2 specifies `DriverItem` as a discrete component, rendered in `DriverList`. The brutal review and the brief both note that this becomes a card grid in practice. Three drivers in a row, each in its own visual container, is a card grid.

**Evidence:** §5.2, §6.2.1.

**Risk:** The driver list, the most-read content on the page, looks like a card grid. The product's anti-card-soup stance is violated in its most-read content.

**Recommendation:** Drivers are a typographic list with hairlines between items, no backgrounds, no borders around individual items. Each driver is a row: name (left, 50%), value (right, mono, right-aligned), and a contribution bar (full width, below the row). The list is a list, not a grid.

**Implementation impact:** §5.2, §6.2.1. ~3 hours of design. ~6 hours of frontend work. No backend change.

### M20. The settings page is a top-level nav item

**Problem:** §3.9–3.11 and §4.1 put settings as a top-level nav item with three sub-routes. This is the canonical SaaS settings dropdown.

**Evidence:** §3.9, §3.10, §3.11, §4.1.

**Risk:** The product's chrome has a settings dropdown, which is the canonical SaaS chrome.

**Recommendation:** Settings is reachable from the user-identity dropdown in the top bar. Profile and Defaults are sections on a single page. Batch (if shipped, see R3) is a separate top-level nav item, not a sub-page of Settings. The "Settings" top-level nav item is removed.

**Implementation impact:** §3.9–3.11, §4.1. ~4 hours of design. ~8 hours of frontend work. No backend change.

### M21. The polling interval for batch is hedged

**Problem:** §1.6 says batch polling happens "every 2 seconds (or longer on slow connections, per §6)." This is a hedge, not a number.

**Evidence:** §1.6.

**Risk:** Implementation variance. Some clients poll every 2s, some every 10s, some adaptive. The product's behavior is undefined.

**Recommendation:** 5 seconds is the polling interval. State the reason: below 5s, polling traffic becomes meaningful on 2G/3G; above 10s, the user perceives the job as stalled. 5s is a defensible engineering choice. Document it; don't hedge.

**Implementation impact:** §1.6. ~1 hour of design. ~2 hours of frontend work. No backend change.

### M22. The architecture's open questions leak into v1

**Problem:** §17 lists six open questions. The architecture's instruction ("the architecture is built to be patient about these questions") is correct in principle, but several questions are blocking v1 (especially #3: deletion policy, and #4: escalation is a stub).

**Evidence:** §17.

**Risk:** v1 ships with stubbed features and undefined policies.

**Recommendation:** Resolve questions #3 and #4 before v1 ships. #3 commits to: "v1 does not support assessment deletion. The audit log is append-only." #4 commits to: "v1 does not ship the escalation feature. See R2." Other questions can remain open with their stated degraded states.

**Implementation impact:** §17. ~2 hours of design. No frontend work. No backend change.

---

## Remove From V1

Each feature below has a stated user value and implementation cost. The recommendation is deferral, not deletion. The features may return in v2 if user evidence supports them.

### R1. Compare Two Assessments (`/history/compare`)

**User value:** Speculative. Allows senior analysts to see two decisions side by side. No user research is cited for this feature. It is exactly the kind of "might be useful" feature that bloats a v1.

**Implementation cost:**
- New route (§2.1) and screen (§3.8).
- New organism `ComparisonView` (§5.3).
- Mobile adaptation (read-only on mobile per §10.6, which is the "tell the user no" pattern per M12).
- Estimated effort: ~40 hours of design + ~120 hours of frontend work.

**Recommendation:** **Defer to v2.** The feature has no proven user. The brutal review and §17 both flag it as speculative. v1 history is a reading list (per M7); comparison can be added as a power-user feature in v2 if user evidence emerges.

**Implementation impact:** Delete §1.5, §3.8, `ComparisonView` from §5.3. Modify §17 to remove question #1.

### R2. Escalation Feature (`/assess/{id}/escalate`)

**User value:** Real but secondary. Officers do escalate. The frozen backend does not support it (§11.2, §17 question #4). v1 ships it as a stub with optimistic UI, which is dangerous per M8.

**Implementation cost:**
- New route (§2.3) and screen.
- New molecule `EscalationPanel` (§5.2).
- New organism (or extension of `ModalRouteShell`).
- Backend endpoint not in v1 backend; requires backend work too.
- Estimated effort: ~24 hours of design + ~80 hours of frontend work + ~80 hours of backend work.

**Recommendation:** **Defer to v2.** v1 does not ship escalation. The Approve/Decline buttons are the action surface. If the institution needs escalation, it uses an out-of-band channel (email, ticket) until v2.

**Implementation impact:** Delete §1.4, §3.6 (escalation is removed; report stays), `EscalationPanel` from §5.2, `/assess/{id}/escalate` from §2.3. Modify §11.2 (remove `POST /api/escalations`). Modify §17 (resolve question #4 as "deferred to v2").

### R3. Batch CSV Upload (`/settings/batch`)

**User value:** Real and load-bearing for the MFI segment. MFI managers do need to assess in batches. The brutal review and the architecture both acknowledge this is the right power-user feature for MFI.

**Implementation cost:**
- New route and screen (§3.11).
- New organism `BatchUploader` (§5.3).
- Two new backend endpoints (`POST /api/assessments/batch`, `GET /api/assessments/batch/{job_id}`).
- CSV parser, validation, error states.
- Estimated effort: ~32 hours of design + ~120 hours of frontend work + ~120 hours of backend work.

**Recommendation:** **Defer to v2** for the v1 frontend build, because the backend endpoints are not in the frozen backend and the frontend's v1 cannot ship against stubs. The architecture should explicitly defer this and not ship a half-built batch uploader.

**Implementation impact:** Delete §1.6, §3.11, `BatchUploader` from §5.3. Modify §11.2 (remove batch endpoints). Modify §10.6 (remove "Batch CSV upload" from the desktop-only list, since it is not in v1 at all). Modify §17 (resolve question #5 as "v2 feature; v1 has no batch uploader").

### R4. Settings → Model Version Override

**User value:** Speculative. "Default users do not need it" (§3.10). This is a power-user feature for institutional admins, who are not v1's primary user.

**Implementation cost:** Small. ~4 hours of design + ~8 hours of frontend work.

**Recommendation:** **Defer to v2.** Remove the disclosure in §3.10. The defaults page shows only the user-type selector and the language selector. Model version override is an institutional-admin concern, not a v1 user concern.

**Implementation impact:** Modify §3.10. ~1 hour of design. ~2 hours of frontend work. No backend change.

### R5. Toast component (system events)

**User value:** Speculative. §5.2 describes the Toast as "for system events (assessment saved, sign-out confirmed)," but neither event uses a toast in the architecture. Draft saves are silent on blur (§1.1). Sign-out is a redirect (§1.7).

**Implementation cost:** Small, but the cost of unused components is design-system rot.

**Recommendation:** **Remove from v1.** If a use case appears, add Toast back. Don't ship a component "in case."

**Implementation impact:** Delete `Toast` from §5.1 and §5.2. Modify §5.4 (remove "Toast with marketing copy" since Toast is removed entirely). No frontend work; this is a documentation change.

### R6. HistoryTrend sparkline (§6.2.5)

**User value:** Speculative. It is a "summary widget" that provides no actionable information to the officer. The brutal review flags it as "vestigial BI."

**Implementation cost:** Small, but the visual cost is real: it makes the history page look like a dashboard.

**Recommendation:** **Remove from v1.** Per M7, history is a reading list. If institution-wide trends are needed, they are a separate admin-only page in v2.

**Implementation impact:** Delete §6.2.5. No frontend work; the visualization is not built yet.

### R7. "Available on desktop" mobile pattern

**User value:** None. It is a pattern, not a feature.

**Implementation cost:** None, but it is a trust-damage pattern (per M12).

**Recommendation:** **Remove from v1.** For each feature in §10.6, the architecture commits to either "build the mobile version" or "defer the feature." No "tell the user no" messages.

**Implementation impact:** Delete §10.6. With R1–R4 deferred, the list of "what is not adapted" becomes empty.

### R8. `/` index route (redirect-only)

**User value:** None. The architecture says the index "redirects to `/assess/new` or `/history` based on role and last activity." This is a "where am I" moment that the product is supposed to eliminate (per M22 of the brutal review).

**Implementation cost:** Small, but the route is conceptually wrong.

**Recommendation:** **Change v1 behavior:** `/` is the home, and the home is `/assess/new` — the type selector. The product begins at the first action. There is no "dashboard home." The user is always one click from the next decision.

**Implementation impact:** Modify §2.1. `/` becomes `/assess/new` (or a redirect to it). No frontend work; this is a routing change.

### R9. Sticky-anchor right rail on the decision spine (§4.3)

**User value:** Speculative. The decision spine is one page. Anchors are useful on long pages. The decision spine, with the M2 layout specification, is approximately 3-4 viewport heights on desktop. Anchors may help.

**Implementation cost:** Small, but it adds chrome to the screen.

**Recommendation:** **Defer to v2.** The decision spine in v1 is scrolled linearly. The in-page anchor list can be added in v2 if user evidence supports it. The keyboard model still allows `j`/`k` navigation between major blocks.

**Implementation impact:** Delete §4.3 (the in-page anchor list as a UI affordance; keep the keyboard navigation if M3 specifies it). ~2 hours of design. ~6 hours of frontend work (subtracted, since the affordance is not built).

### R10. Settings page (entire top-level nav item)

**User value:** Real, but the page is small. Per M20, settings becomes a single reachable page from the user-identity dropdown, not a top-level nav item.

**Implementation cost:** Saves work.

**Recommendation:** **Remove from top-level nav.** Per M20, the nav item is deleted. Profile, Defaults, and (if shipped) Batch are reachable from elsewhere.

**Implementation impact:** Per M20.

### R11. `/legal/audit` route

**User value:** Real but not v1. The product is not public-facing in v1. The audit policy belongs on the institution's own compliance site, not in the product.

**Implementation cost:** Small, but adds a route.

**Recommendation:** **Defer to v2** or remove. The other `/legal/*` routes can stay (they are linked from the sign-in page footer).

**Implementation impact:** Delete `/legal/audit` from §2.2. ~30 minutes of design. No frontend work (not built).

### R12. `/status` route

**User value:** Real but not v1. The product is internal; a `/status` page is for public-facing services. The connection indicator (§3.13) is the officer's status surface.

**Implementation cost:** Small.

**Recommendation:** **Defer to v2.** v1 surfaces status via the `ConnectionIndicator` only.

**Implementation impact:** Delete `/status` from §2.2 and §11.2. ~30 minutes of design. No frontend work (not built).

### R13. Voice input on mobile (deferred reactivation)

The brutal review's §6.4 asks to enable voice input for free-text fields. The architecture forbids it.

**Recommendation:** **Defer to v2.** The dignity principle's review step is correct, but voice input is a power-user feature for the field officer, not a v1 requirement. v1 is monospace and text-only.

**Implementation impact:** §10.4 unchanged. No frontend work in v1.

---

## Missing Specifications

The following are areas where an engineer could build different UIs from the same document. Each is a hole in the architecture. Each must be filled before the build.

### MS1. Decision spine layout grid
**Status:** Not specified. (See M2.) Two engineers will build two different spines.

### MS2. Spacing scale
**Status:** Mentioned in brief (8px baseline) but not operationalized in the architecture. There is no specification of the spacing tokens (`--space-1` through `--space-8`), the margin conventions, or the rules for when to use which.

**Required:** A spacing scale: 4, 8, 16, 24, 32, 48, 64, 96, 128. Token names. Usage rules (e.g., "vertical rhythm between major blocks is always 64px on desktop, 48px on tablet, 32px on mobile").

### MS3. Container widths and gutters
**Status:** Not specified. The 12-column desktop grid is implied by the brief's "8px baseline" but not stated. There is no max-width on the content area, no gutter width, no outer margin.

**Required:** A container spec: max-width 1200px desktop, full-width with 32px outer padding tablet, 16px outer padding mobile. Gutter 32px desktop, 24px tablet, 16px mobile. The audit footer is full-width, breaking out of the container if needed.

### MS4. Z-axis specification
**Status:** Not specified. The architecture says the audit footer is "page-bottom," but does not specify stacking. Sticky elements are mentioned (the M14 metadata strip, the M11 top bar auto-hide) but their z-indexes are not.

**Required:** A z-index scale: base (0), sticky-top-bar (10), sticky-metadata-strip (20), modal-overlay (100), modal-content (110), connection-indicator-toast (200). No element may use a z-index outside this scale.

### MS5. Focus ring specification
**Status:** Mentioned (§4.6: "2px hairlines in `--accent`") but not fully specified. There is no spec for focus ring offset, focus ring color on dark backgrounds, focus ring on the verdict (which is `--accent` itself), focus ring contrast against the audit footer.

**Required:** A focus ring spec: 2px solid `--accent`, 2px offset, always visible. On `--accent` backgrounds (the verdict), the focus ring is `--ink` instead. Contrast ≥ 3:1 against any background.

### MS6. Form field visual states
**Status:** Partial. The architecture says inline validation (§1.1, §7.2) but does not specify the visual treatment of: default, focused, filled, valid, invalid, disabled, readonly. The "first invalid field receives focus" rule (M3) needs a consistent visual state across the form.

**Required:** A form field state spec, per state in the component library's 9-state discipline (§5.5).

### MS7. Link visual treatment
**Status:** Partial. §5.1 says "Default, Subtle (in lists). Always underlined." But it does not specify the hover state, the visited state, the active state, or the focus state of a link. Visited links (purple default) would violate the design system.

**Required:** A link state spec: default (`--ink`, underlined, 1px), hover (`--accent`, underlined, 1px), active (`--accent`, underlined, 2px), focus (`--accent` focus ring, 2px), visited (same as default — no purple, ever).

### MS8. Tag visual treatment
**Status:** Partial. §5.1 says "Default, Positive, Negative, Accent. Never filled. Always outlined." But it does not specify the border thickness, the corner treatment (sharp vs. rounded), the padding, or the rules for multiple tags in a row.

**Required:** A tag spec: outlined, 1px border, 0 corner radius (sharp), 4px vertical padding × 8px horizontal padding, mono text 12pt equivalent, single-line. Tags wrap on whitespace; no truncation.

### MS9. Rule visual treatment
**Status:** Partial. §5.1 says "Default (12% alpha), strong (24% alpha), accent (in `--accent`)." But it does not specify the thickness (the architecture implies 1px but does not state it), the rules for when to use which, or the rule's behavior on the audit footer.

**Required:** A rule spec: 1px (default), 2px (strong, used for active nav indicator), accent (used only for the verdict underline or the active state). Vertical rules: same scale, 1px. Rules do not animate.

### MS10. Typography hierarchy
**Status:** Partial. The architecture lists the type scale (14, 15, 17, 22, 30, 44) but does not specify the weight of each, the line-height of each, the letter-spacing of each, or the rules for choosing between them. An engineer can pick a weight that the brief forbids.

**Required:** A type spec: 44pt/52pt line-height, weight 500, letter-spacing -0.5px (display); 30pt/40pt, weight 500, letter-spacing -0.25px (heading); 22pt/32pt, weight 500 (subheading); 17pt/26pt, weight 400 (body-large); 15pt/24pt, weight 400 (body); 14pt/22pt, weight 400 (body-small); 14pt mono/22pt (data); 12pt mono/18pt (data-small). All text sets with `text-rendering: optimizeLegibility` and `font-feature-settings: 'kern', 'liga', 'tnum'` where tabular.

### MS11. Motion hierarchy
**Status:** Partial. The brief establishes motion principles (160ms ease-out entrance, 120ms ease-in exit) but the architecture does not specify the motion for: state changes (button hover, link hover), page transitions, modal route entry/exit, error state appearance, loading counter appearance.

**Required:** A motion spec: 160ms ease-out (entrance), 120ms ease-in (exit), 240ms ease-out (modal route entry), 320ms ease-in (modal route exit, 60% black backdrop fade). No bounce. No spring. No parallax. `prefers-reduced-motion` disables all transitions; state changes become instant.

### MS12. Loading hierarchy
**Status:** Partial. §8 lists the loading states per scenario, but does not specify the **loading order** for the decision spine. What renders first, second, third? The brief's "rule of three" (M2) is the start, but the architecture does not continue the sequence.

**Required:** A loading order for the decision spine:
1. First paint (rule of three): identity, verdict slot (`—`), audit footer.
2. Identity resolves (timestamps, model version).
3. Verdict slot fills.
4. Drivers render.
5. Breakdown sections lazy-load on scroll or on demand.
6. Recommendations render with the drivers.

### MS13. Error hierarchy
**Status:** Partial. §7 lists 16 error states, but does not specify the **error priority** when multiple errors occur. A form with 3 validation errors and a network error: which renders first?

**Required:** An error priority: form validation errors first (inline, with the first field focused), then form submit error (top of form), then page-level errors (replace content). Network errors are surfaced via the `ConnectionIndicator` and never replace content. Server errors (5xx) replace content with the 500 page.

### MS14. Empty state hierarchy
**Status:** Partial. §9 lists 8 empty states, but does not specify the rule for what happens when an empty state is the result of a network failure vs. a real "no data" condition. A history list with no results from a server timeout is not the same as a history list with no assessments.

**Required:** An empty state priority: real empty (no data) renders the typographic empty state. Network-empty (could not load) renders the connection indicator + a "Retry" link. The two states are visually distinct.

### MS15. Responsive rules
**Status:** Partial. The architecture lists breakpoints (§10.2) and per-component adaptations (§10.3), but does not specify the rules for: when to switch from two-column to one-column, when to hide non-essential content, when to collapse the audit footer to a metadata strip only.

**Required:** Responsive rules:
- Two-column to one-column: at 1024px viewport (the tablet-to-desktop boundary).
- Hide non-essential content on mobile: archetype, audit footer extended lineage (keep correlation ID).
- Audit footer collapse: at 768px viewport, the footer becomes a one-line metadata strip with a "Show details" link.

### MS16. Accessibility tree
**Status:** Partial. M3 specifies the keyboard model. §14 specifies the standards. But there is no specification of the **accessibility tree** for the decision spine: which elements are H1, H2, H3, which are landmarks, which are live regions.

**Required:** An accessibility tree for the decision spine:
- `<header>`: applicant identity.
- `<h1>`: the verdict.
- `<h2>`: drivers, recommendations, breakdown sections, audit metadata.
- `<main>`: the decision spine content.
- `<footer>`: the audit footer.
- `aria-live="polite"`: connection indicator.
- `aria-live="assertive"`: form validation errors on submit.

### MS17. Dark mode
**Status:** Not specified. The brief establishes a two-tone palette on `--paper`. The architecture does not commit to light-only or specify a dark variant.

**Required:** Commit to light-only for v1. The product is used in branches and offices with controlled lighting. Dark mode is a v2 concern. State this explicitly.

### MS18. Print styles
**Status:** Not specified. The product generates PDFs via `/api/report/generate`. The user may want to print a decision spine directly from the browser. The architecture does not specify print styles.

**Required:** A print style spec: the audit footer is preserved; the verdict is preserved; the top bar and left rail are hidden; the page is set to A4; the metadata strip replaces the audit footer at the page header (so it appears on every printed page).

### MS19. RTL and bidi
**Status:** Deferred to v2 (§15). But the architecture does not specify the **directional-neutrality** of the design system. A design system that hardcodes LTR will not be RTL-ready later.

**Required:** All layout tokens are direction-neutral (use `margin-inline-start` instead of `margin-left`). Type direction follows `dir` attribute. No LTR-only icons. Commit to this in the design system; do not ship LTR-only CSS.

### MS20. Form draft lifecycle
**Status:** Partial. §1.1 says drafts save on blur. §8.2 (in M6 of brutal review, not yet in architecture) says drafts are cleared on sign-out. But there is no specification of: when drafts are purged, what happens when a draft is older than 24 hours, what happens if the user signs in on a different device, what happens if the form schema changes between draft creation and draft restoration.

**Required:** A draft lifecycle spec:
- Drafts are saved to `localStorage` on form blur, keyed by form type and user ID.
- Drafts are cleared on successful submit, on sign-out, and after 24 hours.
- Drafts are not synced across devices.
- If the form schema changes (e.g., a new required field is added), drafts are marked stale and the user is told "Form has changed since you last edited. Start fresh or restore with missing fields highlighted."

---

## V1 Scope Lock

Every route and screen classified as **Required**, **Deferred**, or **Future**. The list is exhaustive. Any addition requires a new architecture review.

### Routes

| Route | Status | Notes |
|---|---|---|
| `/` | **Removed** | Per R8. The product begins at `/assess/new`. |
| `/auth/sign-in` | **Required** | |
| `/auth/forgot` | **Required** | Email field only. |
| `/auth/locked` | **Required** | |
| `/assess/new` | **Required** | The home page. Per R8, M10. |
| `/assess/person-a` | **Required** | |
| `/assess/person-b` | **Required** | |
| `/assess/{id}` | **Required** | The decision spine. |
| `/assess/{id}/report` | **Required** | Separate page, not a modal. Per M-updates. |
| `/history` | **Required** | Reading list, not a table. Per M7. |
| `/history/{id}` | **Required** | Decision spine from history. |
| `/history/compare` | **Deferred** | Per R1. |
| `/settings` | **Required (but reorganized)** | Reachable from user-identity dropdown. Per M20, R10. |
| `/settings/profile` | **Required** | |
| `/settings/defaults` | **Required (reduced)** | Model version override removed. Per R4. |
| `/settings/batch` | **Deferred** | Per R3. |
| `/legal/terms` | **Required** | |
| `/legal/privacy` | **Required** | |
| `/legal/audit` | **Deferred** | Per R11. |
| `/status` | **Deferred** | Per R12. |
| `/404` | **Required** | |
| `/500` | **Required** | |

### Screens

| Screen | Status | Notes |
|---|---|---|
| Sign-in | **Required** | |
| Assessment Intake — Type Selector | **Required (redesigned)** | Two text links, not two cards. Per M10. |
| Person A Intake Form | **Required** | |
| Person B Intake Form | **Required** | |
| Decision Spine | **Required (heavily specified)** | Add layout grid per M2, MS1. |
| Report Generation | **Required (re-typed)** | Separate page, not a modal. |
| History — List | **Required (re-typed)** | Reading list, not a table. Per M7. |
| History — Compare | **Deferred** | Per R1. |
| Settings — Profile | **Required (re-nav)** | Reachable from user-identity dropdown. Per M20. |
| Settings — Defaults | **Required (reduced)** | Model version override removed. Per R4. |
| Settings — Batch | **Deferred** | Per R3. |
| Error pages (404, 500, session expired) | **Required** | |
| Escalation panel | **Deferred** | Per R2. |
| Batch uploader | **Deferred** | Per R3. |
| Comparison view | **Deferred** | Per R1. |

### Components

| Component | Status | Notes |
|---|---|---|
| All atoms in §5.1 except `Spinner` and `Toast` | **Required** | `Spinner` is forbidden; `Toast` is removed (R5). |
| All molecules in §5.2 except `FilterBar`, `HistoryRow`, `CommandPalette`, `EscalationPanel`, `Toast` | **Required (modified)** | `FilterBar` and `HistoryRow` are replaced by `HistoryList`/`HistoryItem` (M7). `CommandPalette` is replaced by a search field (M5). `EscalationPanel` is deferred (R2). `Toast` is removed (R5). |
| `DriverList` and `DriverItem` | **Required (modified)** | Drivers merged with recommendations (M9). Rendered as a list, not cards (M19). |
| `ApplicantIdentity` | **Required (extended)** | Add metadata strip per M14. Add privacy mode per M15. |
| All organisms in §5.3 except `LeftRail`, `BottomBar`, `ComparisonView`, `BatchUploader`, `SettingsPage` | **Required (modified)** | `LeftRail` and `BottomBar` are deleted (M1). `ComparisonView` is deferred (R1). `BatchUploader` is deferred (R3). `SettingsPage` is replaced by a single page (M20). |
| `AppShell` | **Required (rewritten)** | Per M1. |
| `TopBar` | **Required (rewritten)** | Per M1. |
| `DecisionSpine` | **Required (heavily specified)** | Add layout grid (M2), confidence frame moved (M13), metadata strip added (M14), privacy mode (M15), merged drivers/recommendations (M9), screen-reader contract (MS16). |
| `HistoryTable` | **Removed** | Per M7. |
| `HistoryList` and `HistoryItem` | **Required (new)** | Per M7. |

### Features

| Feature | Status |
|---|---|
| Approve / Decline actions on decision spine | **Required** |
| Generate report PDF | **Required** |
| Download report PDF | **Required** |
| View history (reading list) | **Required** |
| Search history (by name, ID) | **Required** (search field, not Cmd-K) |
| Filter history (by date, type, verdict) | **Required (via search, not filter bar)** |
| Privacy mode | **Required** (M15) |
| History scope toggle (team ↔ institution) | **Required** (M16) |
| Escalation | **Deferred** (R2) |
| Batch CSV upload | **Deferred** (R3) |
| Compare two assessments | **Deferred** (R1) |
| Model version override | **Deferred** (R4) |
| Settings as a top-level nav | **Removed** (M20, R10) |
| Toast notifications | **Removed** (R5) |
| Cmd-K command palette | **Removed** (M5) |
| Modal routes | **Removed (replaced with separate pages)** |
| Skeleton screens | **Forbidden** |
| Spinners | **Forbidden** |
| Dark mode | **Deferred (v2)** |
| Voice input | **Deferred (v2)** |
| Print styles | **Required (with spec)** (MS18) |
| RTL support | **Deferred (v2)** (MS19) |

### Open Questions Resolved for V1

| # | Question | Resolution |
|---|---|---|
| 1 | Compare view roles | **Deferred to v2** (R1) |
| 2 | Model version override users | **Deferred to v2** (R4) |
| 3 | Assessment deletion policy | **v1 has no deletion. Audit log is append-only.** |
| 4 | Escalation workflow | **Deferred to v2** (R2) |
| 5 | Batch file formats | **Deferred to v2** (R3) |
| 6 | Institution-level model version pinning | **Deferred to v2** |

---

## Final Recommendation

**Revise the architecture once, then build.**

The architecture is not unbuildable. It is not even weak in most places. It is **a few decisions away from world-class** and **a few decisions away from a Linear-clone that nobody remembers.** The 22 modifications and 13 removals in this critique are scoped, not open-ended. Each is a concrete change to a specific section, with a specific implementation impact, in hours not weeks.

**Do not redesign.** The document is structurally sound. The doctrine is right. The execution needs tightening, not replacement.

**Do not build yet.** The architecture has 22 modifications that must be applied before the build, plus 20 missing specifications (MS1–MS20) that must be filled. Building now means reworking the decision spine, the chrome, the history view, the empty states, and the accessibility contract after the first sprint. That is more expensive than fixing the document.

**Sequence:**

1. Apply the 22 modifications (M1–M22). Estimated effort: ~120 hours of design + ~280 hours of frontend work, no backend work.
2. Fill the 20 missing specifications (MS1–MS20). Estimated effort: ~80 hours of design + ~120 hours of frontend work, no backend work.
3. Apply the 13 removals (R1–R13). Estimated effort: ~16 hours of design + ~40 hours of frontend work (subtracted, since the deferred features are not built).
4. Re-baseline the architecture as v1.1. Run the architecture sign-off process. Lock the v1 scope per this document.
5. Build.

Total pre-build effort: ~216 hours of design + ~440 hours of frontend work, no backend work. The v1.1 architecture will be approximately 30% shorter than v1.0 (the deferred features and the LLM-trained filler are removed) and approximately 3x more specific (the 20 missing specifications are filled).

**The brutal review was right.** The architecture is structurally sound but LLM-trained in its details. The next pass must be human-edited. Once it is, the product is world-class.

**Build signal:** Build when v1.1 is signed off and the v1 scope is locked per this document. Not before.

**Risk if built now:** The product ships looking like a B2B SaaS. The differentiator (editorial-finance, anti-dashboard) is invisible in the chrome. The procurement team evaluates it as "another internal tool." The 90-second decide-stage budget is violated by chrome that takes 30% of the viewport. The accessibility contract is incomplete. The escalation feature has optimistic UI on a consequential action.

**Risk of one more revision pass:** Two weeks of design work and four weeks of frontend prototyping. Then a build that ships a product the team is proud of, that the institution's procurement team cannot compare to its competitors, and that the loan officer uses without resentment.

The two risks are not comparable. Revise once. Then build.
