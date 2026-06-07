# RiskIntel — Visual Acceptance Criteria

**Version:** 1.0
**Status:** Frozen for build gate
**Inherits from:** `DESIGN_BRIEF.md` v1.0, `FRONTEND_ARCHITECTURE_V1.1.md` v1.1, `DESIGN_TOKENS.md` v1.0
**Author:** Final Design Director

---

## 1. Purpose

This document is the visual gate between the frozen design and the frozen implementation. Its job is to make implementation drift reviewable from screenshots, browser inspection, and keyboard testing — not from taste.

**How this document is used:**

1. **Pre-implementation:** every engineer reads it before writing the first component.
2. **Per-PR review:** reviewers run the §3 anti-slop checklist and the §7 build gate on every visual PR.
3. **Pre-release:** the §5 scorecard is filled in for the final release candidate.
4. **Post-release:** the §7 build gate becomes the regression test. A future PR that regresses the score fails CI.

**Every rule in this document is testable from one or more of:** screenshot diff, browser DevTools inspection, axe-core output, keyboard-only walkthrough, automated visual regression.

**Every rule in this document is negative as well as positive.** "Do X" is paired with "do not Y." Both are testable.

**Subjective language is forbidden in this document.** No "looks clean," "feels premium," "modern," "professional," "beautiful." Each rule names a measurable property.

---

## 2. Global Acceptance Rules

Fifty rules. Every rule is testable. Every rule has a "check" that an engineer can run.

### 2.1 Color

**R1.** The accent color `#9A5A1F` MUST appear on ≤ 8% of any single screen's pixel area.
*Check:* Open DevTools → Elements. Sample a screenshot. Manually estimate accent ratio. Or run a pixel-counting script.

**R2.** The accent color MUST appear only on the verdict, the focus ring, the largest-positive indicator, and hover/active states of `Button[variant=primary]`.
*Check:* Grep the codebase. No `color: var(--color-accent)` outside the listed contexts.

**R3.** The negative color `#8B2E2A` MUST appear only on "Not Ready" verdicts, override flag Tags, and field-level validation errors.
*Check:* Grep `color: var(--color-negative)`. Allowed contexts enumerated.

**R4.** The positive color `#2F6B4A` MUST appear only on "Ready" verdicts and their derivative Tags.
*Check:* Grep `color: var(--color-positive)`. Allowed contexts enumerated.

**R5.** Background MUST be `#F7F5F0` (paper) or transparent. No other background colors are permitted.
*Check:* DevTools → Computed. All `background-color` properties are paper, ink (for the inverse audit header in Direction C, if adopted), or transparent.

**R6.** The audit footer MUST be `#F7F5F0` background. No drop shadow, no card, no container fill.
*Check:* DevTools inspection of the `<footer>` element.

**R7.** No color is the SOLE signal for any state. Every state indicator (positive/negative/override/disabled) MUST have a non-color signal: text, sign indicator, position, or border.
*Check:* Visually inspect every status indicator. Each has a text label, +/− sign, or position change.

**R8.** No gradients. No `linear-gradient`, `radial-gradient`, `conic-gradient`, `background-image` with gradient values.
*Check:* Grep the codebase. CI gate.

**R9.** No drop shadows. No `box-shadow`, no `filter: drop-shadow`.
*Check:* Grep the codebase. CI gate.

**R10.** No glow effects. No `filter: blur` for decorative purposes, no `box-shadow` with 0 0.
*Check:* Grep the codebase. CI gate.

**R11.** No glassmorphism. No `backdrop-filter: blur()` for any purpose.
*Check:* Grep the codebase. CI gate.

### 2.2 Typography

**R12.** The verdict MUST be the largest type on the decision spine page.
*Check:* DevTools → Computed → font-size. The verdict's font-size is greater than every other text element on the page.

**R13.** Body text MUST be 15px (`0.9375rem`). The 16px default is forbidden.
*Check:* Grep `font-size: 1rem` in component CSS. Should be 0 occurrences on body text.

**R14.** All numeric values (monetary, scores, probabilities, counts) MUST use a tabular-nums font feature.
*Check:* DevTools inspection. Every data cell has `font-variant-numeric: tabular-nums` or inherits it from a parent.

**R15.** The audit footer MUST use mono font family.
*Check:* DevTools → Computed. The audit footer's computed `font-family` includes a mono font.

**R16.** Form labels MUST use mono, uppercase, 12px (`0.75rem`), and `--color-ink-60`.
*Check:* DevTools inspection of `<label>` elements.

**R17.** No text in mixed case for status badges or override flags. Override flags MUST be uppercase mono.
*Check:* Visual inspection. All Tags are uppercase.

**R18.** No font-weight other than 400 or 500 is used.
*Check:* Grep `font-weight`. Allowed values: 400, 500.

**R19.** Letter-spacing is permitted only in two contexts: display type (`-0.5px` to `-0.25px`) and uppercase labels (`0.5px`). No other letter-spacing values.
*Check:* Grep `letter-spacing`. Allowed values enumerated.

**R20.** Line-height is set per type token. Custom line-heights in component CSS are forbidden.
*Check:* Grep `line-height` outside `:root`. Only `--type-*-line` references allowed.

