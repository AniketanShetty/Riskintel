# RiskIntel — Frontend Architecture v1.1

**Status:** Frozen for build
**Supersedes:** `FRONTEND_ARCHITECTURE.md` v1.0
**Inherits:** `DESIGN_BRIEF.md` v1.0
**Author:** Final Frontend Architect
**Reconciliation source:** `DESIGN_CRITIQUE.md` v1.0

---

## 0. Reconciliation Decisions

Every critique item evaluated against six filters: user workflow efficiency, enterprise software usability, accessibility, scalability, maintainability, Editorial Finance alignment. Decisions are final. Each entry is binding on the build.

### 0.1 Modifications

| ID     | Decision | Title |
|--------|----------|-------|
| M1     | **MODIFY** | Replace Left Rail |
| M2     | **ACCEPT** | Decision Spine Layout Specification |
| M3     | **ACCEPT** | Complete Keyboard Model |
| M4     | **ACCEPT** | Audit Footer Accessibility Fix |
| M5     | **MODIFY** | Replace Cmd-K With Search Field |
| M6     | **ACCEPT** | Empty States as One Line |
| M7     | **MODIFY** | History As Reading List With Filters |
| M8     | **ACCEPT** | No Optimistic UI For Consequential Actions |
| M9     | **REJECT** | Merge Drivers + Recommendations |
| M10    | **ACCEPT** | Type Selector As Text Links |
| M11    | **MODIFY** | Mobile Bottom Bar Removal |
| M12    | **ACCEPT** | Remove "Available On Desktop" Pattern |
| M13    | **REJECT** | Move Confidence Below Breakdown |
| M14    | **ACCEPT** | Metadata Strip In Applicant Identity |
| M15    | **ACCEPT** | Privacy Mode For Applicant Identity |
| M16    | **MODIFY** | History Scope Default |
| M17    | **ACCEPT** | Mobile Breakdown As Stacked List |
| M18    | **ACCEPT** | Non-Color Signals On Contribution Chart |
| M19    | **ACCEPT** | Driver List As List Not Cards |
| M20    | **MODIFY** | Settings Navigation Restructure |
| M21    | **ACCEPT** | Batch Polling At 5 Seconds |
| M22    | **ACCEPT** | Resolve Open Questions For V1 |

### 0.2 Per-Item Reasoning

#### M1 — Replace Left Rail — **MODIFY**

**Reasoning:** Full removal breaks enterprise usability. Officers trained on rail-based navigation lose orientation. A 240px persistent rail is correct for desktop. The critique's complaint is about content, not presence. **Decision:** Keep the rail, but reduce its visual weight (32px collapsed micro-rail at left edge, expanding to 200px on hover or focus), and remove the redundant section name from the top bar. The rail is contextual: items shown depend on the current section, but the rail itself persists.

**User impact:** Officers keep a persistent orientation surface. The rail shrinks visual weight from 240px to 32px when not in use, freeing 208px for content. The product stops looking like Salesforce.

**Engineering impact:** Existing `LeftRail` component retained. `TopBar` simplified (no section name). ~12 hours of design + ~16 hours of frontend.

#### M2 — Decision Spine Layout Specification — **ACCEPT**

**Reasoning:** Two engineers building the same screen from prose-only specs is a known failure mode. Layout grid is required. The brief's "8px baseline" is necessary but insufficient. **Decision:** Add §3.5.1 with full grid, gutter, type assignment, and vertical rhythm specification.

**User impact:** Consistent decision spine across implementations. Verdict is the largest type on every screen. Hierarchy is not subject to engineer interpretation.

**Engineering impact:** One new section. ~6 hours of design + ~16 hours of frontend. No backend change.

#### M3 — Complete Keyboard Model — **ACCEPT**

**Reasoning:** A keyboard model that omits arrow keys, skip links, focus restoration, and error announcement is not a keyboard model. AA accessibility is a hard requirement (DESIGN_BRIEF §4.4). **Decision:** Expand §4.6 with arrow keys, skip links, focus restoration, error announcement, in-page anchor keyboard model.

**User impact:** Keyboard-only and screen-reader users can navigate the product. Form errors are announced. Modals restore focus correctly.

**Engineering impact:** §4.6 rewrite. ~4 hours of design + ~16 hours of frontend.

#### M4 — Audit Footer Accessibility Fix — **ACCEPT**

**Reasoning:** The audit footer at 12pt mono 60% alpha is 4.2:1, below the AA 4.5:1 standard. The product's most defensible content fails its own accessibility floor. **Decision:** Audit footer becomes 14pt mono, 80% alpha, on `--paper`. Result ~5.4:1.

**User impact:** Low-vision users can read the audit footer. The product's most important content is the most readable.

**Engineering impact:** §10.3.5 + §14 update. ~2 hours of design + ~4 hours of frontend.

#### M5 — Replace Cmd-K With Search Field — **MODIFY**

**Reasoning:** Cmd-K is a 2022 cliché. But a top-bar search field without a shortcut is undiscoverable. The fix is to remove the modal-palette pattern and keep a shortcut for power users. **Decision:** Search field in the breadcrumb area, top-right. Keyboard shortcut: `/` (the documentation convention, not the chat-app convention). Cmd-K is removed.

**User impact:** Search is discoverable (visible in the chrome) and fast (keyboard). No modal appears; results render in a dropdown under the field.

**Engineering impact:** `CommandPalette` deleted. New `SearchField` component. ~4 hours of design + ~12 hours of frontend.

#### M6 — Empty States As One Line — **ACCEPT**

**Reasoning:** Paragraph empty states are LLM-trained filler. The brief is anti-empty-state-marker; the architecture contradicts itself. **Decision:** Each empty state is one line in 17pt body, with a single text link if needed. Two lines maximum.

**User impact:** Empty states occupy proportional visual real estate. The product's anti-marketing stance is consistent.

**Engineering impact:** §9.2 update. ~2 hours of design + ~4 hours of frontend.

#### M7 — History As Reading List — **MODIFY**

**Reasoning:** A pure reading list (no filters, no table) breaks enterprise usability. Loan officers and analysts do filter by date, type, verdict, and applicant name. The reading list is the default rendering; filters are a power-user affordance. **Decision:** History renders as a chronological reading list by default. Filters are exposed via a **filter disclosure** (a single "Filter" text link at the top of the list) that expands inline to show date range, type, verdict, applicant name. Not a persistent filter bar. Not a separate page.

**User impact:** Default reading-list experience for browsing. Filter disclosure for targeted search. No dashboard chrome. No filter bar in the way.

**Engineering impact:** `FilterBar` deleted. `HistoryList` + `HistoryItem` (new). Filter disclosure component. ~10 hours of design + ~24 hours of frontend.

#### M8 — No Optimistic UI For Consequential Actions — **ACCEPT**

**Reasoning:** Optimistic UI on escalation, approval, decline, or any action producing an audit log entry is dangerous. The officer thinks the action completed; the audit log disagrees. **Decision:** All consequential actions show a "Submitting…" state until the server confirms. Server errors are surfaced inline; the action is not "completed."

**User impact:** Officers never believe an action completed when it did not. The audit log is the source of truth.

**Engineering impact:** §1.4 + §11.2 update. ~2 hours of design + ~4 hours of frontend.

#### M9 — Merge Drivers + Recommendations — **REJECT**

**Reasoning:** Drivers and recommendations are conceptually distinct. A driver explains the verdict. A recommendation is an action. An officer who reads the drivers knows *why*; an officer who reads the recommendations knows *what to do*. Merging them in the UI conflates two decisions. The critique is correct that there is overlap; the resolution is to make them **visually adjacent but semantically distinct**, not to merge them.

**Decision:** Drivers and recommendations remain two separate content blocks. Drivers render first (ranked list with contribution bars). Recommendations render immediately below, separated by a hairline and a label ("What to do"). The label is typographic, 14pt mono, 60% alpha. Officers read both without confusion.

**User impact:** Clear separation of mechanism and action. The product maintains editorial-finance's information density without collapsing categories.

**Engineering impact:** No change. Drivers and recommendations remain separate. ~2 hours of design for the typographic label. ~4 hours of frontend for the label rendering.

#### M10 — Type Selector As Text Links — **ACCEPT**

**Reasoning:** Two cards side by side is a card pattern. A typographic two-link row is not. The first screen the officer sees should not look like a card grid. **Decision:** `/assess/new` is a single row of two text links, display 30pt, separated by a hairline. Each link has a one-line description in 15pt body.

**User impact:** The first interaction is reading, not card selection. The product's differentiator is visible from the first click.

**Engineering impact:** `IntakeTypeSelector` organism rewritten. ~2 hours of design + ~4 hours of frontend.

#### M11 — Mobile Bottom Bar Removal — **MODIFY**

**Reasoning:** Full removal of the bottom bar breaks enterprise mobile navigation. Loan officers and MFI field staff need persistent access to History and New Assessment. The critique's complaint is that the bottom bar steals the verdict's space on the decision spine. **Decision:** The bottom bar is **conditional**. It auto-hides on scroll-down and re-appears on scroll-up **on the decision spine only**. On all other routes, it persists. The bar is 40px (not 56px) with 56×56px tappable regions. Section nav on mobile is also reachable from the top bar's user-identity dropdown (one tap from anywhere).

