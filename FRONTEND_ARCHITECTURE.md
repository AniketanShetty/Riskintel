# RiskIntel — Frontend Architecture

**Version:** 1.0
**Status:** Frozen for build
**Inherits from:** `DESIGN_BRIEF.md` v1.0
**Author:** Principal Product Designer, Frontend Architecture Lead

---

## 0. Architecture Principles

These six principles govern every architectural decision in this document. They are inherited from the design brief and restated here in their engineering-relevant form.

1. **Verdict-forward** — every architectural path makes the verdict reachable in one scroll, on every device, on every screen, on every connection.
2. **Evidence-anchored** — every component is wired to a typed API contract; no component is allowed to invent a value.
3. **Dignity-preserving** — the architecture forbids "fun" features: no animations that are not feedback, no decorative micro-interactions, no empty reassurance copy.
4. **Audit-ready** — the audit footer is not a route, not a feature flag, and not a developer panel. It is in the page shell, always rendered.
5. **Calm density** — the architecture supports information density without overhead. Components compose; nothing is one-off.
6. **Offline-resilient** — every critical-path view has a static fallback that renders without the network. The architecture degrades honestly.

**The rule of three:** every page renders three things on first paint. (1) The applicant identity. (2) The verdict slot, even if empty. (3) The audit footer. These three are non-negotiable. Everything else may load progressively.

---

## 1. User Flows

The product has three primary flows and four secondary flows. All flows are described in the same six-stage template: **Entry → Identify → Decide → Defend → Archive → Exit.**

### 1.1 Primary Flow — Standard Person A Assessment

**Persona:** Loan officer at a small private bank, salaried applicant, full documentation.

| Stage | What the officer does | What the product does |
|---|---|---|
| Entry | Opens dashboard, clicks "New Assessment" | Displays two-card intake: Person A / Person B. No tour. No upsell. |
| Identify | Selects Person A, fills form (income, CIBIL, assets, dependents, loan request). Tab-to-tab, no pagination. | Validates inline. Saves draft to local store on blur. No autosave toast. |
| Submit | Clicks "Run Assessment" | Calls `POST /api/assess/person-a`. Renders decision spine (§3.2). Loading state is a typographic counter, not a spinner. |
| Decide | Reads verdict, top drivers, recommendations. Has 30 seconds to approve, decline, or escalate. | Renders three primary actions below the verdict: **Approve, Decline, Escalate.** Each is a button, not a modal trigger. |
| Defend | Hovers any number in the breakdown. Audit footer is always visible. | Shows inline provenance on hover: input field, model version, contribution value. Audit footer is one scroll away at all times. |
| Archive | Clicks "Generate Report" or "Close." | Report is generated via `POST /api/report/generate`. The PDF is served with `Content-Disposition: attachment`. The assessment is recorded in local history. |

**Time budget for the flow:** 90 seconds. Anything longer is an architecture failure.

### 1.2 Primary Flow — Standard Person B Assessment

**Persona:** MFI field officer, NTC (new-to-credit) rural borrower, partial documentation.

Same six stages. The differences:

- **Entry:** Default selection is Person B for users with an "MFI" role tag. The two-card intake is still shown, but the MFI card is the primary visual emphasis.
- **Identify:** Form includes infrastructure, household, and business-viability fields. Form is longer; the page is one column on tablet, two on desktop.
- **Submit:** Calls `POST /api/assess/person-b`.
- **Decide:** Verdict is a readiness band, not a probability. The E5 floor-breach override (when triggered) is shown explicitly as a "Floor breach" tag, never hidden.
- **Defend:** The income proxy used (when original income is missing) is shown in the breakdown, not hidden. The officer can see "income imputed as ₹4,200/mo from monthly expenses" inline.

### 1.3 Primary Flow — Assessment History Lookup

**Persona:** Senior credit analyst revisiting a past decision to defend it in a review meeting.

| Stage | What the analyst does | What the product does |
|---|---|---|
| Entry | Clicks "History" in the navigation. | Renders a filterable table: date range, applicant name, verdict, user type, model version. |
| Identify | Filters to a date range and applicant name. | Filters in real time, no Apply button. Filter state persists in URL. |
| Decide | Clicks a row. | Opens the assessment detail page, which is the same decision spine the officer saw at decision time. |
| Defend | Reads the audit footer. | Audit footer is the same one that was on the page at decision time. Identical timestamp, version, correlation ID. |
| Archive | Downloads the report PDF. | `GET /api/report/download/{report_id}`. PDF returns 200 with the same bytes the original generate returned. |
| Exit | Closes the tab. | No goodbye. No retention prompt. The product does not market to its own users. |

### 1.4 Secondary Flow — Escalation

The officer selects "Escalate" on a decision. A side panel slides in (320ms, no bounce) with:

- The full decision spine (read-only).
- A free-text escalation note field (limited to 500 chars, monospace).
- A recipient selector (the officer's team, single-select).
- An "Escalate" primary button.

On submit: `POST /api/escalations` (out of scope for the frozen backend; stubbed locally with optimistic UI). The decision spine moves from "Decide" state to "Pending Review" state, indicated by a hairline tag, not a banner.

### 1.5 Secondary Flow — Compare Two Assessments

A power-user feature for analysts. Available only when two assessments are selected from history.

- Renders a side-by-side decision spine at 50% width each, on a single page.
- Differences are highlighted by a hairline, never by color.
- Each side retains its own audit footer; a third footer at the page bottom shows the comparison's model version delta.

### 1.6 Secondary Flow — Batch Assessment (MFI only)

MFI users with field-officer accounts can upload a CSV of applicants. The flow is async:

- Upload accepts CSV, parses client-side, shows a row count and validation summary.
- Submit triggers a batch job. The product polls a `GET /api/assessments/batch/{job_id}` endpoint every 2 seconds (or longer on slow connections, per §6).
- Progress is shown as a typographic counter: "23 of 140 complete. 2 failed validation."
- Completed rows are clickable, opening the standard decision spine. Failed rows show the validation reason inline.
- The batch job's results are downloadable as a CSV (audit metadata included per row).

### 1.7 Secondary Flow — Sign-out

There is no sign-out flow described. The product signs the user out on session expiry with a single full-page message: "Session expired. Sign in to continue." with a single primary button. There is no "stay signed in" toggle, no "remember me," no marketing footer on the sign-out page.

---

## 2. Sitemap

The product has **eight top-level routes**, of which **five are core** and **three are support**. Every route is reachable in two clicks from any other route.

### 2.1 Top-level routes

| Route | Purpose | Auth | Cold-load |
|---|---|---|---|
| `/` | Redirects to `/assess/new` or `/history` based on role and last activity | Required | No |
| `/assess/new` | New assessment entry — choose Person A or Person B | Required | Yes |
| `/assess/person-a` | Person A intake form | Required | Yes |
| `/assess/person-b` | Person B intake form | Required | Yes |
| `/assess/{id}` | Decision spine for a specific assessment | Required | Yes |
| `/history` | Filterable history of past assessments | Required | Yes |
| `/history/compare` | Side-by-side comparison of two assessments | Required | No (lazy) |
| `/settings` | User preferences (model version override, default user type, batch upload credentials) | Required | No (lazy) |

### 2.2 Support routes (out of core flow)

| Route | Purpose |
|---|---|
| `/auth/sign-in` | Sign-in form. Three fields: email, password, institution code. |
| `/auth/forgot` | Password recovery. Email field only. |
| `/auth/locked` | Account locked. Plain text message. No marketing. |
| `/legal/terms` | Frozen terms of use. |
| `/legal/privacy` | Frozen privacy policy. |
| `/legal/audit` | Public-facing audit policy (how the product is itself audited). |
| `/status` | Service status. The product's own status, surfaced honestly. |
| `/404` | Not found. Plain text. |
| `/500` | Server error. Plain text. |

### 2.3 Route hierarchy (visual)

```
/                          (index — redirects)
├── /auth
│   ├── /sign-in
│   ├── /forgot
│   └── /locked
├── /assess
│   ├── /new               (intake type selector)
│   ├── /person-a          (intake form A)
│   ├── /person-b          (intake form B)
│   └── /{id}              (decision spine)
│       ├── /report        (generate + download PDF)
│       └── /escalate      (escalation side panel — modal route)
├── /history
│   ├── (default — list)
│   ├── /{id}              (decision spine from history)
│   └── /compare           (two-up comparison)
├── /settings
│   ├── /profile
│   ├── /defaults
│   └── /batch
├── /legal
│   ├── /terms
│   ├── /privacy
│   └── /audit
├── /status
└── (errors)
    ├── /404
    └── /500
```

### 2.4 URL design rules

- Kebab-case, lowercase, ASCII only.
- IDs are opaque (UUID v4), not sequential. No `?id=123` — the ID is in the path.
- Filter state is in the query string and is canonical: `?from=2026-01-01&to=2026-01-31&type=person_a`.
- No hash routing. No fragment identifiers for state.
- URLs are shareable. A URL opened in a fresh tab renders the same content for the same data.

---

## 3. Screen Inventory

Every screen in the product is described below. Each entry lists: purpose, content blocks (from the design brief's decision spine), data sources, and which user roles see it.

### 3.1 Screen: Sign-in

**Route:** `/auth/sign-in`
**Purpose:** Authenticate a user.
**Content blocks:** Sign-in form, password recovery link, institution code, legal links.
**Data sources:** None (POST on submit).
**Roles:** All.
**Notes:** No "remember me." No "sign in with Google." No SSO marketing.

### 3.2 Screen: Assessment Intake — Type Selector

**Route:** `/assess/new`
**Purpose:** Choose Person A or Person B.
**Content blocks:** Two cards. Card A: name, key fields preview. Card B: name, key fields preview. No images on the cards — typographic only.
**Data sources:** None.
**Roles:** Loan officer, MFI field officer, credit analyst.

### 3.3 Screen: Person A Intake Form

**Route:** `/assess/person-a`
**Purpose:** Collect Person A inputs.
**Content blocks:** Identity, financial, asset, loan, dependents. Each section is a labeled group with a hairline rule. Submit button is below the last field, right-aligned.
**Data sources:** `POST /api/assess/person-a` on submit.
**Roles:** Loan officer, credit analyst.

### 3.4 Screen: Person B Intake Form

**Route:** `/assess/person-b`
**Purpose:** Collect Person B inputs.
**Content blocks:** Identity, household, infrastructure, business, loan. Form is longer than Person A but follows the same structure.
**Data sources:** `POST /api/assess/person-b` on submit.
**Roles:** MFI field officer, loan officer.

### 3.5 Screen: Decision Spine (the hero screen)

**Route:** `/assess/{id}` (also reachable from history)
**Purpose:** Display the underwriting decision.
**Content blocks (in order, from the design brief):**
1. Applicant identity block (name, age, business, loan request, generated timestamp)
2. **Verdict** — the answer, hero type, full width
3. **Confidence frame** — band, probability range, override flags
4. **Top drivers** — 3 to 5 ranked factors (positive and negative)
5. **Recommendations** — actionable next steps
6. **Archetype** — single-line secondary context
7. **Full breakdown** — expandable domain groups, tabular data
8. **Audit footer** — model lineage, decision version, schema version, timestamp, correlation ID

**Primary actions:** Approve, Decline, Escalate. Each is a primary button below the verdict, never a modal trigger.

**Data sources:** `GET /api/assessments/{id}` (assumed; backend may differ — see §11).

**Roles:** All.

**Notes:** This is the screen that defines the product. Every design decision in the brief ultimately serves this screen.

### 3.6 Screen: Report Generation Modal-Route

**Route:** `/assess/{id}/report`
**Purpose:** Generate and download the PDF.
**Content blocks:** Loading state (typographic), success state (download button, "Open PDF" inline link), error state (plain text).
**Data sources:** `POST /api/report/generate`, `GET /api/report/download/{report_id}`.
**Roles:** All.
**Notes:** This is a modal route, not a modal dialog. The URL changes. The browser back button works.

### 3.7 Screen: History — List

**Route:** `/history`
**Purpose:** Browse past assessments.
**Content blocks:** Filter bar (date range, type, verdict, applicant name), tabular list (rows: applicant, type, verdict, date, action). Row hover: hairline + type-color shift, no background fill.
**Data sources:** `GET /api/assessments?from=...&to=...&type=...`.
**Roles:** All.
**Notes:** Pagination is cursor-based, not page-based. The user never sees "Page 3 of 12." They see "Showing 41–60 of 247." Infinite scroll is forbidden (§3 of design brief). A "Load more" button is the only pagination affordance.

### 3.8 Screen: History — Compare

**Route:** `/history/compare?ids=...&ids=...`
**Purpose:** Side-by-side decision spine for two assessments.
**Content blocks:** Two decision spines at 50% width, vertical divider hairline, comparison footer showing model version delta.
**Data sources:** Two `GET /api/assessments/{id}`.
**Roles:** Credit analyst, senior loan officer.
**Notes:** Available only with two IDs in the query string. A 400 page is shown otherwise.

### 3.9 Screen: Settings — Profile

**Route:** `/settings/profile`
**Purpose:** User account management.
**Content blocks:** Name, email, institution, role. Change password link.
**Data sources:** `GET /api/me`, `PATCH /api/me`.
**Roles:** All.

### 3.10 Screen: Settings — Defaults

**Route:** `/settings/defaults`
**Purpose:** User workflow defaults.
**Content blocks:** Default user type selector, default model version override (advanced), default decision language.
**Data sources:** `GET /api/me/preferences`, `PUT /api/me/preferences`.
**Roles:** All.
**Notes:** The "default model version" selector is hidden behind a disclosure. Default users do not need it.

### 3.11 Screen: Settings — Batch (MFI only)

**Route:** `/settings/batch`
**Purpose:** CSV upload for batch assessment.
**Content blocks:** File drop zone, sample CSV download link, recent batch jobs list.
**Data sources:** `POST /api/assessments/batch`, `GET /api/assessments/batch/{job_id}`.
**Roles:** MFI field officer (manager).
**Notes:** The drop zone uses OS-native file picker on click. No drag-and-drop marketing animation.

### 3.12 Screen: Error pages

**Routes:** `/404`, `/500`
**Purpose:** Render uncaught routing and server errors.
**Content blocks:** Plain text message, sign-out or back link, audit footer.
**Data sources:** None.
**Notes:** No illustrations. No "oops." No "something went wrong but we're on it." Plain text, hairline, link.

### 3.13 Global elements

These render on every page in the application shell:

- **Top bar** — product name (typographic monogram), current section, user identity dropdown, sign-out.
- **Section navigation** — left rail on desktop (240px), bottom bar on mobile (56px).
- **Audit footer** — page-bottom, always visible.
- **Connection state indicator** — top-right, typographic only ("Connected" / "Reconnecting" / "Offline"). Never a colored dot.

---

## 4. Navigation Structure

### 4.1 Primary navigation

The top-level navigation has five items, in this order, on every screen:

1. **New Assessment** → `/assess/new`
2. **History** → `/history`
3. **Compare** → `/history/compare` (active state only when two assessments are selected)
4. **Settings** → `/settings`
5. **Sign out** → `/auth/sign-in` (after redirect)

The current section is indicated by a 2px hairline underline in `--ink`, not by a background color, not by a bold weight. The hover state is a color shift to `--accent`. There is no active-state background fill.

### 4.2 Section navigation (left rail)

The left rail renders three items when on `/assess/*`:

1. **New**
2. **Person A**
3. **Person B**

It renders one item when on `/history/*`:

1. **List**

It renders four items when on `/settings/*`:

1. **Profile**
2. **Defaults**
3. **Batch** (MFI only)
4. **—** (no fourth item for non-MFI)

The left rail is 240px wide on desktop. It collapses to a 56px bottom bar on tablet and mobile. The collapse happens at 1024px viewport width.

### 4.3 Within-page navigation (decision spine anchors)

The decision spine has five in-page anchors, visible as a sticky right rail on desktop and a sticky bottom bar on mobile:

1. Verdict
2. Confidence
3. Drivers
4. Breakdown
5. Audit

Clicking an anchor scrolls the page to the section. The active anchor is underlined. There is no smooth-scroll animation.

### 4.4 Breadcrumbs

Breadcrumbs render on every screen except `/assess/new` and `/auth/*`. The breadcrumb shows: **Section / Page.** Example: `History / Ramesh Kumar — RI-20260606-B-00012`. The breadcrumb is set in the smallest body type, in `--ink` at 60% alpha, with a hairline below. It is informational, not interactive in the sense of a navigation menu — clicking the section part navigates to the section index.

### 4.5 Modal routes

Three routes open as modal routes (URL changes, history is updated, back works):

- `/assess/{id}/report` — report generation
- `/assess/{id}/escalate` — escalation panel
- `/history/{id}/breakdown` — full breakdown overlay (for senior reviewers)

Modal routes render the parent page behind a 60% black overlay. There is no slide-in animation. The modal opens at fade-in (120ms) and closes at fade-out (120ms).

### 4.6 Keyboard navigation

The product is fully keyboard navigable. The keyboard model:

- **Tab** moves through interactive elements in document order
- **Shift-Tab** moves backward
- **Enter** activates the focused element
- **Escape** closes any open modal route, then any open dropdown, then navigates back
- **Cmd/Ctrl-K** opens a command palette (search by applicant name, assessment ID, or report ID)
- **Cmd/Ctrl-Enter** submits any open form

Focus rings are 2px hairlines in `--accent`, never the default browser blue.

---

## 5. Component Inventory

The component library is **closed.** Every component used in the product is in this list. New components require a design review. Components are categorized as atoms, molecules, and organisms, following a strict atomic-design discipline.

### 5.1 Atoms

| Component | Purpose | Variants |
|---|---|---|
| `Text` | All text rendering. Wraps type scale, weight, color. | Display, Body, Data, Mono. Sizes: 14, 15, 17, 22, 30, 44. |
| `Rule` | Horizontal hairline divider. | Default (12% alpha), strong (24% alpha), accent (in `--accent`). |
| `Tag` | Inline status label. | Default, Positive, Negative, Accent. Never filled. Always outlined. |
| `Button` | Primary action. | Primary (`--ink` background, `--paper` text), Secondary (outlined), Tertiary (text-only with underline on hover). One size per role (default, large for hero verdict). |
| `Input` | Form field. | Text, Number, Select, Date, Textarea. Inline validation. No floating labels. |
| `Label` | Form field label. | Above-input, always. Set in mono, 12pt equivalent. |
| `Checkbox` | Boolean input. | Default. No indeterminate visual variant — indeterminate is rendered as a third state. |
| `Radio` | Single-select from a small set. | Default. |
| `Select` | Single-select from a large set. | Default, searchable. |
| `Tooltip` | Hover-revealed supplementary text. | Default. Appears at 240ms hover. Dismissable with Escape. |
| `Badge` | Small numeric or status indicator. | Numeric (count), Status (one of 5 states). |
| `Link` | Text link. | Default, Subtle (in lists). Always underlined. |
| `Kbd` | Keyboard shortcut indicator. | Default. |
| `Spinner` | Loading state. | **FORBIDDEN.** Use `LoadingCounter` instead. |
| `LoadingCounter` | Typographic loading indicator. | Default. Shows "Loading 4 of 7 signals…" |

### 5.2 Molecules

| Component | Purpose | Composition |
|---|---|---|
| `VerdictBlock` | Hero verdict display. | `Text` (display 44pt), `ConfidenceFrame`, primary action buttons. |
| `ConfidenceFrame` | Band, probability range, override flags. | `Tag`, `Text` (data 17pt), `Tooltip` per flag. |
| `DriverList` | Ranked list of top factors. | `DriverItem` × N, `Rule`. |
| `DriverItem` | A single factor: name, value, direction, contribution. | `Text`, `Tag`, `Rule`. |
| `BreakdownTable` | Tabular view of inputs and contributions. | `Table`, `Rule`, `Tag`. |
| `DomainSection` | Collapsible group of related fields. | `Heading`, `Rule`, `BreakdownTable` or child list. |
| `ApplicantIdentity` | Identity block at top of decision spine. | `Text`, `Rule`. |
| `AuditFooter` | Page-bottom audit metadata. | `Text` (mono), `Kbd` (for shortcut hint), `Link` to full audit log. |
| `FilterBar` | History filter controls. | `Input` × N, `Select` × N, `Button` (Apply is not needed; filters are real-time). |
| `HistoryRow` | A row in the history table. | `Text`, `Tag`, `Link`. |
| `CommandPalette` | Cmd-K search. | `Input`, `CommandList`. |
| `EscalationPanel` | Side panel for escalation. | `Textarea`, `Select`, `Button`. |
| `ReportPanel` | Report generation modal route content. | `LoadingCounter`, `Button`, `Link`. |
| `ConnectionIndicator` | Network state at top-right. | `Text` (mono), `Tag`. |
| `Toast` | Brief, dismissable notification. | `Text`, `Button` (Dismiss). For system events only (assessment saved, sign-out confirmed). Never for marketing. |
| `EmptyState` | Empty list / no results. | `Text`, optional `Button`. |
| `ErrorBoundary` | React error boundary fallback. | `Text`, `Link` to home. |
| `ModalRouteShell` | Modal route wrapper. | Children + close button. |

### 5.3 Organisms

| Component | Purpose | Composition |
|---|---|---|
| `AppShell` | Top bar + left rail + content + audit footer. | All global organisms. |
| `TopBar` | Product name + section + user identity. | `Text`, `Dropdown`. |
| `LeftRail` | Section navigation. | `Link` × N. |
| `BottomBar` | Mobile section navigation. | `Link` × N. |
| `DecisionSpine` | The hero screen. | `ApplicantIdentity` + `VerdictBlock` + `DriverList` + `Recommendations` + `Archetype` + `DomainSection` × N + `AuditFooter`. |
| `IntakeForm` | Person A or Person B form. | `DomainSection` × N + `Button` (Submit). |
| `HistoryTable` | History list. | `FilterBar` + `HistoryRow` × N + pagination. |
| `ComparisonView` | Two-up decision spine. | `DecisionSpine` × 2 + comparison footer. |
| `BatchUploader` | CSV upload + job status. | `Input` (file) + job list. |
| `SignInForm` | Authentication. | `Input` × 3 + `Button`. |
| `SettingsPage` | Settings sub-pages. | `DomainSection` + `Button`. |
| `ErrorPage` | 404, 500, session expired. | `Text` + `Link`. |

### 5.4 Forbidden components

These components are explicitly rejected. They will be removed from any PR that introduces them.

- `Carousel`
- `Modal` (as a non-URL dialog — use `ModalRouteShell` instead)
- `Alert` (use `Tag` or `EmptyState`)
- `ProgressBar` with animation (use typographic progress)
- `Toast` with marketing copy (use `Toast` for system events only)
- `EmptyIllustration` (typographic empty state only)
- `StatCard` with gradient fill (use `DriverItem` in a `DriverList`)

### 5.5 Component state discipline

Every component has a documented set of states. The states are exhaustive; a component is not "done" until every state is designed. The states are:

- Default
- Hover
- Focus
- Active / Pressed
- Disabled
- Loading (where applicable)
- Error (where applicable)
- Empty (where applicable)
- Read-only (where applicable)

Each component spec sheet includes every state. No state is unstated. No state is "designed later."

---

## 6. Data Visualizations

RiskIntel is a tabular product. Charts are used only where they communicate something a table cannot. Each visualization has a stated purpose and a stated rejection.

### 6.1 Visualization principles

1. **Tables are the primary visualization.** A table is preferred over any chart.
2. **Charts are decompression tools.** A chart is used to make a tabular relationship *spatially* legible, not to introduce information that is not in the table.
3. **No pie, donut, radar, or 3D.** A pie chart hides precision. The product's job is precision.
4. **No traffic-light coloring.** A chart's color is structural (axes, groupings) or it is the single accent.
5. **All charts are monochrome + accent.** No multi-color palettes.
6. **Charts have legends in plain prose, not icons or color swatches.** "Negative contribution" not "red dot."

### 6.2 Approved visualizations

#### 6.2.1 `FeatureContributionBar`

**Purpose:** Show the contribution of each feature to the final probability.
**Form:** Horizontal bar chart. One bar per feature. Bar length is the absolute contribution. Bar direction (left/right) shows the sign. Color is `--ink` for all bars. The single largest positive and single largest negative are highlighted with `--accent` and `--negative` (oxblood) respectively.
**Rejected alternatives:** waterfall (over-complex for this data), pie (no precision), diverging stacked bar (no total visible).
**Used in:** Decision spine, top drivers section.

#### 6.2.2 `ProbabilityRange`

**Purpose:** Show the probability as a range, not a point estimate.
**Form:** A horizontal track, 100% width. A range bar at the probability range. A center marker at the point estimate. Numeric labels in mono, below the track. The track is `--ink` at 8% alpha. The range bar is `--ink` at 60% alpha. The center marker is `--accent`.
**Rejected alternatives:** gauge (false precision, no range), dot-on-scale (no range visible).
**Used in:** Confidence frame, decision spine.

#### 6.2.3 `ComponentBreakdown`

**Purpose:** Show the readiness components (financial health, housing, infrastructure, household burden, business viability) and their weights.
**Form:** Five rows. Each row: component name, score, weight, hairline. No chart. A table is the right tool.
**Rejected alternatives:** radar (no precision, no weight visible), donut (no precision).
**Used in:** Decision spine, full breakdown.

#### 6.2.4 `CibilTierStrip`

**Purpose:** Show where the applicant's CIBIL score sits relative to the tier thresholds.
**Form:** A horizontal track, four labeled segments (P1 ≥ 701, P2 669–700, P3 659–668, P4 ≤ 658). A marker at the applicant's score. Tick marks at the boundaries. Numeric labels in mono.
**Used in:** Person A decision spine, top drivers.

#### 6.2.5 `HistoryTrend`

**Purpose:** Show the verdict distribution over time (institution-wide, for senior reviewers).
**Form:** A sparkline-style mini chart. One data point per day. Y-axis is the count of approvals/declines. X-axis is the date. The chart is monochrome. A "details" link below opens the full history table.
**Rejected alternatives:** line chart with multi-color (clutter), bar chart (visual weight too high for a summary).
**Used in:** History page, top of list.

### 6.3 Forbidden visualizations

| Visualization | Why forbidden |
|---|---|
| Pie / donut | Hides precision. The product deals in probabilities with three decimal places. |
| Radar | No precision. Weights hidden. |
| 3D any | Distortion is a bug. |
| Gauge | False precision, no range visible. |
| Heatmap | Color carries meaning. Forbidden. |
| Stacked area | Cumulative impact obscured. |
| Sankey | Beautiful, not legible. |
| Animated chart | Animation is feedback, not narration. |
| Map (geo) | Not in scope for v1. MFI branch distribution is a future feature. |

---

## 7. Error States

Errors are not exceptional. They are part of the product. Every error is rendered with the same type, the same color, and the same restraint as the rest of the interface. Errors never use red banners, never use exclamation points, never use "oops."

### 7.1 Error state principles

1. **Errors are plain text.** No icons. No color fills. No animations.
2. **Errors are specific.** "Could not load assessment 3a4f. The assessment may have been deleted, or your access may have changed."
3. **Errors are recoverable.** Every error has at least one action: retry, go back, or sign in again.
4. **Errors are quiet.** They replace the page content. They do not pop over it. They do not toast.
5. **Errors are logged.** Every error emits a structured event to the audit log. The officer can copy the correlation ID.

### 7.2 Error catalog

| Error | Where it appears | UI treatment |
|---|---|---|
| Validation error (form field) | Inline, below the field | `Text` in `--negative` (oxblood), 14pt. Field border switches to `--negative`. The first invalid field receives focus. |
| Form submit error | Top of form, hairline-separated | `Text` in `--negative`, 15pt. Below: list of specific field errors. |
| API 400 (bad request) | Replace page content | `Text` (display, 30pt) + paragraph + retry button. |
| API 401 (unauthorized) | Redirect to `/auth/sign-in?from=...` | Sign-in page with a `Text` line above the form: "Your session expired." |
| API 403 (forbidden) | Replace page content | `Text` (display, 30pt) "You do not have access to this assessment." + back link. |
| API 404 (not found) | Replace page content | `Text` (display, 30pt) "This assessment does not exist or has been deleted." + back link. |
| API 409 (conflict, e.g., report id collision) | Inline, near the action that triggered it | `Text` in `--negative` + retry button. The audit log entry is shown as a tooltip. |
| API 429 (rate limit) | Replace page content | `Text` (display, 30pt) "You have made many requests. Please wait a moment." + audit footer with the rate-limit ID. |
| API 500 (server error) | Replace page content | `Text` (display, 30pt) "RiskIntel could not complete this request." + retry button + correlation ID copy button. |
| API 503 (service unavailable) | Replace page content | `Text` (display, 30pt) "RiskIntel is temporarily unavailable. We are working on it." + link to `/status` page. |
| Network offline | Top-bar `ConnectionIndicator` changes state | `ConnectionIndicator` shows "Offline — your work is saved." No modal, no banner. |
| Network reconnect failure | `ConnectionIndicator` shows "Reconnecting" then "Offline" | Same. No toast. |
| JS error / unhandled exception | React error boundary fallback | `ErrorPage` (display 30pt + correlation ID + sign-out link). |
| Form field with imputed value | Inline, in the field | `Text` 12pt, mono, in `--ink` at 60% alpha: "Income imputed as ₹4,200/mo from monthly expenses." |

### 7.3 The "forbidden" error patterns

These are explicitly rejected:

- **Red banner across the top of the page.** Banners train the user to ignore them.
- **Modal alert dialogs.** Native browser alerts. They block the page. They break the keyboard model.
- **"Oops!" / "Something went wrong" copy.** The product knows what went wrong. It says so.
- **"Click here to retry" inside a paragraph of marketing.** A retry button is a button. It is labeled "Retry."
- **Errors that disappear on their own.** A self-dismissing error is an error the user cannot read.
- **Errors that require a page reload to recover.** Recovery is in the page.
- **Errors that hide the audit footer.** The audit footer is always visible, even on errors.

### 7.4 Error → audit integration

Every error, including client-side JS errors, produces a structured audit entry. The entry includes:

- The error category (validation, network, server, unhandled)
- The endpoint or component that produced the error
- A correlation ID (the same one shown to the user)
- The user role and institution
- The model version (where applicable)
- A timestamp

The user sees the correlation ID. The support team can query the audit log by it. The borrower never sees this infrastructure.

---

## 8. Loading States

The product has no spinners. There is no spinning wheel, no pulsing dot, no skeleton screen. Loading is a typographic statement of what is happening.

### 8.1 Loading state principles

1. **Loading is honest.** The product says what it is waiting for.
2. **Loading is static.** Loading states do not animate. If a state changes, the new state is rendered. If the state has not changed, the page is not moving.
3. **Loading is bounded.** Every loading state has a maximum wait time, after which an error state is shown.
4. **Loading is non-blocking where possible.** The audit footer is always rendered. The applicant identity is always rendered. The verdict slot is always rendered (as `—` if unknown).
5. **Loading is not a marketing moment.** No "We're working hard for you" copy. No skeletons. No progress bars that look like they're animating.

### 8.2 Loading state catalog

| Loading scenario | Treatment |
|---|---|
| Submitting a form | The submit button label changes to "Submitting…" and the button is disabled. The form is not cleared. No spinner. |
| Loading the decision spine (after submit) | The verdict slot shows "—". The rest of the page shows a `LoadingCounter` with the current step: "Validating inputs…", "Running model…", "Computing confidence interval…", "Finalizing…" The audit footer is rendered. |
| Loading the full breakdown | A `DomainSection` shows "Loading 4 of 7 signals…" inside it. The other sections render in their empty state. |
| Loading the history list | The list area shows "Loading assessments from 2026-01-01 to 2026-06-06…" with the date range from the URL. The filter bar is interactive even during loading. |
| Loading the report PDF | The report modal route shows a `LoadingCounter` and a "Cancel" button. The audit footer is rendered. Maximum wait: 30 seconds. After 30 seconds, an error state is shown. |
| Loading a comparison | Each side renders independently. Each shows its own loading state. The page does not block on the second. |
| Loading any single component (e.g., `DomainSection` expand) | The component shows "Loading…" in mono, in the same place its content would go. The page is not blocked. |
| Reconnecting after network loss | `ConnectionIndicator` shows "Reconnecting…" The current page state is preserved. |

### 8.3 Forbidden loading patterns

- **Spinners.** No spinning anything. No pulsing dots. No circular progress indicators.
- **Skeleton screens.** They look like content. They lie about what's loaded.
- **"Loading…" with no context.** If the page can say what it's loading, the page must say it.
- **Blocking overlays that prevent navigation.** A loading state that prevents the user from going back is a loading state that is also a trap.
- **Loading states that hide the audit footer.** The footer renders on the server or in static form. It is never "loading."
- **Loading states that change copy over time ("Step 1…" → "Step 2…") without the state actually changing.** This is fake progress.
- **Loading animations longer than 800ms total.** If a real operation takes longer than 800ms, it is a long operation and the product must show a different state (e.g., a back-end job).

### 8.4 Loading time budgets

| Operation | Budget |
|---|---|
| Sign-in | 1.5s |
| Form submit → first byte | 2.0s |
| Decision spine render | 4.0s (full breakdown may continue loading after this) |
| Full breakdown lazy load | 3.0s |
| Report PDF generation | 5.0s (PDF download stream begins by 2.0s) |
| History list first page | 1.0s |
| History list next page | 1.0s |
| Comparison view | 2.0s per side |
| Search (Cmd-K) | 200ms (local), 1.0s (remote) |

Operations exceeding their budget emit a performance audit event. The product's own performance is monitored by the product's own audit log.

---

## 9. Empty States

Empty states are not apologies. They are not illustrations. They are not invitations to "get started." They are statements of what is missing and what to do about it.

### 9.1 Empty state principles

1. **Empty states are not onboarding.** The product does not onboard. The product opens.
2. **Empty states are typographic.** A short statement of what is empty. A short statement of what to do.
3. **Empty states are non-judgmental.** They do not say "No assessments yet — let's create your first one!" They say "No assessments in this date range. Adjust the filters or run a new assessment."
4. **Empty states preserve the page shell.** The audit footer renders on every empty state. The top bar renders. The left rail renders.

### 9.2 Empty state catalog

| Empty state | Treatment |
|---|---|
| No assessments in history (first use) | "No assessments yet." + "Run a new assessment" link. |
| No assessments matching filters | "No assessments match these filters." + "Clear filters" button. The filter bar remains visible and populated. |
| No comparison selected (user navigates to /history/compare without IDs) | "Choose two assessments to compare." + "Open history" link. |
| No settings to display (e.g., MFI flag not set, batch page is empty) | "Batch assessment is not enabled for your role." + "Contact your institution administrator" link. |
| Sign-in form submitted with empty fields | Inline validation errors on the fields. No "empty state" page. |
| Report generation: assessment has no eligible report | "A report cannot be generated for this assessment." + back link. |
| Search (Cmd-K) with no results | "No results for 'q'. Try a different name or ID." |
| History with a single assessment (compare disabled) | Compare is not shown in the navigation. The page does not show an empty state for a feature that is not available. |

### 9.3 Forbidden empty state patterns

- **Illustrations of people looking confused or holding magnifying glasses.** Illustrations of confusion are not useful. They are condescending.
- **"Oops, nothing here yet!"** "Oops" is not a sentence.
- **"Looks like you're new here!"** The product does not notice when users are new.
- **Onboarding modals with "Got it!" buttons.** "Got it" is a vacuous acknowledgment.
- **Empty states that say "Click here to add your first X."** The empty state is a result, not a prompt.
- **Empty states with marketing copy.** "RiskIntel helps you make better decisions. Get started by…" The product is not a salesperson.

---

## 10. Mobile Adaptations

The product is desktop-first. Mobile is supported as a read-mostly companion for the field officer in transit, the analyst reviewing a decision on a tablet between meetings, and the MFI manager checking history on a phone. Mobile is not a primary surface; the design does not pretend it is.

### 10.1 Mobile adaptation principles

1. **The decision spine is the mobile screen.** Everything else is a degraded form of it.
2. **Mobile is read-mostly.** Form input on mobile is permitted but not optimized for long-form data entry. The product encourages tablet or desktop for new assessments.
3. **Mobile is offline-tolerant.** A history row, once loaded, is cached locally and accessible offline.
4. **Mobile is one-handed.** The primary actions are reachable with the thumb. The audit footer is reachable with one tap from anywhere.

### 10.2 Breakpoints

| Breakpoint | Range | Target |
|---|---|---|
| Mobile (portrait) | 0 – 639px | Phone, primary |
| Mobile (landscape) | 640 – 767px | Phone, secondary |
| Tablet | 768 – 1023px | Tablet, primary |
| Desktop | 1024 – 1439px | Desktop, primary |
| Wide | 1440px+ | Desktop, large |

The breakpoints are inclusive of the lower bound. They are not "mobile first" — they are desktop first, with mobile as a deliberate adaptation.

### 10.3 Per-component adaptations

#### 10.3.1 `AppShell`

- **Desktop:** Top bar (56px) + left rail (240px) + content + audit footer.
- **Tablet:** Top bar (56px) + content + audit footer. Left rail becomes a hamburger drawer.
- **Mobile:** Top bar (48px) + content + bottom bar (56px) + audit footer. The bottom bar holds section navigation.

#### 10.3.2 `DecisionSpine`

- **Desktop:** Verdict at 44pt display. Top drivers in 3-column grid. Full breakdown in expandable domain groups at full width.
- **Tablet:** Verdict at 30pt. Top drivers in 2-column grid. Full breakdown at full width.
- **Mobile:** Verdict at 30pt. Top drivers stacked, single column. Full breakdown uses horizontal-scroll tables (with a "scroll for more" affordance at the right edge, in mono).

The verdict is **always** the largest type on the page, on every breakpoint. No breakpoint may shrink the verdict below 30pt.

#### 10.3.3 `IntakeForm`

- **Desktop:** Two-column where appropriate. Form is on the left, hints and field-level explanations on the right.
- **Tablet:** Two-column where appropriate. Hints collapse into inline disclosure components.
- **Mobile:** Single column. Numeric input uses the native number keyboard. Date input uses the native date picker. File input is hidden (mobile intake does not support file upload in v1).

The intake form on mobile is intentionally heavier to discourage use. The product is honest: new assessments belong on desktop.

#### 10.3.4 `BreakdownTable`

- **Desktop:** Full table visible. All columns. Sortable.
- **Tablet:** Full table visible. Horizontal scroll if needed.
- **Mobile:** Horizontal scroll. Sticky first column (the field name). Other columns scroll. A "scroll for more" affordance is shown at the right edge.

The sticky first column is non-negotiable. Without it, the officer cannot read the table.

#### 10.3.5 `AuditFooter`

- **Desktop:** Three columns. Model lineage, version info, correlation ID.
- **Tablet:** Two columns. Correlation ID moves to a second row.
- **Mobile:** Single column, stacked. Each row in mono, 12pt equivalent. The correlation ID is at the bottom, larger than the rest, for copyability.

The audit footer is **always** rendered. It is never hidden on mobile, never collapsed behind a tap, never replaced with a "show more" link. It is the product's promise to the borrower and the regulator.

#### 10.3.6 `TopBar`

- **Desktop:** Product name (left), section name (center), user identity (right).
- **Tablet:** Product name (left), user identity (right). Section name is shown in the breadcrumb.
- **Mobile:** Product monogram (left), connection indicator (right). Section name is in the breadcrumb.

#### 10.3.7 `LeftRail` / `BottomBar`

- **Desktop:** Left rail, 240px, persistent.
- **Tablet:** Hamburger drawer, slides in from the left at 320ms. Backdrop is 60% black.
- **Mobile:** Bottom bar, 56px, persistent. The five items are reduced to four: New, History, Settings, Sign out. Compare is moved to a long-press on a history row.

#### 10.3.8 `CommandPalette`

- **Desktop:** Centered modal, 640px wide.
- **Tablet:** Centered modal, 80% width.
- **Mobile:** Full-screen sheet. Slides up from the bottom at 200ms.

#### 10.3.9 `EscalationPanel`

- **Desktop:** Right-side panel, 480px wide. Slides in from the right.
- **Tablet:** Right-side panel, 60% width.
- **Mobile:** Full-screen modal route. The user navigates back to return to the decision spine.

#### 10.3.10 Touch targets

Every interactive element on mobile and tablet is at minimum 44×44px. The product does not honor the iOS-recommended 44pt exactly, because the design brief uses a metric system; the conversion is exact: 44pt = 14.7mm = 56px. All touch targets are **56×56px minimum** on mobile and tablet.

### 10.4 Mobile-specific interactions

| Interaction | Mobile behavior |
|---|---|
| Pull-to-refresh | Disabled. The product does not refresh on pull. Refresh is a button in the top bar. |
| Swipe-to-delete | Disabled. Deletion is not supported in v1. |
| Long-press | Opens context menu. Used for the "Compare" affordance on history rows. |
| Pinch-to-zoom | Disabled on intake forms. Enabled on decision spine and breakdown (the officer may need to zoom in on a specific number). |
| Haptic feedback | Disabled. The product does not vibrate the device. |
| Native share sheet | Enabled on report PDFs. The "Share" button uses the OS share sheet. |
| Voice input | Disabled in v1. The product does not transcribe voice. |

### 10.5 Mobile network resilience

The product is built for 2G, 3G, and intermittent connections in rural India.

- **First-paint budget:** 1.5s on 3G, 4.0s on 2G.
- **Critical path payload:** the verdict, the audit footer, and the applicant identity, server-rendered or cached locally. Total: ~14KB gzipped.
- **Full breakdown lazy load:** triggered on scroll, not on page load. If the user never scrolls, the breakdown is never loaded.
- **History list:** cursor-paginated, 20 rows per page. First page renders with the page shell. Subsequent pages load on tap.
- **Offline mode:** when the network is down, the history list shows the most recent 50 cached rows with a `Tag` "Cached — last synced [timestamp]." New assessments are disabled. The submit button is replaced with "Reconnecting…" text.

### 10.6 Mobile adaptations — what is **not** adapted

The following are **not** adapted for mobile in v1. They are desktop-only, and the mobile UI shows a typographic "Available on desktop" message with a copy-to-clipboard link to the assessment's desktop URL.

- Batch CSV upload
- Settings → Defaults → Model version override
- Settings → Batch
- Comparison view (read-only on mobile, full interactivity on desktop)

The product is honest about its mobile capabilities. It does not fake a feature.

---

## 11. API Contract Surface (Frontend View)

The frontend's view of the backend is the typed API contract. The contract is enforced by generated types from the OpenAPI schema. The frontend never reaches into the backend's internals.

### 11.1 Endpoints consumed

| Method | Path | Purpose | Used by |
|---|---|---|---|
| POST | `/api/assess` | Unified assessment gateway | `DecisionSpine` (unified entry) |
| POST | `/api/assess/person-a` | Person A assessment | `DecisionSpine` (Person A path) |
| POST | `/api/assess/person-b` | Person B assessment | `DecisionSpine` (Person B path) |
| POST | `/api/report/generate` | Generate report PDF | `ReportPanel` |
| GET | `/api/report/download/{report_id}` | Download report PDF | `ReportPanel` |

### 11.2 Endpoints assumed (for full feature set)

The following endpoints are not in the frozen backend list but are required for the full architecture. They are listed here so that future backend work is scoped; their absence does not block the v1 frontend build because the affected screens degrade to their empty state.

| Method | Path | Purpose | Degraded state |
|---|---|---|---|
| GET | `/api/assessments/{id}` | Fetch a specific assessment for history navigation | History → Assessment navigation shows "Could not load assessment." |
| GET | `/api/assessments?from=&to=&type=&verdict=` | List assessments for history | History shows "Could not load history." |
| GET | `/api/me` | Current user profile | Settings page shows "Could not load profile." |
| GET | `/api/me/preferences` | User preferences | Settings → Defaults shows "Could not load preferences." |
| POST | `/api/escalations` | Submit escalation | Escalation panel shows error toast. |
| GET | `/api/assessments/batch/{job_id}` | Poll batch job | Batch page shows "Could not load job status." |
| POST | `/api/assessments/batch` | Submit batch CSV | Batch page shows "Could not submit batch." |
| GET | `/api/status` | Service status | `/status` page shows cached status. |

### 11.3 Type generation

The frontend generates TypeScript types from the backend's OpenAPI schema. The types are generated at build time and committed. Manual types are forbidden. A type that does not match the backend is a build error, not a runtime warning.

### 11.4 Error envelope contract

The backend's frozen error envelope is:

```ts
type ErrorEnvelope = {
  status: "error";
  error: {
    code: string;
    message: string;
    details?: Array<{
      engine?: string;
      error_type?: string;
      context?: string;
      field?: string;
    }>;
  };
};
```

The frontend's error handling is built around this shape. Any deviation is a contract violation, surfaced to the user as a generic 500 with the correlation ID.

---

## 12. Frontend Stack (recommended)

The following stack is recommended. The architecture is stack-agnostic in principle, but this stack best matches the design brief's principles.

| Layer | Recommendation | Rationale |
|---|---|---|
| Framework | React 18+ (or SolidJS as an alternative) | Mature, accessible, designer-friendly, ecosystem. |
| Routing | TanStack Router | Type-safe, file-based, URL-as-state. |
| State | TanStack Query (server state) + Zustand (client state) | Server state belongs to the cache. Client state is small. |
| Forms | React Hook Form + Zod | Performance, type-safe validation. |
| Styling | Vanilla CSS with design tokens, or CSS Modules | No utility framework. Tokens drive consistency. |
| Type generation | openapi-typescript | Generated types from backend OpenAPI. |
| Testing | Playwright (e2e) + Vitest (unit) + Testing Library (component) | The product's tests are tests of the user, not the implementation. |
| Linting | ESLint + Prettier + Stylelint | The design system has rules. The rules are enforced. |
| Build | Vite | Fast, type-safe, modern. |
| CI | GitHub Actions | Standard. |

**Explicitly rejected:**
- Tailwind CSS. Utility classes erode the design system.
- Material UI, Chakra, Ant Design, Mantine. Component libraries impose an aesthetic.
- Framer Motion. Animations are feedback, not entertainment.
- Storybook for documentation (Storybook is permitted for component development but not for design review).
- A state management library larger than Zustand. The product is not a state machine.

---

## 13. Performance Budgets

Performance is a design principle, not an engineering afterthought. The frontend's performance budgets are part of the architecture.

| Metric | Budget |
|---|---|
| First Contentful Paint (desktop) | 1.0s |
| First Contentful Paint (mobile, 3G) | 2.0s |
| Largest Contentful Paint (desktop) | 1.5s |
| Largest Contentful Paint (mobile, 3G) | 3.0s |
| Time to Interactive (desktop) | 2.0s |
| Time to Interactive (mobile, 3G) | 4.0s |
| Cumulative Layout Shift | 0.00 |
| Total Blocking Time | 100ms |
| Critical-path JS payload | 80KB gzipped |
| Critical-path CSS payload | 25KB gzipped |
| Initial route HTML | 30KB gzipped |
| Full app JS payload (lazy-loaded) | 300KB gzipped |
| Decision spine render time (after API response) | 200ms |
| Input latency (form typing) | 16ms (one frame) |

Performance regressions above the budget are build errors. The CI gate enforces them via Lighthouse CI.

---

## 14. Accessibility (WCAG 2.2 AA)

The product is built to WCAG 2.2 AA. AA is the floor. AAA is the target where it does not conflict with the design brief.

| Area | Standard |
|---|---|
| Color contrast | Body text 7:1, large text 4.5:1. Decorative elements excluded. |
| Keyboard navigation | Full keyboard support. See §4.6. |
| Screen reader | Semantic HTML. ARIA only when HTML cannot express. Live regions for the connection indicator. |
| Focus management | Visible focus rings (2px `--accent`). Focus trapping in modal routes. |
| Motion | Respects `prefers-reduced-motion`. Animations are removed; state changes are instant. |
| Touch targets | 56×56px minimum on touch devices. |
| Forms | Labels are always visible. Errors are associated with fields via `aria-describedby`. |
| Language | The `lang` attribute is set on the root and on any embedded foreign-language content. |
| Audio | No audio in v1. |
| Video | No video in v1. |

Accessibility regressions above AA are build errors. The CI gate enforces them via axe-core.

---

## 15. Internationalization (i18n)

The product is built for English (India) in v1. The architecture is i18n-ready, but only one locale is shipped.

- All strings are externalized. No hardcoded English in components.
- Date formatting uses `Intl.DateTimeFormat` with the user's locale.
- Number formatting uses `Intl.NumberFormat` with the user's locale.
- Currency formatting uses `Intl.NumberFormat` with the user's locale and the `INR` currency.
- Right-to-left support is a future architecture, not a v1 requirement.
- The product's voice, vocabulary, and sentence structure are designed for English (India) professional usage. Translation is a future architectural concern.

---

## 16. Testing Strategy

The product's tests are tests of the user, not of the implementation. The test pyramid is inverted from the convention: more e2e tests than unit tests.

| Layer | Coverage target | Tool |
|---|---|---|
| E2E (user journeys) | 100% of primary flows, 50% of secondary flows | Playwright |
| Component (visual regression) | 100% of atoms and molecules, 50% of organisms | Chromatic or Playwright snapshots |
| Unit (logic) | 80% of non-trivial utility code | Vitest |
| Integration (API contract) | 100% of API endpoints consumed | openapi-typescript + contract tests |
| Accessibility | 100% of routes | axe-core + Playwright |
| Performance | 100% of primary routes | Lighthouse CI |
| Visual design review | 100% of new components | Figma + Chromatic |

Every primary user flow has at least one e2e test. The e2e tests are the **definition of done** for a feature. A feature without a passing e2e test is not shipped.

---

## 17. Open Questions for the Team

These questions remain open as of v1.0. They are listed so the build does not silently make the wrong decision.

1. **Should the comparison view be available to all roles, or only to credit analysts?** Currently scoped to credit analyst and senior loan officer. The decision affects permissions and routing.
2. **Should the settings → model version override be allowed for all users, or only for institutional admins?** Currently hidden behind a disclosure for non-admins. The decision affects who can break production.
3. **What is the policy on assessment deletion?** Currently out of scope (no UI for it). The decision affects the audit log and the institution's compliance posture.
4. **Is the "Escalate" action a real workflow, or a stub?** Currently stubbed locally with optimistic UI. The decision affects whether to ship the escalation backend in v1.
5. **Should batch CSV upload support file formats other than CSV?** Currently CSV only. The decision affects the parser, the validation, and the error states.
6. **What is the policy on institution-level model version pinning?** Currently per-user, in settings → defaults. The decision affects whether to ship an institution admin console in v1.

Each question is resolved before the affected feature ships. The architecture is built to be patient about these questions: the screens for the affected features degrade to empty states until the questions are resolved.

---

## 18. Sign-off

This architecture is frozen for build. Any change to the architecture is a design decision and must be made by the Principal Product Designer and the Frontend Architecture Lead, with review by the Senior UX Researcher and the Fintech Design Lead. Architecture changes are recorded in `ARCHITECTURE_CHANGELOG.md`.

The architecture is reviewed at the end of each milestone. A review is triggered by:
- A new user segment entering the product
- A new backend endpoint becoming available
- A pattern in production errors that the architecture did not anticipate
- A drift in shipped code that the architecture was meant to prevent
- A change in regulatory or compliance environment