### 2.3 Spacing and Layout

**R21.** Every margin, padding, and gap value MUST be a `--space-*` token. No hardcoded `px` or `rem` values for spacing.
*Check:* Grep the codebase. CI gate: `grep -E "margin|padding|gap" --include="*.css" --include="*.tsx" | grep -v "var(--space"`. No matches.

**R22.** The audit footer MUST extend full viewport width at all breakpoints, breaking out of the content container.
*Check:* Visual inspection. The audit footer's left and right edges align with the viewport edges, not with the content container.

**R23.** No component may have a border-radius other than `0`.
*Check:* Grep `border-radius` outside `:root`. No matches.

**R24.** The grid gutter is `32px` on desktop, `24px` on tablet, `16px` on mobile.
*Check:* DevTools inspection. Match against the grid tokens.

**R25.** The page content max-width is `1200px` on desktop. Pages exceeding `1200px` content width are forbidden.
*Check:* DevTools → Layout. The content container is ≤ 1200px.

**R26.** Section padding is `64px` top/bottom on desktop, `48px` on tablet, `32px` on mobile. The hero section uses `96px`–`128px`.
*Check:* DevTools inspection. Match against the §7 of `DESIGN_TOKENS.md` and FRONTEND_ARCHITECTURE_V1.1 §8.1.

**R27.** Drivers and recommendations render in 3 columns on desktop, 2 columns on tablet, 1 column on mobile. No 4-column layout for these sections.
*Check:* Visual inspection at each breakpoint.

**R28.** The verdict block MUST have ≥ 96px of vertical padding (top + bottom) on desktop.
*Check:* DevTools inspection of the verdict block.

### 2.4 Borders and Rules

**R29.** Section dividers MUST be 1px hairlines (`--color-rule` or `--color-rule-strong`). No 2px borders on section boundaries.
*Check:* DevTools inspection. Hairlines only between sections.

**R30.** Only the audit footer in Direction C's variant permits an inverted (`--color-ink` background, `--color-paper` text) block. All other surfaces are paper.
*Check:* Visual inspection.

**R31.** The override flag Tag in `accent` variant uses a 1px border in `--color-accent` and text in `--color-accent`. NEVER a filled background.
*Check:* DevTools inspection.

**R32.** Driver rank numbers (in the Direction C variant) are permissible as 11px mono in `--color-ink-40`. The rank number for the largest positive is `--color-accent`; the rank for the largest negative is `--color-negative`.
*Check:* DevTools inspection.

### 2.5 Empty and Loading States

**R33.** Empty states MUST be exactly one line of text in 17px body-large, with at most one optional text link below. Two lines maximum.
*Check:* Visual inspection of every empty state in the product. No paragraphs.

**R34.** No spinners. No pulsing dots. No circular progress indicators. Loading is a typographic `LoadingCounter` only.
*Check:* Grep the codebase for `Spinner`, `@keyframes spin`, `animation:`. Should be 0 matches outside the motion file.

**R35.** No skeleton screens. No shimmering gray placeholders. No spinning content blocks.
*Check:* Grep `skeleton`, `shimmer`, `pulse`. Should be 0 matches.

**R36.** Loading counters MUST be mono 14px in `--color-ink`. No animation.
*Check:* Visual inspection. Loading text is static.

**R37.** Loading counters MUST be bounded. Maximum wait is 30 seconds. After 30 seconds, an error state replaces the loading counter.
*Check:* Code inspection. `LoadingCounter` has `maxWaitMs` enforcement.

### 2.6 Error States

**R38.** Errors MUST be rendered as plain text. No icons, no color fills, no animations.
*Check:* Visual inspection.

**R39.** No red banners across the top of the page. No modal alert dialogs. No "Oops!" copy.
*Check:* Grep `Oops`, `error-banner`, `alert-banner`. Should be 0 matches in product copy.

**R40.** Field-level validation errors MUST be in `--color-negative`, 14px body, directly below the field. The field border switches to `--color-negative` and `aria-invalid` is set.
*Check:* Visual + DevTools inspection.

**R41.** Page-level errors MUST include the correlation ID as a copyable mono text element.
*Check:* Visual inspection. The correlation ID is visible and copyable.

**R42.** The audit footer MUST remain visible on error pages.
*Check:* Visual inspection. The footer renders even on `/500`.

### 2.7 Audit Footer

**R43.** The audit footer MUST be present on every page in the product.
*Check:* Visual inspection. No page renders without the audit footer.

**R44.** The audit footer MUST contain: model lineage (version + training data hash + deployment date), decision version, request schema version, recommendation version, ISO 8601 timestamp, officer identity, institution, correlation ID, and any override flags with their semantics.
*Check:* Field-by-field inspection. All 9 fields present.

**R45.** The correlation ID MUST be copyable (one-click copy to clipboard).
*Check:* Manual test. Click on the correlation ID. Clipboard contains the ID.

**R46.** The audit footer MUST use 14px mono in `--color-ink-80` (Direction A/B variant) or 13px mono in `--color-ink` (Direction C variant).
*Check:* DevTools inspection. Match the chosen direction's spec.

### 2.8 Navigation