**User impact:** Decision spine gets full viewport when reading. Other routes keep persistent navigation. Officers in the field keep one-tap access to History.

**Engineering impact:** `BottomBar` retained with conditional visibility on `/assess/{id}`. ~6 hours of design + ~12 hours of frontend.

#### M12 — Remove "Available On Desktop" Pattern — **ACCEPT**

**Reasoning:** The pattern is condescending and tells the user the product does not work for them. The product either ships the feature on mobile or does not ship it. **Decision:** Pattern removed. For each feature in the v1.0 list (§10.6), the architecture commits to mobile-build or deferral.

**User impact:** No "go away" messages. Users see either a working feature or a feature that is not in the product.

**Engineering impact:** §10.6 update. ~2 hours of design + ~4 hours of frontend.

#### M13 — Move Confidence Below Breakdown — **REJECT**

**Reasoning:** The confidence frame (band + probability range + override flags) is part of the verdict. The officer needs to know "Moderately Ready, 68% probability" at a glance, not after scrolling past the breakdown. The override flags (E5 floor breach, P4 rejection) are consequential and must be visible at the verdict. The probability range is dense, but in mono type at 14pt it occupies 1 line. The critique confuses the hero area with cognitive load.

**Decision:** Confidence frame remains in the hero area, below the verdict, above the drivers. Rendered in 14pt mono, single line: `68% probability, range 61–74%`. Override flags are `Tag` components on the same line.

**User impact:** Officer sees the verdict and its confidence at a glance. Override flags are immediately visible.

**Engineering impact:** No change. §3.5 stands as written.

#### M14 — Metadata Strip In Applicant Identity — **ACCEPT**

**Reasoning:** The audit footer at the page bottom is below the fold on long decision spines. The officer needs metadata (timestamp, model version, correlation ID) within the first viewport. **Decision:** A metadata strip in the applicant identity block, top of decision spine, 14pt mono, contains timestamp, model version, decision version, schema version, correlation ID (truncated). Full versions on hover. Correlation ID is copyable on hover.

**User impact:** Audit metadata is in the first viewport. Officers can copy the correlation ID in 2 seconds.

**Engineering impact:** New component `MetadataStrip`. ~3 hours of design + ~6 hours of frontend.

#### M15 — Privacy Mode For Applicant Identity — **ACCEPT**