**R47.** The top bar MUST be 56px tall on desktop, 48px tall on mobile, and remain sticky on scroll-down.
*Check:* DevTools inspection. Position is `sticky` or `fixed`. Height matches.

**R48.** The top bar contains exactly: product monogram, primary nav (3 items max), search field, connection indicator, privacy toggle, user identity. No more, no less.
*Check:* Visual inspection. No additional elements in the top bar.

**R49.** The user identity is a typographic monogram (1–2 character initials), not an avatar image, not a photo, not a colored circle.
*Check:* Visual inspection. The avatar is text on a square outline, no fill.

**R50.** The connection indicator is a typographic state string ("Connected" / "Reconnecting…" / "Offline — your work is saved."). No colored dot, no icon.
*Check:* Visual inspection. Text only.

---

## 3. Anti-AI-Slop Checklist

Twelve symptoms. Each lists the symptom, the cause, the violation, and the remediation.

### 3.1 Card Soup

**Symptom:** Multiple `<div>` or `<section>` elements with visible backgrounds, rounded corners, and drop shadows stacked on a gray surface.
**Cause:** Default component library behavior. LLM-generated UI gravitates to cards because cards are easy.
**Violation:** The brief forbids card soup. Cards obscure the editorial-finance direction. Rounded corners are forbidden.
**Remediation:** Refactor to hairlines. Sections are separated by 1px `--color-rule` hairlines, not by backgrounded rectangles. If a section needs emphasis, it gets a 2px `--color-ink` top border, not a background.

### 3.2 Dashboard Syndrome

**Symptom:** A "page" composed of metric tiles, charts, and KPI cards arranged in a grid, with a primary navigation rail, filter bar, and search field.
**Cause:** Default SaaS dashboard pattern. LLM training data overrepresents dashboards.
**Violation:** RiskIntel is a decision surface, not a dashboard. The architecture's history list is a reading list, not a dashboard.
**Remediation:** Refuse the "page of cards" composition. The decision spine is a single document. The history list is a chronological reading list. The settings page is a single page with three sections. No KPI tiles. No chart grids.

### 3.3 Vercel Clone Syndrome

**Symptom:** Pure white background, sans-serif, gray-200 borders, sans-serif monospace, generous padding, no accent color, no serif type.
**Cause:** Vercel's design language has been overtrained. LLMs default to it.
**Violation:** The brief specifies paper (`#F7F5F0`), serif display type, mono metadata, and a single accent color. Pure white, sans-serif, no accent is the opposite of the brief.
**Remediation:** Set background to `--color-paper`. Use serif for the verdict and section headings. Set the audit footer to mono. Add the burnt sienna accent to the verdict and focus ring.

### 3.4 Linear Clone Syndrome

**Symptom:** Dark sidebar, dark top bar, minimalist sans-serif, micro-interactions, and Cmd-K palette.
**Cause:** Linear's aesthetic is overrepresented in 2024–2025 LLM training data.
**Violation:** The brief specifies paper background, not dark. The architecture has replaced Cmd-K with a search field in the breadcrumb area.
**Remediation:** Paper background. Search field in breadcrumb, not a modal palette. No micro-interactions. State changes are 120ms transitions only.

### 3.5 Overuse of Accent Color

**Symptom:** Accent color appears on buttons, links, icons, highlights, hover states, focus states, tags, and indicators — visible in 15–30% of the screen.
**Cause:** The accent is visually distinct. LLMs over-rely on it because it produces visible results.
**Violation:** The brief caps accent at ≤ 8% of any screen. Accent is rationed.
**Remediation:** Audit the accent usage. R8 forbids accent on anything other than the verdict, the focus ring, the largest-positive indicator, and the primary button hover/active. Use `--color-ink` (and its alpha variants) for everything else.

### 3.6 Generic Settings Pages

**Symptom:** A settings page composed of labeled form fields in a 2-column grid, with a "Save" button at the bottom, and section headings.
**Cause:** Default form pattern.
**Violation:** The architecture specifies a single-page settings with three sections separated by hairlines, not a 2-column form. The settings page should not look like a standard SaaS settings panel.
**Remediation:** Three sections, hairline-divided, no cards. Each section is a typographic block. Save button is per-section, not at the bottom of the page.

### 3.7 Decorative Charts

**Symptom:** Donut, radar, gauge, 3D, or animated charts that visualize data already present in a table.
**Cause:** LLM-generated charts default to visually interesting but data-poor visualizations.
**Violation:** The brief specifies tables as the primary visualization. Charts are decompression tools only. Forbidden visualizations: pie, donut, radar, 3D, gauge, heatmap, stacked area, Sankey, animated.
**Remediation:** Use tables. The only chart-like components in the product are `FeatureContributionBar` (horizontal bars) and `ProbabilityRange` (a track with a marker). Both are monochrome + accent.

### 3.8 Decorative Icons

**Symptom:** Filled icons, colored icons, icon-heavy interfaces, icons-as-decoration on every row.
**Cause:** Icon libraries are easy to import. LLMs default to them.
**Violation:** The brief uses 1.5px line icons sparingly. Icons are verbs (Compare, Audit), not nouns. Status icons are forbidden in the decision path.
**Remediation:** Remove decorative icons. Use typographic indicators: `+`/`−` signs, mono labels, hairline rules. Line icons only where they replace text (close, expand/collapse, copy).

### 3.9 Marketing Language

**Symptom:** "Welcome to RiskIntel," "Get started in seconds," "Trusted by leading institutions," "Your data is safe with us."
**Cause:** LLM-generated copy gravitates to marketing register.
**Violation:** The brief forbids marketing copy. The product's voice is the voice of a senior analyst. Empty reassurance is forbidden.
**Remediation:** Grep the codebase. `Welcome`, `Get started`, `Trusted by`, `safe with us`. Zero matches in product copy. The sign-in page is "Sign in." Not "Welcome back."

### 3.10 Excessive Animation

**Symptom:** Smooth-scroll, parallax, hover scale transforms, spring physics, fade-in cascades, animated illustrations.
**Cause:** Motion libraries are easy. LLMs over-animate.
**Violation:** The brief specifies motion is feedback, not entertainment. The maximum motion duration is 240ms. Spring physics, bounce, parallax, and scale transforms are forbidden.
**Remediation:** Grep `transition`, `animation`, `@keyframes`. The only transitions allowed are 120ms exits and 160ms entrances. The only "emphasis" motion is 240ms on the verdict underline.

### 3.11 Underlined Links Without Cursor Affordance

**Symptom:** Underlined text links with no color or weight difference, blending into body text.
**Cause:** Default link styling.
**Violation:** The architecture requires links to be visually distinct from body text.
**Remediation:** Links in `--color-accent` when active, `--color-ink` when default, underlined always. Hover shifts color to `--color-accent`. Visited state is the same as default (no purple).

### 3.12 Status Bar / Toast Notifications

**Symptom:** Toast notifications popping from the top-right, status banners, snackbars.
**Cause:** Default UX pattern for system events.
**Violation:** The architecture forbids `Toast`. System events use typographic inline messages or the connection indicator.
**Remediation:** No Toast component. "Assessment saved" is silent (on blur). "Sign-out confirmed" is a redirect. "Could not submit" is inline below the submit button.

---

## 4. Screen-by-Screen Acceptance Criteria

### 4.1 Assess New (Type Selector) — `/assess/new`

**Above the fold (1440×900, no scroll):**
- Product monogram in top bar
- Section nav
- Two text-link options side by side, separated by a vertical hairline
- One-line description below each link
- The 1280px content area is centered with 96px outer margin

**Hierarchy order (top to bottom):**
1. Top bar (monogram, nav, connection, identity)
2. Breadcrumb ("Decision" or none)
3. Two text links in display type
4. Descriptions in 15px body
5. Optional: a typographic sub-label (e.g., "Choose a path") in 11px mono uppercase

**Typography:**
- The two link labels are 30px serif display, weight 500, letter-spacing -0.25px
- Descriptions are 15px body, weight 400
- Sub-label is 12px mono uppercase, `--color-ink-40`

**Forbidden:**
- No cards. The two options are text links with a hairline between, not rectangles.
- No images. No illustrations.
- No "Select an option" placeholder text. The page IS the selector.

**Density:** Low. Whitespace dominates. The two links are the only typographic moment.

### 4.2 Person A Intake — `/assess/person-a`

**Above the fold (1440×900):**
- Top bar
- Breadcrumb
- H1 intake heading ("Person A — Documented borrower")
- First form section heading (e.g., "Identity")
- First 2–3 form fields

**Hierarchy order:**
1. Top bar
2. Breadcrumb
3. H1
4. Form sections (Identity, Financial, Asset, Loan, Dependents)
5. Submit button (right-aligned, below the last field)

**Typography:**
- H1: 30px serif, weight 500
- Section headings: 22px serif, weight 500
- Field labels: 12px mono uppercase, `--color-ink-60`
- Field text: 15px body
- Hints: 14px body-small, `--color-ink-60`

**Forbidden:**
- No floating labels. Labels are always above the field.
- No multi-column form on mobile. Single column only.
- No wizard step indicator ("Step 2 of 5"). The form is a single page.
- No autosave toast. Drafts are silent on blur.