**Reasoning:** Borrower PII is exposed by default in the applicant identity. Officers reviewing decisions in public spaces (regulator's office, branch, meeting) need a privacy mode. **Decision:** Privacy mode toggle in the top bar. When active: monogram instead of name, age band instead of age, business category instead of business, loan band instead of loan request. Correlation ID preserved.

**User impact:** Officers can defend a decision in any context without exposing the borrower.

**Engineering impact:** Privacy mode state, top-bar toggle, conditional rendering. ~4 hours of design + ~12 hours of frontend.

#### M16 — History Scope Default — **MODIFY**

**Reasoning:** Team-wide default is too restrictive. An analyst defending a decision in a review meeting needs to see the chief credit officer's decision. Institution-wide is the correct default for senior roles. **Decision:** History scope is **role-based**. Loan officers see their own. Senior loan officers see their team. Credit analysts and admins see institution-wide. The scope is shown in the breadcrumb area (`Your decisions` / `Team decisions` / `Institution decisions`). No toggle in v1.

**User impact:** Each role sees the appropriate scope. No "why does a junior see the chief's decisions" question.

**Engineering impact:** Role-based query parameter on `GET /api/assessments`. ~2 hours of design + ~8 hours of frontend. No backend change (assumes role-based filtering is added to the endpoint, which the architecture's §11.2 lists as assumed; if not, the frontend sends a user-id filter and the backend filters).

#### M17 — Mobile Breakdown As Stacked List — **ACCEPT**

**Reasoning:** Horizontal-scroll tables on mobile are hostile. The sticky-first-column trick does not work on a 375px phone. **Decision:** On mobile, the full breakdown is a stacked list. Each input is a row: field name (left, 50%), value (right, mono, right-aligned), contribution (below in 12pt). On tablet and desktop, the full table renders.

**User impact:** Officers can read the breakdown on a phone. The product is usable in the field.

**Engineering impact:** Responsive `BreakdownTable` with list rendering at <768px. ~4 hours of design + ~12 hours of frontend.

#### M18 — Non-Color Signals On Contribution Chart — **ACCEPT**

**Reasoning:** Color-only signals exclude colorblind users. WCAG 2.2 AA requires non-color signal alternatives. **Decision:** Largest positive and negative drivers are distinguished by position (top vs. bottom of ranked list), sign indicator in mono (`+`/`−`), and color (accent vs. oxblood). Three redundant signals; no single one is primary.

**User impact:** Colorblind users can read the contribution chart. All users benefit from the redundant signals.

**Engineering impact:** §6.2.1 update. ~2 hours of design + ~4 hours of frontend.

#### M19 — Driver List As List Not Cards — **ACCEPT**

**Reasoning:** Driver items in cards is a card grid. The brief forbids card soup. **Decision:** Drivers are a typographic list with hairlines between items. Each row: name (left, 50%), value (right, mono), contribution bar (full width, below the row). No backgrounds, no borders around individual items.

**User impact:** Drivers read as a list, not a grid. The product maintains its anti-card stance.

**Engineering impact:** `DriverItem` rendered as a row, not a card. ~3 hours of design + ~6 hours of frontend.

#### M20 — Settings Navigation Restructure — **MODIFY**

**Reasoning:** Full removal of Settings as a top-level nav item breaks enterprise usability. Officers expect to find account settings in a discoverable place. The critique is correct that three sub-routes is SaaS-pattern filler. **Decision:** Settings is a top-level nav item with **one page** containing three sections (Profile, Defaults, Security). No sub-routes. The "Settings" label remains. The three sections are typographic, separated by hairlines, not by tabs or sub-routes.

**User impact:** Settings is discoverable as a single page. The three sections are visible at once; officers do not navigate between sub-pages.

**Engineering impact:** `SettingsPage` rewritten. Sub-routes deleted. ~4 hours of design + ~8 hours of frontend.

#### M21 — Batch Polling At 5 Seconds — **ACCEPT**

**Reasoning:** 2s is too aggressive on 2G/3G. 5s is the engineering-defensible default. **Decision:** Batch polling is 5 seconds, with no adaptive behavior in v1.

**User impact:** Predictable. Documented. No implementation variance.

**Engineering impact:** §1.6 update. ~1 hour of design + ~2 hours of frontend.

#### M22 — Resolve Open Questions For V1 — **ACCEPT**

**Reasoning:** v1 cannot ship with stubbed features and undefined policies. **Decision:** All six open questions resolved in §17 of this document (see §14 of this v1.1).

**User impact:** No stubs, no undefined behavior.

**Engineering impact:** §17 update. ~2 hours of design. No frontend work.

### 0.3 Removals

| ID     | Decision | Title |
|--------|----------|-------|
| R1     | **DEFER** | Compare Two Assessments |
| R2     | **DEFER** | Escalation Feature |
| R3     | **DEFER** | Batch CSV Upload |
| R4     | **DEFER** | Model Version Override |
| R5     | **REMOVE** | Toast Component |
| R6     | **REMOVE** | HistoryTrend Sparkline |
| R7     | **REMOVE** | "Available On Desktop" Pattern |
| R8     | **ACCEPT** | Index Route Becomes Type Selector |
| R9     | **DEFER** | Sticky-Anchor Right Rail |
| R10    | **MODIFY** | Settings Stays As Nav Item (Per M20) |
| R11    | **DEFER** | `/legal/audit` Route |
| R12    | **DEFER** | `/status` Route |
| R13    | **DEFER** | Voice Input |

All removals and deferrals are documented in §14 of this v1.1. No code is written for deferred features.

---

## 1. Frontend State Architecture

### 1.1 Routing Strategy

**Library:** TanStack Router (file-based, type-safe).

**Route table (frozen):**

| Route | Component | Auth | Lazy |
|---|---|---|---|
| `/` | Redirect → `/assess/new` | Required | No |
| `/assess/new` | `TypeSelector` | Required | No |
| `/assess/person-a` | `PersonAIntake` | Required | Yes |
| `/assess/person-b` | `PersonBIntake` | Required | Yes |
| `/assess/$id` | `DecisionSpine` | Required | No |
| `/assess/$id/report` | `ReportPage` | Required | Yes |
| `/history` | `HistoryList` | Required | No |
| `/history/$id` | `DecisionSpine` | Required | Yes |
| `/settings` | `SettingsPage` | Required | Yes |
| `/auth/sign-in` | `SignIn` | Public | No |
| `/auth/forgot` | `Forgot` | Public | Yes |
| `/auth/locked` | `Locked` | Public | No |
| `/legal/terms` | `Legal` | Public | Yes |
| `/legal/privacy` | `Legal` | Public | Yes |
| `/404` | `NotFound` | Public | No |
| `/500` | `ServerError` | Public | No |

**Route guards:** `beforeLoad` checks session via `GET /api/me`. Redirect to `/auth/sign-in?from=$pathname` on 401. No global guard on `/auth/*` routes.

**Route state:** Filter state in URL query string (`?from=&to=&type=&verdict=&q=`). Form drafts not in URL (local storage, per §9.6). Privacy mode in `localStorage` (key: `riskintel:privacy-mode`), not in URL.

**Preloading:** Routes the user is likely to visit next are preloaded on hover. `DecisionSpine` is preloaded when the user opens the intake form. `HistoryList` is preloaded after the user submits their first assessment.

### 1.2 Query Strategy

**Library:** TanStack Query.

**Query keys (canonical):**

```ts
// Assessment
["assessment", id]
["assessments", { from, to, type, verdict, q, scope, cursor }]

// User
["me"]
["me", "preferences"]

// Reports
["report", id]

// Static
["legal", "terms"]
["legal", "privacy"]
```

**Stale times:**

| Query | `staleTime` | `gcTime` |
|---|---|---|
| `["assessment", id]` | Infinity (assessment is immutable once written) | 1h |
| `["assessments", ...]` | 30s | 5m |
| `["me"]` | 5m | 30m |
| `["me", "preferences"]` | 5m | 30m |
| `["report", id]` | Infinity | 1h |

**Mutation invalidation:**
- `POST /api/assess/person-a` and `POST /api/assess/person-b` invalidate `["assessments", ...]` (any scope) and prepend the new assessment to the active list.
- `POST /api/report/generate` does not invalidate any list. The report is not a queryable resource; it is a one-shot artifact.
- `PUT /api/me/preferences` invalidates `["me", "preferences"]` only.

**Optimistic updates:** **Forbidden** for any mutation that produces an audit log entry. Permitted only for: privacy mode toggle, filter disclosure expand/collapse, form draft saves.

### 1.3 Caching Strategy

**Three layers:**

1. **HTTP cache (TanStack Query).** Configured above. `staleTime` controls refetch on mount.
2. **Browser cache (Service Worker).** v1 ships with no Service Worker. The product's offline mode (§1.6) is degraded: the user sees the last-loaded page from the browser's bfcache, but the frontend does not actively cache assets. Service Worker is a v2 feature.
3. **Local storage.** Form drafts (`riskintel:draft:person-a:<userId>`, `riskintel:draft:person-b:<userId>`), privacy mode (`riskintel:privacy-mode`), and last 50 history rows for offline viewing (`riskintel:history-cache:<userId>`).

**No IndexedDB. No Redux Persist. No localStorage-based state management library.**

### 1.4 Error Boundaries

**Three error boundaries, mounted at three levels:**

1. **Root error boundary** (`App` level). Catches uncaught errors. Renders `ErrorPage` with the correlation ID. Sign-out link.
2. **Route error boundary** (per route, via TanStack Router's `errorComponent`). Catches route-load errors. Renders the route's error state per §10 (Error States). Preserves the parent route if possible.
3. **Component error boundary** (per organism, via `react-error-boundary`). Catches rendering errors in a single organism. Renders the organism's empty state with a "Reload component" link. The page shell remains functional.

**Every error boundary:**
- Emits a structured audit event to `POST /api/audit/client-error` (assumed endpoint, per §11 of the v1.0 architecture; if not available, the event is queued in localStorage and sent on next successful request).
- Displays the correlation ID. The user can copy it.
- Does not break the audit footer. The footer renders above the error fallback.

### 1.5 Form Architecture

**Library:** React Hook Form + Zod.

**Schema source:** Zod schemas are generated from the backend's OpenAPI types. The form schema is a strict superset of the API contract — additional fields (e.g., UI-only toggles) are allowed, but every field sent to the API is validated against the generated Zod schema.

**Validation:**
- **Field-level:** on blur. Errors render below the field in 14pt, `--negative`. The field border switches to `--negative`.
- **Form-level:** on submit. All field errors render. The first invalid field receives focus AND an `aria-live="assertive"` region announces the error count.
- **Server-side:** server validation errors are mapped to fields via the `error.details[].field` path. Unmapped errors render at the top of the form.

**Drafts:**
- On blur, the form state is serialized to localStorage, keyed by `riskintel:draft:<form-name>:<userId>`.
- Drafts are restored on form mount if the user has visited the form before and the draft is <24h old.
- Drafts are cleared on successful submit and on sign-out.
- Stale drafts (form schema changed) trigger a typographic "Form has changed. Start fresh or restore." message in the form header. The user chooses.

**Submission:**
- The submit button is disabled until the form is valid.
- On click, the button label changes to "Submitting…" and the button is disabled. The form is not cleared.
- On 2xx, the form is unmounted, the draft is cleared, and the user is navigated to the new assessment's decision spine.
- On 4xx, the form remains. Server errors render per §1.5 (server-side validation). Network errors render the `ConnectionIndicator` state and a typographic "Could not submit. Try again." message below the submit button.
- On 5xx, the form remains. A typographic "RiskIntel could not complete this request. [Correlation ID]" message renders. Retry button below.

### 1.6 Offline Behavior

**v1 offline mode is read-only, last-loaded-state.**

**Detection:** `navigator.onLine` + `window.addEventListener('offline'/'online')`. The `ConnectionIndicator` in the top bar reflects state.

**Online (default):**
- All routes function normally.
- Queries fetch fresh data per `staleTime`.
- Mutations are sent to the server.

**Offline:**
- The `ConnectionIndicator` shows "Offline — your work is saved." (top bar, 14pt mono).
- All forms are disabled. Submit buttons are replaced with "Reconnecting…" text.
- The history list shows the last 50 rows from `riskintel:history-cache:<userId>` with a `Tag` "Cached — last synced [ISO timestamp]."
- The decision spine shows the last-loaded assessment (bfcache or query cache) with a `Tag` "Cached."
- The intake forms (`/assess/person-a`, `/assess/person-b`) show a typographic message: "RiskIntel requires a connection to run a new assessment."
- No optimistic UI. No local-first writes. No conflict resolution. The product is honest about what it can and cannot do offline.

**Reconnect:**
- On `online` event, the `ConnectionIndicator` shows "Reconnecting…" for 2 seconds, then "Connected."
- Active queries are refetched in the background.
- The user does not need to reload.

---

## 2. Design Token System

All tokens are CSS custom properties on `:root`. Tokens are referenced by name in components. No hardcoded values. No utility classes. The token system is the only source of design truth.

### 2.1 Spacing Scale

| Token | Value | Usage |
|---|---|---|
| `--space-0` | 0 | Reset |
| `--space-1` | 4px | Hairline padding (tag internals) |
| `--space-2` | 8px | Tight padding (within a row) |
| `--space-3` | 16px | Default padding (within a block) |
| `--space-4` | 24px | Block-to-block gap (mobile) |
| `--space-5` | 32px | Block-to-block gap (desktop), container gutter |
| `--space-6` | 48px | Section gap (mobile) |
| `--space-7` | 64px | Section gap (desktop), vertical rhythm between major blocks |
| `--space-8` | 96px | Page-level outer margin (desktop) |
| `--space-9` | 128px | Hero padding (verdict top/bottom) |

**Usage rules:**
- `--space-1` to `--space-3`: within a component.
- `--space-4` to `--space-5`: between components in a section.
- `--space-6` to `--space-7`: between sections.
- `--space-8` to `--space-9`: page-level.
- No other values. If a value is not in the scale, the design is wrong.

### 2.2 Typography

**Type scale:**

| Token | Size | Line-height | Weight | Letter-spacing | Usage |
|---|---|---|---|---|---|
| `--type-display` | 44px | 52px | 500 | -0.5px | Verdict (desktop) |
| `--type-display-tablet` | 30px | 40px | 500 | -0.25px | Verdict (tablet) |
| `--type-display-mobile` | 30px | 40px | 500 | -0.25px | Verdict (mobile) |
| `--type-heading` | 30px | 40px | 500 | -0.25px | Section H2 (desktop) |
| `--type-subheading` | 22px | 32px | 500 | 0 | Section H3, applicant name |
| `--type-body-large` | 17px | 26px | 400 | 0 | Body large (empty states, lead paragraphs) |
| `--type-body` | 15px | 24px | 400 | 0 | Body default |
| `--type-body-small` | 14px | 22px | 400 | 0 | Body small (form field errors, footnotes) |
| `--type-data` | 14px | 22px | 500 | 0 | Tabular numerics, monetary values |
| `--type-data-small` | 12px | 18px | 500 | 0 | Audit metadata (with alpha adjustment per M4) |
| `--type-mono` | 14px | 22px | 400 | 0 | Code, IDs, technical metadata |
| `--type-mono-small` | 12px | 18px | 400 | 0 | Small mono (form labels, breadcrumb) |
| `--type-label` | 12px | 18px | 500 | 0.5px (uppercase) | Form field labels (mono) |

**Font families:**
- `--font-display`: serif (GT Sectra, Tiempos Headline, Source Serif 4)
- `--font-body`: humanist sans (Inter, GT America, Söhne)
- `--font-data`: tabular sans (Inter, IBM Plex Sans, Berkeley Mono)
- `--font-mono`: monospace (Berkeley Mono, JetBrains Mono)

**Font features:**
- All text: `font-feature-settings: 'kern', 'liga'`
- Numeric: `font-variant-numeric: tabular-nums` (in data components)
- Display: `font-feature-settings: 'kern', 'liga', 'dlig'`

**Usage rules:**
- Display type is reserved for the verdict and section H2.
- Body text is 15px, never 16px (the 16px default is forbidden).
- Data type is used for all monetary values, scores, probabilities, and counts.
- Mono type is used for IDs, timestamps, version strings, and form labels.
- The 12px size is permitted only for: form labels, audit metadata, footnotes, and contribution-bar subtext.

### 2.3 Z-Index Hierarchy

| Token | Value | Usage |
|---|---|---|
| `--z-base` | 0 | Default flow |
| `--z-sticky` | 10 | Sticky elements (top bar, metadata strip) |
| `--z-overlay` | 50 | Connection indicator toast |
| `--z-modal` | 100 | Modal route backdrop |
| `--z-modal-content` | 110 | Modal route content |
| `--z-tooltip` | 200 | Tooltips |
| `--z-skip-link` | 300 | Skip links (above everything) |

**Rules:**
- No element may use a z-index outside this scale.
- Stacking context is created by `position: relative; z-index: <token>`.
- Tooltips are the highest non-skip-link layer.

### 2.4 Motion Hierarchy

| Token | Value | Usage |
|---|---|---|
| `--motion-instant` | 0ms | `prefers-reduced-motion` fallback |
| `--motion-exit` | 120ms ease-in | State exits (modal close, dropdown close) |
| `--motion-enter` | 160ms ease-out | State entrances (modal open, dropdown open, page transition) |
| `--motion-emphasis` | 240ms ease-out | Verdict underline reveal (the only motion longer than 160ms) |

**Easing:**
- `ease-out`: `cubic-bezier(0, 0, 0.2, 1)` (CSS keyword)
- `ease-in`: `cubic-bezier(0.4, 0, 1, 1)` (CSS keyword)

**Usage rules:**
- No spring physics. No bounce. No parallax.
- No motion longer than 240ms.
- All transitions honor `prefers-reduced-motion: reduce` and become instant.
- The verdict underline reveal (240ms) is the only motion longer than 160ms. It is the product's only "emphasis" motion.
- State changes (hover, focus, active) transition in 120ms. No transition on the default state.

### 2.5 Focus Rings

| Token | Value | Usage |
|---|---|---|
| `--focus-ring-width` | 2px | All focus indicators |
| `--focus-ring-offset` | 2px | Distance between element and ring |
| `--focus-ring-color` | `var(--accent)` | Default focus color |
| `--focus-ring-color-on-accent` | `var(--ink)` | Focus on accent backgrounds (verdict) |

**Usage rules:**
- Every interactive element has a visible focus ring.
- Focus rings are 2px solid, 2px offset.
- On `--accent` backgrounds, the focus ring is `--ink` (the accent cannot be distinguished from the background).
- Focus rings are never removed. `:focus { outline: none }` is forbidden.
- Custom focus styling uses `outline: var(--focus-ring-width) solid var(--focus-ring-color); outline-offset: var(--focus-ring-offset)`.

### 2.6 Breakpoints

| Token | Min-width | Target |
|---|---|---|
| `--bp-mobile` | 0 | Phone, primary |
| `--bp-mobile-landscape` | 640px | Phone, landscape |
| `--bp-tablet` | 768px | Tablet, primary |
| `--bp-desktop` | 1024px | Desktop, primary |
| `--bp-wide` | 1440px | Desktop, large |

**Usage rules:**
- Breakpoints are inclusive of the lower bound.
- Mobile-first queries: `@media (min-width: 768px)`. The default styles are mobile.
- Content max-width: 1200px on desktop, 100% with 16–32px padding on mobile/tablet.
- The audit footer breaks out of the content container at all breakpoints (full width).

### 2.7 Color Tokens

(Frozen from DESIGN_BRIEF.md §2. Re-stated for completeness.)

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#0E1217` | Primary text, structure |
| `--paper` | `#F7F5F0` | Background |
| `--rule` | `rgba(31, 41, 55, 0.12)` | Hairline dividers |
| `--rule-strong` | `rgba(31, 41, 55, 0.24)` | Strong hairlines |
| `--accent` | `#9A5A1F` | Decision accent (≤8% of any screen) |
| `--positive` | `#2F6B4A` | "Ready" verdicts (reserved) |
| `--negative` | `#8B2E2A` | "Not Ready" verdicts, error text |
| `--ink-80` | `rgba(14, 18, 23, 0.80)` | Audit metadata, high-density mono |
| `--ink-60` | `rgba(14, 18, 23, 0.60)` | Secondary text, empty states, labels |
| `--ink-40` | `rgba(14, 18, 23, 0.40)` | Tertiary text, disabled state |
| `--ink-12` | `rgba(14, 18, 23, 0.12)` | Hairlines |
| `--ink-8` | `rgba(14, 18, 23, 0.08)` | Track backgrounds (probability range) |

---

## 3. Accessibility Contract

### 3.1 WCAG Requirements

**Standard:** WCAG 2.2 AA, with AAA where it does not conflict with the brief.

| Area | Standard |
|---|---|
| Color contrast (body) | 7:1 (AAA) |
| Color contrast (large text) | 4.5:1 (AAA) |
| Color contrast (non-text UI) | 3:1 (AA) |
| Keyboard navigation | Full support, all interactive elements |
| Focus visible | 2px solid, 2px offset, ≥3:1 contrast |
| Touch targets | 56×56px minimum |
| Motion | Honors `prefers-reduced-motion` |
| Audio | None in v1 |
| Video | None in v1 |
| Language | `lang` attribute on root, `dir` attribute set |
| Form labels | Always visible, associated via `for`/`id` |
| Error identification | Errors identified in text, associated with fields via `aria-describedby` |

**Enforcement:** axe-core in CI. Zero violations on any route is a build gate.

### 3.2 Landmarks

**Every route renders these landmarks:**

| Landmark | Element | Content |
|---|---|---|
| Banner | `<header>` | Top bar |
| Navigation | `<nav aria-label="Primary">` | Section navigation |
| Main | `<main>` | Route content |
| Contentinfo | `<footer>` | Audit footer |
| Region (when applicable) | `<section aria-labelledby="...">` | Major content blocks (verdict, drivers, breakdown) |

**Skip links** (visible on focus):
- "Skip to main content" → `<main>`
- "Skip to audit footer" → `<footer>`
- "Skip to verdict" → the verdict's `<section>` (on decision spine only)

### 3.3 Screen-Reader Structure (Decision Spine)

```html
<header>
  <MetadataStrip> — landmark, contains timestamp, version, correlation ID
  <ApplicantIdentity> — heading is the applicant's name (H2)
</header>

<main>
  <section aria-labelledby="verdict-heading">
    <h1 id="verdict-heading">Verdict</h1>  <!-- the largest type on the page -->
    <VerdictBlock>
      [verdict text]
      [ConfidenceFrame — single line in mono]
      [override flags as Tags]
    </VerdictBlock>
  </section>

  <section aria-labelledby="drivers-heading">
    <h2 id="drivers-heading">Top drivers</h2>
    <DriverList>
      <DriverItem>
        [name] [value] [contribution]
        [sign indicator in mono: + or −]
      </DriverItem>
      <!-- ... -->
    </DriverList>
  </section>

  <section aria-labelledby="recommendations-heading">
    <h2 id="recommendations-heading">What to do</h2>
    <RecommendationsList>
      <Recommendation>
        [action text]
      </Recommendation>
      <!-- ... -->
    </RecommendationsList>
  </section>

  <section aria-labelledby="breakdown-heading">
    <h2 id="breakdown-heading">Full breakdown</h2>
    <DomainSection aria-labelledby="domain-financial-heading">
      <h3 id="domain-financial-heading">Financial health</h3>
      [table or list of fields]
    </DomainSection>
    <!-- ... -->
  </section>
</main>

<footer aria-label="Audit metadata">
  [full audit lineage]
</footer>
```

**The verdict is the page's H1.** It is the most important element. The screen reader announces it first.

**Live regions:**
- `aria-live="polite"`: connection indicator (top bar).
- `aria-live="assertive"`: form validation errors on submit.

### 3.4 Keyboard Navigation (Complete Model)

**Global:**

| Key | Action |
|---|---|
| `Tab` | Move to next interactive element in document order |
| `Shift-Tab` | Move to previous |
| `Enter` | Activate focused element |
| `Space` | Activate focused element (for buttons) or toggle (for checkboxes) |
| `Escape` | Close modal route → close dropdown → navigate back |
| `/` | Focus search field |
| `Cmd/Ctrl-Enter` | Submit open form |

**In-page anchor navigation (decision spine, history list):**

| Key | Action |
|---|---|
| `j` | Move to next major block |
| `k` | Move to previous major block |
| `Enter` | Scroll focused anchor into view |
| `Escape` | Clear active anchor |

**Form keyboard model:**

| Key | Action |
|---|---|
| Arrow keys | Navigate within radio groups, selects, anchor lists |
| `Tab` from last field | Focus submit button |
| Submit on validation failure | Focus first invalid field, announce error count via `aria-live` |

**Modal routes (none in v1.1 per M1, but if reintroduced):**

| Key | Action |
|---|---|
| `Tab` | Cycle within modal (focus trap) |
| `Escape` | Close modal, restore focus to opener |
| `Enter` on primary button | Submit modal action |

**Skip links:**

| Key | Action |
|---|---|
| `Tab` (first focus) | Reveal skip links at top of page |

---

## 4. Component Ownership Matrix

The component library is **closed**. Every component in the product is in this list. New components require a design review and a v1.2 architecture revision.

### 4.1 Atoms

| Component | Owner | Variants | Tokens Used |
|---|---|---|---|
| `Text` | Typography | display, heading, subheading, body-large, body, body-small, data, data-small, mono, mono-small, label | `--type-*`, `--font-*`, `--ink`, `--ink-60`, `--accent`, `--negative` |
| `Rule` | Layout | default (1px, `--ink-12`), strong (1px, `--ink-24`), accent (1px, `--accent`), vertical (same scale) | `--rule`, `--rule-strong`, `--accent` |
| `Tag` | Atoms | default, positive, negative, accent. Always outlined, 1px border, 0 corner radius | `--type-mono-small`, `--ink`, `--ink-60`, `--positive`, `--negative`, `--accent` |
| `Button` | Atoms | primary, secondary, tertiary. Sizes: default (40px), large (56px) | `--ink`, `--paper`, `--accent`, `--type-body`, `--type-subheading` |
| `Input` | Forms | text, number, select, date, textarea, searchable-select | `--ink`, `--paper`, `--rule`, `--type-body`, `--type-mono` |
| `Label` | Forms | (single component, always mono 12px uppercase) | `--type-label`, `--ink-60` |
| `Checkbox` | Forms | (single component, three states: unchecked, checked, indeterminate) | `--ink`, `--paper`, `--accent` |
| `Radio` | Forms | (single component, single group) | `--ink`, `--paper`, `--accent` |
| `Select` | Forms | default, searchable | `--ink`, `--paper`, `--rule`, `--type-body` |
| `Tooltip` | Overlays | (single component, 240ms hover delay, dismissable with Escape) | `--type-body-small`, `--ink`, `--paper`, `--z-tooltip` |
| `Badge` | Atoms | numeric, status (5 states) | `--type-data-small`, `--ink`, `--ink-60` |
| `Link` | Atoms | default, subtle, in-list | `--ink`, `--accent`, `--type-body`, `--type-body-small` |
| `Kbd` | Atoms | (single component) | `--type-mono-small`, `--ink-60` |
| `LoadingCounter` | States | (single component, typographic, 14pt mono) | `--type-mono`, `--ink` |
| `MetadataStrip` | Atoms | (decision spine only) | `--type-mono`, `--ink-80`, `--rule` |

**Forbidden atoms:**
- `Spinner` — replaced by `LoadingCounter`.
- `Toast` — removed (R5).
- `Icon` — not a separate component. Icons are inline SVG, sized at 16px or 20px, stroke 1.5px, `currentColor`. Used sparingly: keyboard hints, dismissable close buttons, expand/collapse indicators.

### 4.2 Molecules

| Component | Owner | Composition | Tokens Used |
|---|---|---|---|
| `VerdictBlock` | Decision spine | `Text` (display), `ConfidenceFrame`, override `Tag` row, primary action `Button` row | `--type-display*`, `--ink`, `--accent` |
| `ConfidenceFrame` | Decision spine | `Text` (mono), `Tag` × N (override flags) | `--type-mono`, `--ink`, `--ink-60` |
| `DriverList` | Decision spine | `DriverItem` × N, `Rule` between items | `--rule`, `--ink` |
| `DriverItem` | Decision spine | `Text` (name, value), `LoadingCounter` (contribution), `Text` (sign indicator) | `--type-body`, `--type-data`, `--type-mono`, `--ink` |
| `RecommendationsList` | Decision spine | `Recommendation` × N, `Rule` between items | `--rule`, `--ink` |
| `Recommendation` | Decision spine | `Text` (action), `Tag` (severity, if applicable) | `--type-body`, `--ink` |
| `BreakdownTable` | Decision spine | `Table` with field name, value, contribution columns | `--type-body`, `--type-data`, `--type-mono` |
| `DomainSection` | Decision spine | `Heading`, `Rule`, `BreakdownTable` or stacked list | `--type-subheading`, `--rule` |
| `ApplicantIdentity` | Decision spine | `Text` (name, age, business, loan), conditional rendering for privacy mode | `--type-subheading`, `--type-body`, `--ink` |
| `AuditFooter` | Global | `Text` (mono), `Kbd` (shortcut hint), `Link` (full audit log) | `--type-mono`, `--ink-80`, `--rule` |
| `FilterDisclosure` | History | collapsible `Button` + `Rule` + filter fields | `--type-body`, `--type-mono`, `--rule` |
| `HistoryItem` | History | `Text` (name, date, verdict, driver summary), `Tag` (verdict band) | `--type-body`, `--type-mono`, `--ink`, `--ink-60` |
| `SearchField` | Global | `Input` (text), result dropdown (`HistoryItem` or `Link`) | `--type-body`, `--ink`, `--paper`, `--rule` |
| `ConnectionIndicator` | Global | `Text` (mono), `Tag` (state) | `--type-mono`, `--ink`, `--ink-60` |
| `EmptyState` | States | `Text` (one line), optional `Link` (one line) | `--type-body-large`, `--ink-60`, `--accent` |
| `ErrorBoundary` | States | `Text` (heading), `Text` (message), `Button` (retry), `Text` (correlation ID) | `--type-heading`, `--type-body`, `--type-mono`, `--ink` |
| `ReportPanel` | Report | `LoadingCounter`, `Button` (download), `Link` (open PDF) | `--type-body`, `--ink`, `--accent` |
| `FormField` | Forms | `Label`, `Input`, `Text` (error), `Text` (hint) | `--type-label`, `--type-body-small`, `--ink`, `--negative` |

**Forbidden molecules:**
- `FilterBar` — replaced by `FilterDisclosure`.
- `HistoryRow` — replaced by `HistoryItem`.
- `CommandPalette` — replaced by `SearchField`.
- `EscalationPanel` — deferred to v2.
- `ModalRouteShell` — no modal routes in v1.1; report generation is a separate page.
- `Toast` — removed.

### 4.3 Organisms

| Component | Owner | Composition | Notes |
|---|---|---|---|
| `AppShell` | Global | `TopBar`, `LeftRail` (conditional), `Content`, `AuditFooter` | Always renders top bar + audit footer. Left rail conditional on breakpoint. |
| `TopBar` | Global | `Text` (monogram), `SearchField`, `ConnectionIndicator`, privacy toggle, user identity dropdown | 56px desktop, 48px mobile. Auto-hides on scroll-down on decision spine. |
| `LeftRail` | Global | `Link` × N (section nav) | 200px expanded, 32px collapsed. Expands on hover/focus. Items depend on route. |
| `BottomBar` | Mobile | `Link` × N (section nav) | 40px visible, 56×56 tappable. Auto-hides on decision spine. |
| `DecisionSpine` | Routes | `MetadataStrip`, `ApplicantIdentity`, `VerdictBlock`, `DriverList`, `RecommendationsList`, `DomainSection` × N, `AuditFooter` | The hero screen. Layout per §5.2. |
| `IntakeForm` | Routes | `FormField` × N, grouped into domain sections, `Button` (submit) | Two-column desktop, one-column mobile. |
| `TypeSelector` | Routes | `Text` (display, two links), `Text` (description) | Single row. No cards. |
| `HistoryList` | Routes | `FilterDisclosure` (collapsible), `HistoryItem` × N, `Button` (load more) | Chronological, newest first. |
| `ReportPage` | Routes | `ReportPanel` (download), `Text` (correlation ID), `Button` (back) | Separate page, not a modal. |
| `SettingsPage` | Routes | `FormField` × N (profile), `FormField` × N (defaults), `FormField` × N (security) | Single page, three sections, hairline-separated. |
| `SignIn` | Auth | `FormField` × 3, `Button` (submit), `Link` (forgot) | |
| `NotFound` | Errors | `Text` (heading), `Text` (message), `Link` (back) | |
| `ServerError` | Errors | `Text` (heading), `Text` (message), `Text` (correlation ID, copyable), `Button` (retry) | |
| `SessionExpired` | Auth | `Text` (message), `Button` (sign in) | |
| `LegalPage` | Legal | `Text` (content from API) | Static content. |

**Forbidden organisms:**
- `ComparisonView` — deferred.
- `BatchUploader` — deferred.
- `ModalRouteShell` — no modals in v1.1.

### 4.4 Page Templates

Each route maps to one page template. Templates are not separate components; they are compositions of organisms in the route's render function.

| Template | Routes | Composition |
|---|---|---|
| `IntakePage` | `/assess/person-a`, `/assess/person-b` | `AppShell` + `IntakeForm` |
| `DecisionPage` | `/assess/$id`, `/history/$id` | `AppShell` + `DecisionSpine` |
| `TypeSelectPage` | `/assess/new` | `AppShell` + `TypeSelector` |
| `ReportPage` | `/assess/$id/report` | `AppShell` + `ReportPage` (full-page report view, not a modal) |
| `HistoryPage` | `/history` | `AppShell` + `HistoryList` |
| `SettingsPage` | `/settings` | `AppShell` + `SettingsPage` |
| `SignInPage` | `/auth/sign-in` | `AppShell` (no left rail) + `SignIn` |
| `ErrorPage` | `/404`, `/500` | `AppShell` + `NotFound` or `ServerError` |
| `LegalPage` | `/legal/terms`, `/legal/privacy` | `AppShell` + `LegalPage` |

---

## 5. Mobile Strategy

### 5.1 Breakpoint Behavior

**Per-route adaptation:**

| Route | Mobile (<768px) | Tablet (768–1023px) | Desktop (≥1024px) |
|---|---|---|---|
| `/assess/new` | Single column, two text links stacked | Single column, two text links side by side | Single column, two text links side by side |
| `/assess/person-a` | One column, fields full width | Two columns (form left, hints inline) | Two columns (form left, hints right) |
| `/assess/person-b` | Same as above | Same as above | Same as above |
| `/assess/$id` | Verdict 30pt, drivers stacked, breakdown as list, top bar auto-hides on scroll-down, no bottom bar | Verdict 30pt, drivers 2-col grid, breakdown as table | Verdict 44pt, drivers 3-col, breakdown as table, left rail 200px |
| `/assess/$id/report` | Single column, download button full width | Same | Same |
| `/history` | Single column, filter disclosure full width | Same, wider | Same, wider |
| `/settings` | Single column, sections stacked | Same | Same |
| `/auth/sign-in` | Single column, fields full width | Same | Centered, max-width 400px |
| `/legal/*` | Single column, max-width 720px, comfortable reading width | Same | Same |

### 5.2 Decision Spine Mobile Specification

**Critical viewport allocation:**

| Element | Height (375px wide) |
|---|---|
| Status bar (OS) | ~20px |
| Top bar (auto-hide) | 48px (when visible) |
| Safe area top | ~0–44px (device-dependent) |
| Verdict | 120–160px (2 lines at 30pt display) |
| Metadata strip | 32px |
| Confidence frame | 32px |
| Drivers (3 items) | 180px (60px each) |
| Recommendations (3 items) | 120px (40px each) |
| Audit footer (collapsed) | 64px |
| Safe area bottom | ~34px (iOS) |

**Auto-hide behavior:**
- Top bar hides on scroll-down (>50px scroll).
- Top bar reveals on scroll-up.
- Bottom bar hides on scroll-down on the decision spine only. On all other routes, it persists.
- Hide animation: 160ms ease-out. Reveal animation: 160ms ease-out.

**Tap targets:**
- All interactive elements: 56×56px minimum tappable region.
- The visible button may be 40px; the tappable region is 56×56px.
- `padding` and `min-height` enforce the tappable region; `box-sizing: border-box` is global.

### 5.3 Touch Interactions

| Interaction | Mobile Behavior |
|---|---|
| Pull-to-refresh | Disabled. The product does not refresh on pull. Refresh is the auto-refetch on reconnect. |
| Swipe-to-delete | Disabled. No deletion in v1. |
| Long-press | Disabled. No context menus in v1. |
| Pinch-to-zoom | Disabled globally. The type scale is set for the viewport. |
| Haptic feedback | Disabled. The product does not vibrate. |
| Native share sheet | Enabled on report PDFs. The "Share" button uses the OS share sheet. |
| Voice input | Disabled in v1. |
| Double-tap to zoom | Disabled. |
| Tap delay | 300ms click delay disabled globally via `touch-action: manipulation`. |

### 5.4 Mobile Network Resilience

**First-paint budget:** 1.5s on 3G, 4.0s on 2G.

**Critical-path payload:** identity, verdict slot, audit footer. Server-rendered or cached. ~14KB gzipped target.

**Lazy loading:** Full breakdown, report generation, history list (beyond first 20), settings sections. Triggered on scroll or on demand.

**Offline behavior:** Per §1.6.

### 5.5 What is Not Adapted for Mobile

v1.1 removes the "Available on desktop" pattern entirely. For v1.1, there are no features that exist on desktop but not on mobile. All shipped features work on all breakpoints, with the adaptations above. Deferred features (compare, batch, escalation, model version override) are not in v1.1 at all.

---

## 6. Performance Contract

### 6.1 Bundle Limits

| Bundle | Limit (gzipped) | Current Target |
|---|---|---|
| Critical-path JS (initial route) | 80KB | 60KB |
| Critical-path CSS (initial route) | 25KB | 20KB |
| Initial route HTML (SSR) | 30KB | 24KB |
| Full app JS (lazy-loaded, total) | 300KB | 250KB |
| Per-route JS (lazy chunk) | 60KB | 45KB |
| Largest single asset (font, image) | 50KB | 40KB |

**Enforcement:** Vite build fails if critical-path JS exceeds 80KB gzipped. CI gate.

### 6.2 Route Budgets

| Route | FCP | LCP | TTI | TBT | CLS |
|---|---|---|---|---|---|
| `/auth/sign-in` | 0.8s | 1.0s | 1.5s | 50ms | 0.00 |
| `/assess/new` | 0.8s | 1.0s | 1.5s | 50ms | 0.00 |
| `/assess/person-a` | 1.0s | 1.5s | 2.0s | 80ms | 0.00 |
| `/assess/person-b` | 1.0s | 1.5s | 2.0s | 80ms | 0.00 |
| `/assess/$id` (initial) | 1.0s | 1.5s | 2.0s | 100ms | 0.00 |
| `/assess/$id` (full) | 1.5s | 2.5s | 3.5s | 150ms | 0.00 |
| `/history` | 1.0s | 1.5s | 2.0s | 100ms | 0.00 |
| `/settings` | 1.0s | 1.5s | 2.0s | 100ms | 0.00 |

Mobile (3G, slow 4x CPU): multiply by 2.0. All values are the 75th percentile from real-user monitoring.

### 6.3 Lighthouse Requirements

| Category | Target | Build Gate |
|---|---|---|
| Performance | ≥90 (mobile) | Build fails below 85 |
| Accessibility | 100 | Build fails below 100 |
| Best Practices | ≥95 | Build fails below 90 |
| SEO | ≥90 | Build fails below 85 |

**Enforcement:** Lighthouse CI on every PR and on every merge to main.

### 6.4 Performance Budgets (Operational)

| Metric | Budget | Action on Exceedance |
|---|---|---|
| First Contentful Paint (desktop) | 1.0s | Performance audit event |
| First Contentful Paint (mobile, 3G) | 2.0s | Performance audit event |
| Largest Contentful Paint (desktop) | 1.5s | Performance audit event |
| Largest Contentful Paint (mobile, 3G) | 3.0s | Performance audit event |
| Time to Interactive (desktop) | 2.0s | Performance audit event |
| Time to Interactive (mobile, 3G) | 4.0s | Performance audit event |
| Cumulative Layout Shift | 0.00 | Build fails |
| Total Blocking Time | 100ms | Build fails |
| Input latency (form typing) | 16ms (one frame) | Build fails |
| Decision spine render (after API response) | 200ms | Performance audit event |

Performance audit events are emitted to `POST /api/audit/performance` (assumed endpoint; if not available, queued in localStorage).

---

## 7. Component State Discipline

Every component in the inventory has nine states. A component is not "done" until every state is designed and implemented. The states are:

| State | Description |
|---|---|
| Default | Resting, no interaction |
| Hover | Cursor over (pointer devices only) |
| Focus | Keyboard focus or programmatic focus |
| Active / Pressed | Mouse down or key down |
| Disabled | Non-interactive (gray, `--ink-40`) |
| Loading | Data is being fetched |
| Error | Validation or API error |
| Empty | No data to display |
| Read-only | Display only, no interaction |

**Component state spec sheet format:** For each component, the spec sheet lists the visual treatment of each state, referencing tokens, transitions, and accessibility annotations (e.g., `aria-busy`, `aria-invalid`, `aria-disabled`).

**No state is "designed later."** A component that has a state in production but no spec is a build blocker.

---

## 8. Decision Spine Layout Specification

(This section is the §3.5.1 referenced in M2. It is the layout specification for the hero screen.)

### 8.1 Desktop Layout (≥1024px)

**Grid:** 12 columns, 32px gutter, max-width 1200px, 96px outer margin.

**Vertical rhythm:** 64px between major blocks, 32px between a block and its label, 16px between a label and its content.

| Block | Columns | Type | Position |
|---|---|---|---|
| Top bar | 12 (full width) | — | Sticky top, 56px |
| Metadata strip | 12 (full width) | Mono 14pt | Below top bar, sticky on scroll, 32px |
| Applicant identity | 8 (left) | Display 22pt name, body 15pt details | Below metadata strip, 96px top padding |
| Verdict | 12 (full width) | Display 44pt | Below identity, 128px top padding, 128px bottom padding |
| Confidence frame | 8 (left) | Mono 14pt, single line | Below verdict, 0px top padding (adjacent) |
| Override flags | 4 (right) | Tag row | Same row as confidence, right-aligned |
| Top drivers heading | 12 | Subheading 22pt | Below confidence, 64px top padding |
| Top drivers | 12 (3 columns × 4 cols each) | Body 15pt + data 14pt + mono 12pt contribution | Below heading, 16px top padding |
| Recommendations heading | 12 | Subheading 22pt | Below drivers, 64px top padding |
| Recommendations | 12 (3 columns × 4 cols each) | Body 15pt | Below heading, 16px top padding |
| Full breakdown heading | 12 | Subheading 22pt | Below recommendations, 64px top padding |
| Domain sections | 12 (stacked) | Body 15pt + data 14pt | Below heading, 32px between sections |
| Audit footer | 12 (full width, breaks container) | Mono 14pt | Bottom of page, 64px top padding |

**Z-axis:** Top bar (z-10) > metadata strip (z-10) > content (z-base). Tooltips (z-200) > everything.

### 8.2 Tablet Layout (768–1023px)

**Grid:** 8 columns, 24px gutter, 64px outer margin.

| Block | Columns | Type |
|---|---|---|
| Top bar | 8 (full width) | — |
| Metadata strip | 8 (full width) | Mono 14pt |
| Applicant identity | 8 (full width) | Subheading 22pt name, body 15pt details |
| Verdict | 8 (full width) | Display 30pt |
| Confidence frame + override flags | 8 (full width, stacked) | Mono 14pt + Tags |
| Top drivers | 8 (2 columns × 4 cols) | Body 15pt |
| Recommendations | 8 (2 columns × 4 cols) | Body 15pt |
| Breakdown | 8 (full width) | Table or list |
| Audit footer | 8 (full width) | Mono 14pt |

**Left rail:** 32px collapsed micro-rail, left edge. Hides on tablet (no hover state). Replaced by top-bar section nav (in user-identity dropdown).

### 8.3 Mobile Layout (<768px)

**Grid:** 4 columns, 16px gutter, 16px outer margin.

| Block | Columns | Type |
|---|---|---|
| Top bar | 4 (full width) | 48px, auto-hide on scroll |
| Metadata strip | 4 (full width) | Mono 12pt (one line, truncated) |
| Applicant identity | 4 (full width) | Subheading 22pt name, body 15pt details (stacked) |
| Verdict | 4 (full width) | Display 30pt, 64px top/bottom padding |
| Confidence frame | 4 (full width) | Mono 12pt (truncated if needed) |
| Override flags | 4 (full width) | Tag row, wraps |
| Top drivers | 4 (stacked) | Body 15pt, 32px between items |
| Recommendations | 4 (stacked) | Body 15pt, 32px between items |
| Breakdown | 4 (stacked list) | List rendering per §5.4 |
| Audit footer | 4 (full width) | Mono 12pt, one-line metadata strip with "Show details" |

**Bottom bar:** 40px visible, 56×56 tappable. Auto-hides on decision spine only. Persists on all other routes.

### 8.4 Type Assignment (Per Block)

| Block | Desktop | Tablet | Mobile |
|---|---|---|---|
| Verdict | Display 44pt | Display 30pt | Display 30pt |
| Section H2 (Top drivers, Recommendations, Breakdown) | Subheading 22pt | Subheading 22pt | Subheading 22pt |
| Applicant name | Subheading 22pt | Subheading 22pt | Subheading 22pt |
| Applicant details | Body 15pt | Body 15pt | Body 15pt |
| Verdict subtext (confidence, flags) | Mono 14pt | Mono 14pt | Mono 12pt |
| Driver name | Body 15pt | Body 15pt | Body 15pt |
| Driver value | Data 14pt | Data 14pt | Data 14pt |
| Driver contribution | Mono 12pt | Mono 12pt | Mono 12pt |
| Recommendation text | Body 15pt | Body 15pt | Body 15pt |
| Domain section heading | Subheading 22pt | Subheading 22pt | Subheading 17pt |
| Field name | Body 15pt | Body 15pt | Body 15pt |
| Field value | Data 14pt | Data 14pt | Data 14pt |
| Field contribution | Mono 12pt | Mono 12pt | Mono 12pt |
| Metadata strip | Mono 14pt | Mono 14pt | Mono 12pt |
| Audit footer | Mono 14pt (80% alpha) | Mono 14pt (80% alpha) | Mono 12pt (80% alpha) |

### 8.5 Loading Order

The decision spine renders in this order:

1. **First paint (rule of three):** applicant identity (placeholder), verdict slot (`—`), audit footer (full).
2. **Identity resolves:** name, age, business, loan, timestamp.
3. **Verdict slot fills:** verdict text appears.
4. **Confidence frame renders:** probability range, override flags.
5. **Drivers render:** ranked list with contribution bars.
6. **Recommendations render:** adjacent list.
7. **Breakdown sections lazy-load:** on scroll, or on demand via "Show full breakdown" link.

**Each step transitions in 160ms ease-out. No step takes longer than 800ms before the next step begins.**

---

## 9. Form Architecture Specification

(This section expands the v1.0 form architecture per §1.5 of this v1.1.)

### 9.1 Schema Source

Zod schemas are generated from the backend's OpenAPI types at build time. The generated schemas live in `src/schemas/`. Manual schemas are forbidden for any field sent to the API. UI-only fields (e.g., a "save as draft" toggle) may have manual Zod schemas.

### 9.2 Field Components

**Every form field is a `FormField` molecule composed of:**

```
<FormField>
  <Label>...</Label>
  <Input />
  <Text>(error or hint)</Text>
</FormField>
```

The `FormField` handles:
- Label association (`for`/`id`).
- Error association (`aria-describedby`).
- Field state visual treatment (default, focused, filled, valid, invalid, disabled, readonly).
- Error message rendering (only when invalid).

### 9.3 Validation Timing

| Trigger | Validation |
|---|---|
| Field blur | Field-level validation. Error renders below field. |
| Field change (after error) | Re-validate field. Error clears if valid. |
| Form submit | Form-level validation. All field errors render. First invalid field focused. Error count announced via `aria-live`. |
| Server response | Server validation errors mapped to fields. Unmapped errors render at form level. |

### 9.4 Draft Lifecycle

| Event | Draft Action |
|---|---|
| Field blur (any field) | Save draft to localStorage. |
| Form submit (success) | Clear draft. |
| Form submit (error) | Preserve draft. |
| Sign-out | Clear draft. |
| Draft > 24h old | Clear draft on next visit. |
| Form schema changed | Mark draft stale. Show "Form has changed" message. User chooses. |
| Different device | Drafts are local. No sync. |

### 9.5 Submission Flow

```
User clicks Submit
  → Button label: "Submitting…"
  → Button disabled
  → Form not cleared
  → POST /api/assess/{person-a|person-b}
  → Success: clear draft, navigate to /assess/{id}
  → 4xx: render errors, button re-enabled, label "Submit"
  → 5xx: render error + correlation ID, button re-enabled
  → Network error: render ConnectionIndicator state + "Could not submit"
```

---

## 10. Data Visualizations

### 10.1 Approved Visualizations

| Component | Purpose | Form | Rejected Alternatives |
|---|---|---|---|
| `FeatureContributionBar` | Feature contributions to probability | Horizontal bar, one per feature, monochrome + accent for largest positive, oxblood for largest negative. Sign in mono. | Waterfall, pie, diverging stacked |
| `ProbabilityRange` | Probability as range, not point | Horizontal track, range bar, center marker. Mono labels below. | Gauge, dot-on-scale |
| `ComponentBreakdown` | Readiness components and weights | Five-row table. No chart. | Radar, donut |
| `CibilTierStrip` | CIBIL score position | Horizontal track, four segments, marker, mono labels. | N/A |
| `OverrideFlag` | Override flag indicator | `Tag` component, outlined, 1px border, 0 corner radius. | N/A |

### 10.2 Forbidden Visualizations

| Visualization | Why Forbidden |
|---|---|
| Pie / donut | Hides precision |
| Radar | No precision, weights hidden |
| 3D any | Distortion is a bug |
| Gauge | False precision, no range |
| Heatmap | Color carries meaning |
| Stacked area | Cumulative impact obscured |
| Sankey | Not legible |
| Animated chart | Animation is feedback, not narration |
| Map (geo) | Not in v1.1 scope |

### 10.3 Contribution Chart Specification (M18)

The `FeatureContributionBar` distinguishes largest positive and largest negative by three redundant signals:

1. **Position:** largest positive is first in the ranked list; largest negative is last.
2. **Sign indicator:** `+` prefix for positive, `−` prefix (not minus-glyph) for negative. Set in mono, 12pt, `--ink-60` alpha.
3. **Color:** `--accent` for largest positive, `--negative` for largest negative. All other bars are `--ink` at 60% alpha.

No single signal is primary. All three together.

---

## 11. Error States

### 11.1 Error Catalog (Final)

| Error | Location | Treatment |
|---|---|---|
| Field validation | Inline, below field | `Text` 14pt `--negative`. Border `--negative`. Focus first invalid on submit. |
| Form submit | Top of form, hairline-separated | `Text` 15pt `--negative`. List of field errors below. |
| API 400 | Replace page | Display 30pt heading + paragraph + retry button. |
| API 401 | Redirect `/auth/sign-in?from=$path` | Sign-in page with "Your session expired." text above form. |
| API 403 | Replace page | Display 30pt "You do not have access to this assessment." + back link. |
| API 404 | Replace page | Display 30pt "This assessment does not exist or has been deleted." + back link. |
| API 409 | Inline near action | `Text` `--negative` + retry button. Audit log entry in tooltip. |
| API 429 | Replace page | Display 30pt "You have made many requests. Please wait a moment." + audit footer with rate-limit ID. |
| API 500 | Replace page | Display 30pt "RiskIntel could not complete this request." + retry button + correlation ID copy button. |
| API 503 | Replace page | Display 30pt "RiskIntel is temporarily unavailable. We are working on it." + link to `/status` (deferred, so link is a no-op with text "We will be back shortly"). |
| Network offline | `ConnectionIndicator` | "Offline — your work is saved." |
| Network reconnecting | `ConnectionIndicator` | "Reconnecting…" |
| JS error | Error boundary | `ErrorPage` with correlation ID + sign-out link. |
| Imputed field | Inline, below field | `Text` 12pt mono `--ink-60` "Income imputed as ₹4,200/mo from monthly expenses." |

### 11.2 Forbidden Error Patterns

- Red banner across top of page.
- Modal alert dialogs.
- "Oops!" / "Something went wrong" copy.
- Errors hidden in marketing paragraphs.
- Self-dismissing errors.
- Errors requiring page reload.
- Errors that hide the audit footer.

### 11.3 Error → Audit Integration

Every error emits a structured audit event:
- Category (validation, network, server, unhandled).
- Endpoint or component.
- Correlation ID.
- User role and institution.
- Model version (if applicable).
- Timestamp.

Events sent to `POST /api/audit/client-error` (assumed endpoint). If unavailable, queued in localStorage and sent on next successful request.

---

## 12. Loading States

### 12.1 Loading Catalog (Final)

| Scenario | Treatment |
|---|---|
| Form submit | Button label "Submitting…", disabled. Form not cleared. |
| Decision spine (after submit) | Verdict slot "—", `LoadingCounter` with step ("Validating inputs…", "Running model…", "Computing confidence interval…", "Finalizing…"). Audit footer rendered. |
| Full breakdown lazy load | `DomainSection` shows "Loading 4 of 7 signals…" |
| History list | "Loading assessments from [date range]…" with date range from URL. Filter disclosure interactive. |
| Report PDF | `LoadingCounter` + "Cancel" button. Audit footer rendered. Max 30s, then error. |
| Single component | Component shows "Loading…" in mono. Page not blocked. |
| Reconnecting | `ConnectionIndicator` shows "Reconnecting…" |

### 12.2 Time Budgets

| Operation | Budget |
|---|---|
| Sign-in | 1.5s |
| Form submit → first byte | 2.0s |
| Decision spine render | 4.0s (full breakdown may continue) |
| Full breakdown lazy load | 3.0s |
| Report PDF generation | 5.0s |
| History list first page | 1.0s |
| History list next page | 1.0s |
| Search field | 200ms (local), 1.0s (remote) |

### 12.3 Forbidden Loading Patterns

- Spinners, pulsing dots, circular progress.
- Skeleton screens.
- "Loading…" without context.
- Blocking overlays preventing navigation.
- Loading states hiding the audit footer.
- Fake progress (copy changes without state changing).
- Loading animations >800ms total.

---

## 13. Empty States

### 13.1 Empty State Catalog (Final, Per M6)

| Empty State | Treatment |
|---|---|
| No history (first use) | "No assessments yet." + "Run a new assessment" link. |
| History filter no match | "No assessments match these filters." + "Clear filters" link. |
| Compare (deferred) | N/A — feature deferred. |
| Settings (MFI not enabled) | N/A — feature deferred. |
| Sign-in empty fields | Inline validation. No empty state page. |
| Report not eligible | "A report cannot be generated for this assessment." + back link. |
| Search no results | "No results for 'query'. Try a different name or ID." |
| History single item | Compare not in navigation. No empty state. |

**Format:** One line in `--type-body-large`, `--ink-60` alpha. One text link below in `--accent` if needed. Two lines maximum.

### 13.2 Forbidden Empty State Patterns

- Illustrations of people.
- "Oops!"
- "Looks like you're new here!"
- Onboarding modals with "Got it!"
- "Click here to add your first X."
- Marketing copy.

---

## 14. Final Scope Lock

### 14.1 Routes (Final)

| Route | Status |
|---|---|
| `/` | Redirect → `/assess/new` |
| `/auth/sign-in` | **Required** |
| `/auth/forgot` | **Required** |
| `/auth/locked` | **Required** |
| `/assess/new` | **Required** |
| `/assess/person-a` | **Required** |
| `/assess/person-b` | **Required** |
| `/assess/$id` | **Required** |
| `/assess/$id/report` | **Required** (separate page) |
| `/history` | **Required** |
| `/history/$id` | **Required** |
| `/settings` | **Required** (single page, 3 sections) |
| `/legal/terms` | **Required** |
| `/legal/privacy` | **Required** |
| `/404` | **Required** |
| `/500` | **Required** |
| `/history/compare` | **Deferred to v2** |
| `/assess/$id/escalate` | **Deferred to v2** |
| `/settings/batch` | **Deferred to v2** |
| `/legal/audit` | **Deferred to v2** |
| `/status` | **Deferred to v2** |

### 14.2 Components (Final)

All atoms in §4.1 except `Spinner` (forbidden) and `Toast` (removed). All molecules in §4.2 except those marked forbidden or deferred. All organisms in §4.3 except those marked forbidden or deferred.

### 14.3 Features (Final)

| Feature | Status |
|---|---|
| Approve / Decline / Escalate buttons (Escalate stubbed: shows "Escalation is not available in this version") | **Required** (Escalate stub with typographic message) |
| Generate report PDF | **Required** |
| Download report PDF | **Required** |
| View history (reading list) | **Required** |
| Search history (by name, ID) | **Required** (search field, `/` shortcut) |
| Filter history (by date, type, verdict) | **Required** (filter disclosure) |
| Privacy mode | **Required** |
| History scope (role-based) | **Required** |
| Mobile breakdown as stacked list | **Required** |
| Contribution chart with non-color signals | **Required** |
| Escalation workflow | **Deferred to v2** |
| Batch CSV upload | **Deferred to v2** |
| Compare two assessments | **Deferred to v2** |
| Model version override | **Deferred to v2** |
| Cmd-K command palette | **Removed** |
| Modal routes | **Removed (report is a separate page)** |
| Skeleton screens | **Forbidden** |
| Spinners | **Forbidden** |
| Toast notifications | **Removed** |
| "Available on desktop" pattern | **Removed** |
| Dark mode | **Deferred to v2** |
| Voice input | **Deferred to v2** |

### 14.4 Open Questions Resolved

| # | Original Question | Resolution |
|---|---|---|
| 1 | Compare view roles | **Deferred to v2** |
| 2 | Model version override users | **Deferred to v2** |
| 3 | Assessment deletion policy | **v1 has no deletion. Audit log is append-only.** |
| 4 | Escalation workflow | **Deferred to v2**. Escalate button is stubbed with typographic "Escalation is not available in this version." |
| 5 | Batch file formats | **Deferred to v2** |
| 6 | Institution-level model version pinning | **Deferred to v2** |

### 14.5 Stack (Final)

| Layer | Choice |
|---|---|
| Framework | React 18+ |
| Routing | TanStack Router |
| Server state | TanStack Query |
| Client state | Zustand (small), React Hook Form (form state) |
| Forms | React Hook Form + Zod |
| Schema source | openapi-typescript → generated Zod |
| Styling | Vanilla CSS with design tokens + CSS Modules |
| Type generation | openapi-typescript |
| Testing | Playwright (e2e) + Vitest (unit) + Testing Library (component) |
| Linting | ESLint + Prettier + Stylelint |
| Build | Vite |
| CI | GitHub Actions + Lighthouse CI + axe-core |
| Monitoring | (TBD) |
| Error tracking | (TBD) |

**Explicitly rejected:** Tailwind CSS, Material UI, Chakra, Ant Design, Mantine, Framer Motion, Redux, MobX, Recoil, Jotai (Zustand is the maximum).

### 14.6 Build Sequence

1. Token system (§2) — first, before any component.
2. Atom library (§4.1) — every atom in every state.
3. Molecule library (§4.2) — composed from atoms.
4. Organism library (§4.3) — composed from molecules.
5. Page templates — one per route.
6. Routing and auth guards.
7. Query layer (TanStack Query setup, hooks per API).
8. Form layer (React Hook Form + Zod integration).
9. Error boundaries (3 levels).
10. Performance budgets in CI.
11. Accessibility tests in CI.
12. E2E test suite (Playwright).

---

## 15. Sign-off

This architecture is frozen for build. Any change is a design decision requiring Frontend Architect + Principal Product Designer sign-off, recorded in `ARCHITECTURE_CHANGELOG.md`.

**Build signal:** Approved. v1.1 supersedes v1.0. Build begins with §14.6 sequence.

**Reconciliation summary:**

- 22 modifications evaluated, 15 accepted, 6 modified, 1 rejected (M9).
- 13 removals evaluated, 3 deferred to v2, 3 removed, 2 accepted, 1 modified.
- 20 missing specifications filled (MS1–MS20, now integrated into §2, §3, §4, §5, §6, §8, §9).
- 7 new sections added (State, Tokens, Accessibility, Components, Mobile, Performance, Decision Spine Layout).
- 0 backend changes required.

**Pre-build effort estimate:** ~200 hours of design + ~400 hours of frontend work, no backend work. v1.1 is approximately 25% longer than v1.0 but 5x more specific. Every page is buildable without further design clarification.

**Review triggers:** New user segment, new backend endpoint, production error pattern, design drift, regulatory change.