**Density:** High (it's a form) but no clutter. Whitespace between sections: 48px.

### 4.3 Person B Intake — `/assess/person-b`

**Above the fold:**
- Same shell as Person A
- H1: "Person B — New-to-credit borrower"

**Forbidden:**
- Same as Person A.
- The form is longer (5 sections: Identity, Household, Infrastructure, Business, Loan). It MUST scroll on a 1440×900 viewport. The submit button is reachable by scroll, not by tabs.

**Density:** Higher than Person A. The form has more fields per section. The architecture requires the form to be a single column on mobile.

### 4.4 Decision Spine — `/assess/{id}`

**Above the fold (1440×900, no scroll):**
- Top bar
- Breadcrumb ("Decision / Ramesh Kumar — RI-...")
- Metadata strip (5–6 fields: Generated, Model, Decision, Schema, Recommendation, Correlation)
- Applicant identity block (name + 2–4 detail fields)
- Verdict (the largest type on the page)
- Confidence frame (probability, range, override flag if any)
- Approve / Decline / Escalate button row
- First driver item visible

**Hierarchy order (visual scan order, top to bottom):**
1. Top bar
2. Breadcrumb
3. Metadata strip
4. Applicant identity
5. Verdict (largest type)
6. Confidence frame
7. Action buttons
8. Top drivers heading
9. Top drivers (3 columns)
10. Recommendations heading
11. Recommendations (3 columns)
12. Full breakdown (5+1 domain sections)
13. Audit footer (full width)

**Typography on the verdict block:**
- Verdict: 44px (Direction A/C) or 56px (Direction B) serif, weight 500, `--color-accent`
- Confidence: 14px mono, `--color-ink-80`
- Override flag: 12px mono uppercase, `--color-accent` (outlined, never filled)

**Forbidden:**
- The verdict MUST NOT share a row with any other element. The applicant identity is in a separate row, on the left. The verdict is on the right, or on its own row.
- No "Score: 73" framing. The number is a probability with a range.
- No dark hero. The verdict block is paper.
- No gradient on the verdict. Flat `--color-accent` only.

**Density:** Highest of any screen. The decision spine is a single document. The architecture's rule of three (identity + verdict + audit footer on first paint) applies.

### 4.5 History List — `/history`

**Above the fold (1440×900):**
- Top bar
- Breadcrumb ("History" + scope indicator)
- H1 ("Decision history — [scope]")
- Filter disclosure (collapsed by default)
- First 5–7 history items

**Hierarchy order:**
1. Top bar
2. Breadcrumb + scope
3. H1
4. Filter disclosure (single text link, expands inline)
5. History items (chronological, newest first)
6. Load more button (only if more items exist)

**Typography:**
- H1: 30px serif, weight 500
- Each history item: 15px body for name, 13px mono for date/verdict
- Filter disclosure: 14px body, underline on hover

**Forbidden:**
- No table. The list is a typographic block, not a tabular grid.
- No column headers. Each item is a self-contained block.
- No filter bar. Filters are in a disclosure that expands inline.
- No chart. No trend sparkline. No KPI tile.

**Density:** Medium. 5–7 items per viewport. Load more button at the bottom.

### 4.6 Report View — `/assess/{id}/report`

**Above the fold:**
- Top bar
- Breadcrumb ("Decision / [name] / Report")
- H1 ("Report")
- Download button + Open PDF link
- Metadata (report ID, generated at)

**Hierarchy order:**
1. Top bar
2. Breadcrumb
3. H1
4. Action buttons (Download, Open PDF)
5. Metadata (mono)

**Typography:**
- H1: 30px serif
- Buttons: 15px body, weight 500
- Metadata: 13px mono

**Forbidden:**
- No inline PDF preview. The report is a download, not an embed.
- No "Generating…" animation. The button label changes to "Generating…" but does not animate.
- No iframe. The PDF is downloaded as a file.

**Density:** Low. The page is a single action + metadata. The PDF itself contains the density.

### 4.7 Settings — `/settings`

**Above the fold:**
- Top bar
- Breadcrumb ("Settings")
- H1 ("Settings")
- Profile section heading + first 2–3 fields

**Hierarchy order:**
1. Top bar
2. Breadcrumb
3. H1
4. Profile section (name, email, institution, role, change password)
5. Defaults section (default user type, default language)
6. Security section (change password, sign-out)
7. Audit footer

**Typography:**
- H1: 30px serif
- Section headings: 22px serif
- Field labels: 12px mono uppercase
- Save button: per-section, right-aligned

**Forbidden:**
- No 2-column form layout on desktop. Single column. (The architecture specifies this.)
- No "Save all" button at the bottom. Each section has its own save.
- No tabs. Sections are hairline-divided, not tabbed.
- No "danger zone" red coloring. Section labels are mono uppercase, not red.

**Density:** Medium. Three sections, each with 2–5 fields.

### 4.8 Error States — `/500`, field errors, network errors

**Page-level error (`/500`):**
- Top bar
- H1: "RiskIntel could not complete this request."
- Sub: typographic mono with the correlation ID
- "Try again" button (primary)
- Audit footer

**Field-level error:**
- The field's text turns `--color-negative`
- The field's border turns `--color-negative`
- The field gets `aria-invalid="true"`
- Error text appears directly below the field in `--color-negative`, 14px

**Network error:**
- The connection indicator changes to "Offline — your work is saved."
- Forms are disabled. The submit button is replaced by "Reconnecting…"
- No modal. No banner. The indicator is the signal.

**Forbidden:**
- No red banner across the top of the page.
- No modal alert dialog. Native `alert()` is forbidden.
- No "Oops!" / "Something went wrong" copy.
- No icon next to the error text.

### 4.9 Empty States — every list view

**Pattern (consistent across all empty states):**
- One line of text in 17px body-large, `--color-ink-60`
- One optional text link in `--color-accent` below
- No illustrations. No icons. No "Looks like you're new here!" copy.

**Specific instances:**
- History, no data: "No assessments yet." + "Run a new assessment" link
- History, filter no match: "No assessments match these filters." + "Clear filters" link
- Search, no results: "No results for '[query]'. Try a different name or ID."

**Forbidden:**
- No empty state illustration. No empty state icon.
- No onboarding copy in empty states.
- No CTA that says "Get started" or "Add your first X."

### 4.10 Mobile Decision Spine — `/assess/{id}` (≤768px)

**Above the fold (375×812):**
- Top bar (48px, auto-hides on scroll-down)
- Metadata strip (12px mono, truncated)
- Applicant identity (name + 2 detail fields, stacked)
- Verdict (30px serif, `--color-accent`)
- Confidence frame (12px mono, truncated)
- Action buttons (full width, stacked or 56px tall)
- First driver item

**Hierarchy order (vertical, top to bottom):**
1. Top bar (48px)
2. Metadata strip (32px, scrolls with content)
3. Applicant identity
4. Verdict (the visual anchor of the page)
5. Confidence frame
6. Action buttons
7. Top drivers (stacked, 1 column)
8. Recommendations (stacked, 1 column)
9. Breakdown (stacked list, NOT a table)
10. Audit footer (full width, mono 12px)

**Typography on mobile:**
- Verdict: 30px (NOT 44px or 56px)
- Body: 15px
- Metadata: 12px mono
- Audit footer: 12px mono

**Forbidden:**
- No horizontal-scroll tables. The breakdown is a stacked list.
- No 56px tappable regions shrunk to 40px. Mobile is 56px.
- No sidebar or left rail. The top bar holds navigation.
- No "Available on desktop" message.
- No pinch-to-zoom on the decision spine. (Pinch is enabled for breakdown.)

**Density:** Same as desktop, with stacking. The page is a long scroll. Audit footer at the bottom, visible on scroll.

---

## 5. Screenshot Review Framework

Eight categories, each scored 1–10. The total score is the average. A score below 7.0 in any single category is a build-block.

### 5.1 Trust

**10/10:** The screen reads as consequential. The audit footer is the most visible element after the verdict. The page looks like something a regulator would accept.

**7/10:** The screen is professional. The audit footer is present but not the visual anchor.

**5/10:** The screen looks like a SaaS app with a footer. The audit metadata is a row of text.

**3/10:** The screen looks like a marketing site with a data table.

### 5.2 Clarity

**10/10:** The verdict is the first thing the eye lands on. The applicant identity, confidence, and audit footer are in clear visual hierarchy. No element competes with the verdict.

**7/10:** The verdict is dominant. The hierarchy is clear but the verdict could be larger.

**5/10:** The verdict is visible but competes with other elements (chrome, metadata, etc.).

**3/10:** The verdict is the same size as body text. The hierarchy is unclear.

### 5.3 Editorial Fidelity

**10/10:** The screen reads as a printed page. Serif display type, hairline rules, mono metadata, single accent, off-white paper. The Economist, not Stripe Press.

**7/10:** Most of the brief's typographic and color choices are visible. Minor drift (e.g., a sans-serif heading).

**5/10:** The screen mixes editorial and SaaS elements. Cards, shadows, or rounded corners appear.

**3/10:** The screen reads as a default SaaS app. No editorial fidelity.

### 5.4 Audit Readiness

**10/10:** The audit footer is full-width, contains all 9 required fields, the correlation ID is copyable, and the page is screenshot-defensible to a regulator.

**7/10:** The audit footer is present and contains most fields. The correlation ID is copyable.

**5/10:** The audit footer is present but cramped, partial, or not full-width.

**3/10:** The audit footer is missing, hidden, or non-functional.

### 5.5 Mobile Quality

**10/10:** The mobile decision spine is the same product as the desktop. Verdict is the visual anchor, audit footer is present, actions are reachable, no horizontal scroll, no "Available on desktop" copy.

**7/10:** The mobile screen is functional. The verdict is visible. Audit footer is present.

**5/10:** The mobile screen is degraded. Some elements are missing, some are crammed, some are hidden.

**3/10:** The mobile screen is broken. The verdict is small or missing. The audit footer is absent.

### 5.6 Accessibility

**10/10:** axe-core reports 0 violations. Keyboard walkthrough reaches every interactive element. Screen reader announces the verdict as the H1. Focus rings are visible on every interactive element. Contrast is AAA on body, AA on UI.

**7/10:** axe-core reports 0 critical violations. Keyboard walkthrough reaches most elements. Contrast is AA.

**5/10:** axe-core reports minor violations. Some elements are not keyboard-reachable. Some contrast is below AA.

**3/10:** axe-core reports critical violations. The verdict is not the H1. Focus rings are missing.

### 5.7 Density

**10/10:** The screen is information-rich but readable. Every element earns its place. No element is decorative. The page reads as a document, not a dashboard.

**7/10:** The screen is information-rich. A few elements are decorative or could be removed.

**5/10:** The screen has some unnecessary elements. The density is right but some whitespace is decorative.

**3/10:** The screen is sparse or cluttered. Information is missing or hidden.

### 5.8 Distinctiveness

**10/10:** A reasonable person who has seen Linear, Vercel, Stripe, and Mercury would say "this is not any of those." The aesthetic is editorial and unique.

**7/10:** The screen is distinctive but has some SaaS conventions. The overall feel is "an editorial-finance take on a SaaS product."

**5/10:** The screen could be mistaken for a B2B SaaS dashboard.

**3/10:** The screen could be mistaken for a shadcn demo.

### 5.9 Overall Scoring

The overall score is the average of the 8 categories. **The frontend is not build-complete until the overall score is ≥ 8.0 AND no single category is below 7.0.**

If a category is below 7.0, the PR is blocked with a note naming the category and the offending element.

---

## 6. Competitive Comparison

Seven products. For each, what to emulate and what to avoid.

### 6.1 Linear

**Emulate:** Linear's micro-rail (32px collapsed, expands on hover). The idea that the navigation is not a sidebar but a contextual fold. The keyboard-first culture.
**Avoid:** Linear's dark mode default. Linear's gray-200 borders. Linear's sans-serif everywhere. Linear's Cmd-K palette. Linear's micro-interactions. Linear's avatar circles with colors. Linear's settings tabs. Linear's emoji-free but icon-heavy empty states.

### 6.2 Vercel

**Emulate:** Vercel's confidence in technical detail (build hashes, deployment dates, log lines). The idea that infrastructure is part of the UI. The bold monochrome aesthetic.
**Avoid:** Vercel's pure-white background. Vercel's "deploy" button. Vercel's marketing language. Vercel's gradient logo. Vercel's dashboard tiles. Vercel's GitHub-style commit history.

### 6.3 Stripe Dashboard

**Emulate:** Stripe's tables. Stripe's documentation-quality typography. Stripe's use of serif for emphasis. Stripe's PDF report quality. Stripe's confidence in sparse layouts.
**Avoid:** Stripe's "Atlas" branding gradients. Stripe's three-step onboarding. Stripe's card-heavy dashboards. Stripe's "Stripe Sigma" analytics. Stripe's purple accent. Stripe's marketing CTAs in the product.

### 6.4 Mercury

**Emulate:** Mercury's restraint. Mercury's confidence in a single accent color. Mercury's dense data display. Mercury's no-nonsense empty states. Mercury's use of mono for financial data.
**Avoid:** Mercury's account-type badges. Mercury's product illustrations. Mercury's "Mercury is not a bank" disclaimer overlay. Mercury's rounded cards. Mercury's photo backgrounds.

### 6.5 Bloomberg Terminal

**Emulate:** Bloomberg's information density per square inch. Bloomberg's use of mono for all numerics. Bloomberg's audit-readiness. Bloomberg's lack of marketing language. Bloomberg's command-key shortcuts.
**Avoid:** Bloomberg's dark phosphor-green aesthetic. Bloomberg's color-coded data. Bloomberg's visual noise. Bloomberg's 1990s terminal frame. Bloomberg's table-heavy everything. Bloomberg's amber-on-black.

### 6.6 Government Portal

**Emulate:** Government portals' audit-readiness. Government portals' plain-language copy. Government portals' accessibility discipline. Government portals' no-tracking defaults.
**Avoid:** Government portals' 1990s aesthetic. Government portals' bureaucratic language. Government portals' low-contrast gray text. Government portals' inconsistent typography. Government portals' tabbed-everything navigation.

### 6.7 Generic shadcn Dashboard

**Emulate:** shadcn's component structure (headless primitives). shadcn's accessibility defaults. shadcn's token-based styling.
**Avoid:** shadcn's default Tailwind colors. shadcn's Card component. shadcn's dialog component (use full pages instead). shadcn's skeleton components. shadcn's toaster component. shadcn's "sonner" notifications. shadcn's data tables with checkboxes.

---

## 7. Final Build Gate

The frontend cannot be declared complete unless every item below passes. The checklist is executable from screenshots, keyboard testing, and browser DevTools.

### 7.1 Color

- [ ] No hardcoded colors in component CSS (`grep` returns 0 matches for `#`)
- [ ] No `box-shadow` in component CSS (`grep` returns 0 matches)
- [ ] No `filter: drop-shadow` or `filter: blur` in component CSS
- [ ] No `linear-gradient`, `radial-gradient`, `conic-gradient` (`grep` returns 0 matches)
- [ ] Accent color (`#9A5A1F`) appears on ≤ 8% of any screen (pixel audit on each major page)
- [ ] Accent color is used only on the verdict, the focus ring, the largest-positive indicator, and the primary button hover/active
- [ ] No traffic-light coloring on data rows
- [ ] Background is `--color-paper` on every surface except the audit footer (Direction C variant)
- [ ] `--color-positive` is used only on "Ready" verdicts and their derivative Tags
- [ ] `--color-negative` is used only on "Not Ready" verdicts, override flags, and field-level errors

### 7.2 Typography

- [ ] The verdict is the largest type on the decision spine page
- [ ] Body text is 15px (`0.9375rem`) on all surfaces
- [ ] No `font-size: 1rem` in body text (16px default is forbidden)
- [ ] All numeric values use `font-variant-numeric: tabular-nums`
- [ ] The audit footer uses mono font family
- [ ] Form labels are mono, uppercase, 12px, `--color-ink-60`
- [ ] Override flags are uppercase mono
- [ ] No font-weight other than 400 or 500
- [ ] Letter-spacing is only used in display type and uppercase labels
- [ ] Serif type is used on the verdict and section H2
- [ ] No mixed case for status badges

### 7.3 Layout and Spacing

- [ ] Every margin, padding, and gap is a `--space-*` token (`grep` returns 0 hardcoded values)
- [ ] The audit footer extends full viewport width at every breakpoint
- [ ] No `border-radius` other than `0` (`grep` returns 0 matches)
- [ ] The page content max-width is 1200px on desktop
- [ ] Drivers and recommendations render in 3 columns on desktop, 2 on tablet, 1 on mobile
- [ ] The verdict block has ≥ 96px of vertical padding on desktop
- [ ] Mobile decision spine has no horizontal-scroll tables

### 7.4 Components

- [ ] No `Spinner` component in the codebase (`grep` returns 0 matches)
- [ ] No `Toast` component in the codebase (`grep` returns 0 matches)
- [ ] No skeleton or shimmer components (`grep` returns 0 matches)
- [ ] No `Modal` component (use full pages or `ModalRouteShell`-equivalent patterns)
- [ ] No carousel components
- [ ] No `Alert` components (use `Tag` or `EmptyState`)
- [ ] No pie, donut, radar, 3D, gauge, or animated charts in the rendered output

### 7.5 Content

- [ ] No "Welcome" copy in the product (`grep` returns 0 matches in user-facing copy)
- [ ] No "Get started" CTAs (`grep` returns 0 matches)
- [ ] No "Trusted by" or "safe with us" copy (`grep` returns 0 matches)
- [ ] Empty states are one line, max two, no illustrations, no icons
- [ ] No marketing language in error messages
- [ ] No "Oops!" in any error copy
- [ ] Empty states, error states, and loading states use plain text only

### 7.6 Audit Footer

- [ ] Audit footer is present on every page in the product
- [ ] Audit footer contains all 9 required fields (model lineage, decision version, request schema version, recommendation version, timestamp, officer, institution, correlation ID, override flags)
- [ ] Correlation ID is copyable to clipboard
- [ ] Audit footer uses 14px mono (`DESIGN_TOKENS.md` Direction A/B) or 13px mono (Direction C)
- [ ] Audit footer is full viewport width on all breakpoints

### 7.7 Navigation

- [ ] Top bar is 56px on desktop, 48px on mobile, sticky on scroll
- [ ] Top bar contains exactly 6 elements: monogram, nav (3 max), search, connection indicator, privacy toggle, identity
- [ ] User identity is a typographic monogram, not an avatar image
- [ ] Connection indicator is a typographic state string, no colored dot
- [ ] Search field uses `/` shortcut, no Cmd-K modal
- [ ] No "Available on desktop" copy in mobile views

### 7.8 Loading and Error States

- [ ] Loading is rendered as a typographic `LoadingCounter` (mono 14px, static, no animation)
- [ ] Loading is bounded at 30 seconds
- [ ] Errors are plain text, no icons, no animations, no color fills
- [ ] Field errors are in `--color-negative`, 14px, below the field, with `aria-invalid`
- [ ] Page errors include the correlation ID as a copyable mono element
- [ ] The audit footer remains visible on error pages
- [ ] No `Oops!` / `Something went wrong` copy

### 7.9 Motion

- [ ] No spring physics, no bounce, no parallax
- [ ] No motion longer than 240ms
- [ ] All transitions honor `prefers-reduced-motion: reduce`
- [ ] No `transition: all`
- [ ] No `animation:` outside the motion file

### 7.10 Accessibility (WCAG 2.2 AA, AAA target)

- [ ] axe-core reports 0 violations on every route
- [ ] The verdict is the H1 of the decision spine page
- [ ] Every interactive element is keyboard-reachable
- [ ] Focus rings are visible on every interactive element
- [ ] All form fields have associated labels
- [ ] All error messages are announced to screen readers
- [ ] Contrast is AAA on body text (≥ 7:1)
- [ ] Contrast is AA on UI elements (≥ 3:1)

### 7.11 Distinctiveness

- [ ] The screenshot cannot be mistaken for Linear
- [ ] The screenshot cannot be mistaken for Vercel
- [ ] The screenshot cannot be mistaken for Stripe Dashboard
- [ ] The screenshot cannot be mistaken for a shadcn demo
- [ ] The aesthetic reads as "editorial finance" — printed, not app-like

### 7.12 Scorecard

- [ ] Trust: ≥ 7
- [ ] Clarity: ≥ 7
- [ ] Editorial Fidelity: ≥ 7
- [ ] Audit Readiness: ≥ 7
- [ ] Mobile Quality: ≥ 7
- [ ] Accessibility: ≥ 7
- [ ] Density: ≥ 7
- [ ] Distinctiveness: ≥ 7
- [ ] Overall average: ≥ 8.0

### 7.13 Sign-off

The frontend is build-complete when:

1. All items in §7.1–§7.11 are checked.
2. The scorecard in §7.12 passes the thresholds.
3. The build is reviewed by at least one engineer who was not the author.
4. The build is reviewed by the Principal Product Designer.
5. The audit footer is verified to render on every route.

Any unchecked item blocks the release. No exceptions.
