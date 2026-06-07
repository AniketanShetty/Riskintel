# RiskIntel — Component Specification

**Version:** 1.0
**Status:** Frozen for build
**Inherits from:** `DESIGN_BRIEF.md` v1.0, `FRONTEND_ARCHITECTURE_V1.1.md` v1.1, `DESIGN_TOKENS.md` v1.0
**Author:** Final Frontend Architect

---

## 0. How To Read This File

Every component in the v1 product is specified here. Each spec lists:

1. **Identity** — name, category, ownership, file location
2. **Purpose** — what it does, what it does not do
3. **Composition** — atoms and molecules it composes
4. **Props** — typed interface, no `any`, no optionals without reason
5. **States** — all 9 states (default, hover, focus, active, disabled, loading, error, empty, read-only)
6. **Variants** — enumerated, exhaustive
7. **Tokens** — which design tokens it references
8. **Accessibility** — ARIA roles, keyboard behavior, screen-reader announcements
9. **Dependencies** — what other components it imports

A component is not "done" until every section is filled. No state is "designed later."

**Categories:** Atoms → Molecules → Organisms → Page Templates. Composition flows downward (organisms compose molecules, molecules compose atoms). No upward references.

**File location convention:**
- `src/components/atoms/`
- `src/components/molecules/`
- `src/components/organisms/`
- `src/components/templates/`

**Forbidden components (not in this file):** `Spinner`, `Toast`, `Modal`, `Carousel`, `Alert`, `EmptyIllustration`, `StatCard`, `FilterBar`, `HistoryRow`, `CommandPalette`, `EscalationPanel`, `ModalRouteShell`, `LeftRail` (replaced by `NavRail`), `BottomBar` (replaced by `MobileNav`), `SettingsPage` (replaced by `SettingsTemplate`), `HistoryTable` (replaced by `HistoryList`), `Toast`, `EmptyIllustration`. See FRONTEND_ARCHITECTURE_V1.1.md §4 for the full forbidden list.

---

## 1. Atoms

### 1.1 `Text`

**Category:** Atom
**File:** `src/components/atoms/Text/Text.tsx`
**Owner:** Typography

**Purpose:** Renders a single piece of text with full control over type scale, weight, color, and font family. The only component that produces text on screen. Every other component composes `Text` (directly or via atoms that compose it).

**Props:**

```ts
type TextVariant =
  | "display"
  | "display-tablet"
  | "display-mobile"
  | "heading"
  | "subheading"
  | "body-large"
  | "body"
  | "body-small"
  | "data"
  | "data-small"
  | "mono"
  | "mono-small"
  | "label";

type TextColor =
  | "ink"
  | "ink-80"
  | "ink-60"
  | "ink-40"
  | "accent"
  | "positive"
  | "negative"
  | "inherit";

type TextFont = "display" | "body" | "data" | "mono" | "inherit";

type TextAs =
  | "span" | "p" | "h1" | "h2" | "h3" | "h4"
  | "div" | "label" | "strong" | "em" | "small" | "time";

interface TextProps {
  variant: TextVariant;
  color?: TextColor;
  font?: TextFont;
  as?: TextAs;
  children: React.ReactNode;
  id?: string;
  className?: string;
  truncate?: boolean;
  uppercase?: boolean;
  ariaLabel?: string;
}
```

**Variants:** 13 (one per type scale token). Required: `variant`. Default: `as = "span"`, `color = "ink"`, `font` inferred from variant.

**States:** None. `Text` is stateless.

**Tokens:** All `--type-*`, `--color-*`, `--font-*`.

**Accessibility:**
- `as` prop sets the semantic element. Screen readers use this for navigation.
- `ariaLabel` overrides the visible text for screen readers (rare; used for icons-as-text or abbreviation expansion).
- Truncation uses `text-overflow: ellipsis` with `aria-label` containing the full text.

**Dependencies:** None.

---

### 1.2 `Rule`

**Category:** Atom
**File:** `src/components/atoms/Rule/Rule.tsx`
**Owner:** Layout

**Purpose:** A horizontal or vertical hairline divider. The only visual structure element besides the z-index hierarchy.

**Props:**

```ts
type RuleOrientation = "horizontal" | "vertical";
type RuleWeight = "default" | "strong" | "accent";

interface RuleProps {
  orientation?: RuleOrientation; // default: "horizontal"
  weight?: RuleWeight;            // default: "default"
  length?: string;                // CSS length, e.g. "100%", "240px"
  className?: string;
  ariaHidden?: boolean;           // default: false
}
```

**Variants:** 3 weights × 2 orientations = 6 combinations. Length defaults to 100% of parent (horizontal) or 1px (vertical).

**States:** None.

**Tokens:** `--color-rule`, `--color-rule-strong`, `--color-accent`.

**Accessibility:**
- Renders `<hr>` for horizontal, `<div role="separator" aria-orientation="vertical">` for vertical.
- `aria-hidden="true"` for purely decorative rules (the default is to be discoverable).

**Dependencies:** None.

---

### 1.3 `Tag`

**Category:** Atom
**File:** `src/components/atoms/Tag/Tag.tsx`
**Owner:** Atoms

**Purpose:** An inline outlined label for status, override flags, and metadata. The only semantic-color component besides the verdict.

**Props:**

```ts
type TagVariant = "default" | "positive" | "negative" | "accent";

interface TagProps {
  variant?: TagVariant;        // default: "default"
  children: React.ReactNode;
  className?: string;
  ariaLabel?: string;
}
```

**Variants:** 4. All outlined (1px border, 0 corner radius), never filled.

**States:**
- Default — outlined in `variant` color.
- Hover — no visual change (tag is not interactive).
- Focus — focus ring (2px, `var(--color-accent)`) if tag is wrapped in a focusable parent (rare).
- Disabled — N/A.
- Loading — N/A.
- Error — N/A (use `negative` variant).
- Empty — N/A.
- Read-only — default.

**Tokens:** `--type-mono-small`, `--color-ink`, `--color-rule-strong`, `--color-positive`, `--color-negative`, `--color-accent`.

**Accessibility:**
- Renders `<span>` by default.
- If interactive (e.g., dismissable), use `<button>` with `aria-label`.
- `aria-label` overrides visible text for icon-only tags.

**Dependencies:** None.

---

### 1.4 `Button`

**Category:** Atom
**File:** `src/components/atoms/Button/Button.tsx`
**Owner:** Atoms

**Purpose:** The primary action element. Every primary action in the product uses `Button`. Three variants (primary, secondary, tertiary), two sizes (default, large).

**Props:**

```ts
type ButtonVariant = "primary" | "secondary" | "tertiary";
type ButtonSize = "default" | "large";
type ButtonType = "button" | "submit" | "reset";

interface ButtonProps {
  variant?: ButtonVariant;     // default: "primary"
  size?: ButtonSize;           // default: "default"
  type?: ButtonType;           // default: "button"
  disabled?: boolean;
  loading?: boolean;           // shows "Submitting…" instead of children
  loadingText?: string;        // default: "Submitting…"
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  children: React.ReactNode;
  className?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  ariaExpanded?: boolean;
  ariaPressed?: boolean;
}
```

**Variants:** 3 × 2 = 6 combinations.

**States:**
- Default — per variant.
- Hover — per variant (see design tokens).
- Focus — `var(--focus-color)`, 2px, 2px offset.
- Active/Pressed — `opacity: var(--opacity-pressed)`.
- Disabled — text `var(--color-ink-40)`, background `transparent` (primary) or `var(--color-ink-8)` (secondary), cursor `not-allowed"`, no hover.
- Loading — children replaced by `loadingText` (mono 14pt), button disabled, no hover.
- Error — N/A (use error state in form, not button).
- Empty — N/A.
- Read-only — N/A (use `Tag` or `Text` instead).

**Tokens:** `--space-2`, `--space-3`, `--space-4`, `--space-5`, `--type-body`, `--type-subheading`, `--color-ink`, `--color-paper`, `--color-accent`, `--color-ink-8`, `--color-ink-40`, `--motion-exit`, `--touch-min`, `--radius-none`.

**Accessibility:**
- Renders `<button>`.
- Focus ring on `:focus-visible` only (mouse clicks do not show ring).
- `disabled` sets `aria-disabled="true"` and `disabled` attribute.
- `loading` sets `aria-busy="true"`.
- `aria-label` overrides visible text.
- Tappable region: 56×56px minimum (mobile/tablet), 40px height (desktop).

**Dependencies:** None.

---

### 1.5 `Input`

**Category:** Atom
**File:** `src/components/atoms/Input/Input.tsx`
**Owner:** Forms

**Purpose:** A form input field. Five input types: text, number, date, textarea, searchable-select (the last is a composition of an input + a listbox).

**Props:**

```ts
type InputType = "text" | "number" | "email" | "tel" | "date" | "textarea" | "search";

interface InputProps {
  type?: InputType;            // default: "text"
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  onFocus?: () => void;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  invalid?: boolean;           // controlled invalid state
  id?: string;
  name?: string;
  autoComplete?: string;
  inputMode?: "text" | "numeric" | "decimal" | "email" | "tel" | "search";
  min?: number;
  max?: number;
  step?: number;
  rows?: number;               // textarea only
  className?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  ariaInvalid?: boolean;
  ariaRequired?: boolean;
}
```

**Variants:** 7 input types.

**States:**
- Default — 1px border `var(--color-rule-strong)`.
- Hover — border `var(--color-ink-40)`.
- Focus — border `var(--color-ink)`, focus ring on `:focus-visible`.
- Active/Pressed — same as focus.
- Disabled — background `var(--color-ink-8)`, border `var(--color-rule)`, text `var(--color-ink-40)`, cursor `not-allowed`.
- Loading — N/A (form-level).
- Error — border `var(--color-negative)`, `aria-invalid="true"`.
- Empty — placeholder visible.
- Read-only — background `var(--color-paper)`, border `var(--color-rule)`, no focus ring.

**Tokens:** `--space-2`, `--space-3`, `--type-body`, `--type-mono`, `--color-paper`, `--color-ink`, `--color-rule`, `--color-rule-strong`, `--color-ink-40`, `--color-ink-8`, `--color-negative`, `--focus-color`, `--touch-min`, `--radius-none`.

**Accessibility:**
- Renders `<input>` or `<textarea>`.
- `aria-invalid` set when `invalid` prop is true.
- `aria-required` set when `required` prop is true.
- `aria-describedby` links to error message or hint.
- Label association via `id` (set by parent `FormField`).
- Touch target: 56×56px minimum tappable region.

**Dependencies:** None.

---

### 1.6 `Label`

**Category:** Atom
**File:** `src/components/atoms/Label/Label.tsx`
**Owner:** Forms

**Purpose:** A form field label. Always mono, always uppercase, always above the field. The only label component in the product.

**Props:**

```ts
interface LabelProps {
  htmlFor: string;             // required: id of the associated input
  children: React.ReactNode;
  required?: boolean;          // shows asterisk
  className?: string;
}
```

**Variants:** None. Always `type.label` style (mono 12px uppercase, `var(--color-ink-60)`).

**States:** None.

**Tokens:** `--type-label`, `--color-ink-60`.

**Accessibility:**
- Renders `<label>` with `htmlFor` pointing to the input's `id`.
- `required` adds a visual `*` and sets `aria-required="true"` on the associated input (via parent coordination).

**Dependencies:** None.

---

### 1.7 `Checkbox`

**Category:** Atom
**File:** `src/components/atoms/Checkbox/Checkbox.tsx`
**Owner:** Forms

**Purpose:** A boolean input. Three visual states: unchecked, checked, indeterminate.

**Props:**

```ts
interface CheckboxProps {
  checked: boolean;
  indeterminate?: boolean;     // overrides checked visual
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  id?: string;
  name?: string;
  required?: boolean;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}
```

**Variants:** None. Single component with three internal visual states.

**States:**
- Default — unchecked (square outline), checked (filled square with checkmark), indeterminate (filled square with dash).
- Hover — border `var(--color-ink-40)`.
- Focus — focus ring.
- Active/Pressed — `opacity: var(--opacity-pressed)`.
- Disabled — `var(--color-ink-40)`, no interaction.
- Loading — N/A.
- Error — N/A (use invalid form state).
- Empty — N/A (always one of three states).
- Read-only — visual state preserved, no interaction.

**Tokens:** `--color-ink`, `--color-paper`, `--color-accent`, `--color-ink-40`, `--color-ink-8`, `--focus-color`, `--touch-min`.

**Accessibility:**
- Renders `<input type="checkbox">` (hidden) + visual `<span>`.
- `indeterminate` sets the DOM property (not HTML attribute).
- `aria-checked` reflects state.
- Touch target: 56×56px tappable region (visible box is 16×16px).

**Dependencies:** None.

---

### 1.8 `Radio`

**Category:** Atom
**File:** `src/components/atoms/Radio/Radio.tsx`
**Owner:** Forms

**Purpose:** A single-select input within a radio group. Used for small option sets (≤5).

**Props:**

```ts
interface RadioProps {
  checked: boolean;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  name: string;                // shared across the group
  id?: string;
  required?: boolean;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}
```

**Variants:** None.

**States:**
- Default — unchecked (circle outline), checked (filled circle with center dot).
- Hover — border `var(--color-ink-40)`.
- Focus — focus ring.
- Active/Pressed — `opacity: var(--opacity-pressed)`.
- Disabled — `var(--color-ink-40)`, no interaction.
- Loading — N/A.
- Error — N/A.
- Empty — N/A.
- Read-only — N/A.

**Tokens:** `--color-ink`, `--color-paper`, `--color-accent`, `--color-ink-40`, `--color-ink-8`, `--focus-color`, `--touch-min`.

**Accessibility:**
- Renders `<input type="radio">` (hidden) + visual `<span>`.
- Arrow key navigation within the group is handled by the parent (or natively by the browser if using `<input type="radio">`).
- Touch target: 56×56px tappable region.

**Dependencies:** None.

---

### 1.9 `Select`

**Category:** Atom
**File:** `src/components/atoms/Select/Select.tsx`
**Owner:** Forms

**Purpose:** A single-select input for large option sets (>5). Two variants: default (native select) and searchable (custom combobox).

**Props:**

```ts
type SelectVariant = "default" | "searchable";

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps {
  variant?: SelectVariant;     // default: "default"
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
  name?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}
```

**Variants:** 2.

**States:**
- Default — closed (shows selected value or placeholder).
- Hover — border `var(--color-ink-40)`.
- Focus — border `var(--color-ink)`, focus ring.
- Active/Open — expanded (searchable only; default uses native).
- Disabled — `var(--color-ink-40)`, no interaction.
- Loading — N/A.
- Error — border `var(--color-negative)`.
- Empty — placeholder shown.
- Read-only — visual state preserved, no interaction.

**Tokens:** `--space-2`, `--space-3`, `--type-body`, `--color-paper`, `--color-ink`, `--color-rule`, `--color-rule-strong`, `--color-ink-40`, `--color-ink-8`, `--color-negative`, `--color-accent`, `--focus-color`, `--z-overlay` (for dropdown), `--touch-min`, `--radius-none`.

**Accessibility:**
- Default variant: renders native `<select>`.
- Searchable variant: renders `combobox` ARIA pattern (`role="combobox"`, `aria-expanded`, `aria-controls`).
- Arrow keys navigate options; Enter selects; Escape closes.
- Touch target: 56×56px.

**Dependencies:** None (default), `Input` for the searchable variant's text field (optional composition, may inline).

---

### 1.10 `Tooltip`

**Category:** Atom
**File:** `src/components/atoms/Tooltip/Tooltip.tsx`
**Owner:** Overlays

**Purpose:** A hover-revealed supplementary text. Used sparingly: keyboard hints, dismissable info, model version on hover.

**Props:**

```ts
type TooltipPlacement = "top" | "bottom" | "left" | "right" | "auto";

interface TooltipProps {
  content: React.ReactNode;
  placement?: TooltipPlacement;  // default: "auto"
  delay?: number;                // ms, default: 240
  children: React.ReactElement;   // the trigger element
  className?: string;
}
```

**Variants:** 5 placements.

**States:**
- Default — not visible.
- Hover (240ms) — fades in at `var(--motion-enter)`.
- Focus — also visible on keyboard focus (per WAI-ARIA tooltip pattern).
- Active — visible.
- Disabled — N/A.
- Loading — N/A.
- Error — N/A.
- Empty — N/A.
- Read-only — N/A.

**Tokens:** `--space-2`, `--space-3`, `--type-body-small`, `--color-ink`, `--color-paper`, `--motion-enter`, `--z-tooltip`, `--radius-none`.

**Accessibility:**
- Renders the trigger element with `aria-describedby` pointing to the tooltip.
- Tooltip has `role="tooltip"`.
- Visible on focus (keyboard users see it).
- Dismissible with Escape.

**Dependencies:** None.

---

### 1.11 `Badge`

**Category:** Atom
**File:** `src/components/atoms/Badge/Badge.tsx`
**Owner:** Atoms

**Purpose:** A small numeric or status indicator. Used in nav for unread counts, in the breadcrumb for status.

**Props:**

```ts
type BadgeVariant = "numeric" | "status-success" | "status-warning" | "status-error" | "status-neutral";

interface BadgeProps {
  variant: BadgeVariant;
  value?: number;                // numeric only
  max?: number;                  // shows "99+" if value > max, default: 99
  className?: string;
  ariaLabel?: string;
}
```

**Variants:** 5.

**States:** None (always visible when present).

**Tokens:** `--type-data-small`, `--color-ink`, `--color-positive`, `--color-negative`, `--color-accent`, `--color-rule-strong`.

**Accessibility:**
- Renders `<span>`.
- `aria-label` provides full text (e.g., "5 unread assessments" instead of "5").

**Dependencies:** None.

---

### 1.12 `Link`

**Category:** Atom
**File:** `src/components/atoms/Link/Link.tsx`
**Owner:** Atoms

**Purpose:** A text link. Always underlined. The only navigation-by-click element besides `Button`.

**Props:**

```ts
type LinkVariant = "default" | "subtle" | "in-list";

interface LinkProps {
  href: string;
  variant?: LinkVariant;         // default: "default"
  external?: boolean;            // opens in new tab
  children: React.ReactNode;
  className?: string;
  ariaLabel?: string;
  ariaCurrent?: "page" | "step" | "location" | "date" | "time" | "true" | "false";
  prefetch?: boolean;            // router-level, default: true
}
```

**Variants:** 3.

**States:**
- Default — underlined, `var(--color-ink)`.
- Hover — `var(--color-accent)`, underline 1px.
- Focus — focus ring.
- Active/Pressed — `var(--color-accent)`, underline 2px.
- Disabled — `var(--color-ink-40)`, no underline, no interaction.
- Loading — N/A.
- Error — N/A.
- Empty — N/A.
- Read-only — N/A.

**Tokens:** `--type-body`, `--type-body-small`, `--color-ink`, `--color-accent`, `--color-ink-40`, `--motion-exit`, `--focus-color`.

**Accessibility:**
- Renders `<a>` for external links, router `<Link>` for internal.
- `external` adds `target="_blank" rel="noopener noreferrer"`.
- `aria-current="page"` on the current section link.
- Always underlined. Visited state is the same as default (no purple).

**Dependencies:** Router.

---

### 1.13 `Kbd`

**Category:** Atom
**File:** `src/components/atoms/Kbd/Kbd.tsx`
**Owner:** Atoms

**Purpose:** A keyboard shortcut indicator. Used in audit footer, search field, and tooltip hints.

**Props:**

```ts
interface KbdProps {
  children: React.ReactNode;     // e.g., "/", "Enter", "Cmd+K"
  className?: string;
}
```

**Variants:** None. Single style (mono 12px, `var(--color-ink-60)`, no background).

**States:** None.

**Tokens:** `--type-mono-small`, `--color-ink-60`.

**Accessibility:**
- Renders `<kbd>`.
- No interaction; display only.

**Dependencies:** None.

---

### 1.14 `LoadingCounter`

**Category:** Atom (State)
**File:** `src/components/atoms/LoadingCounter/LoadingCounter.tsx`
**Owner:** States

**Purpose:** A typographic loading indicator. The only loading state component. Replaces `Spinner` (forbidden).

**Props:**

```ts
interface LoadingCounterProps {
  message: string;              // e.g., "Loading 4 of 7 signals…"
  maxWaitMs?: number;           // default: 30000
  className?: string;
  ariaLabel?: string;
}
```

**Variants:** None. Single style (mono 14px, `var(--color-ink)`, no animation).

**States:**
- Loading (default) — message visible.
- Timeout — after `maxWaitMs`, an error state replaces it (handled by parent).
- Static — does not animate.

**Tokens:** `--type-mono`, `--color-ink`.

**Accessibility:**
- Renders `<div role="status" aria-live="polite">`.
- Screen reader announces the message.

**Dependencies:** None.

---

### 1.15 `MetadataStrip`

**Category:** Atom
**File:** `src/components/atoms/MetadataStrip/MetadataStrip.tsx`
**Owner:** Decision Spine

**Purpose:** A horizontal strip of metadata (timestamp, model version, correlation ID) that appears in the applicant identity block on the decision spine.

**Props:**

```ts
interface MetadataItem {
  label: string;                // e.g., "Generated", "Model", "Correlation ID"
  value: string;                // the value to display
  copyable?: boolean;           // shows copy button on hover
  truncated?: boolean;          // show truncated with hover for full
}

interface MetadataStripProps {
  items: MetadataItem[];        // 3-5 items
  className?: string;
  ariaLabel?: string;           // default: "Audit metadata"
}
```

**Variants:** None. Single style (mono 14px, `var(--color-ink-80)`).

**States:**
- Default — items visible, separated by `Rule` (hairline).
- Hover (on copyable item) — copy button appears.
- Focus — same as hover.
- Active/Pressed — copy button active.
- Disabled — N/A.
- Loading — N/A.
- Error — N/A.
- Empty — N/A.
- Read-only — default.

**Tokens:** `--type-mono`, `--color-ink-80`, `--color-rule`, `--color-accent`, `--motion-exit`, `--focus-color`.

**Accessibility:**
- Renders `<div role="region" aria-label={ariaLabel}>`.
- Each item is a `<span>` with the value.
- Copyable items render a `<button>` (hidden until hover/focus) with `aria-label="Copy [label]"`.

**Dependencies:** `Rule`, `Kbd` (optional, for shortcut hint).

---

## 2. Molecules

### 2.1 `VerdictBlock`

**Category:** Molecule
**File:** `src/components/molecules/VerdictBlock/VerdictBlock.tsx`
**Owner:** Decision Spine

**Purpose:** The hero verdict display. The largest type on the decision spine. Composes verdict text, confidence frame, override flags, and the primary action row (Approve / Decline / Escalate).

**Props:**

```ts
interface VerdictBlockProps {
  verdict: string;              // e.g., "Moderately Ready"
  band?: "Ready" | "Moderately Ready" | "Needs Improvement" | "Not Ready";
  probability?: number;         // 0..1
  probabilityRange?: [number, number];
  overrideFlags?: string[];     // e.g., ["E5_FLOOR_BREACH"]
  actions?: Array<{
    label: string;
    variant: "primary" | "secondary" | "tertiary";
    onClick: () => void;
    disabled?: boolean;
  }>;
  privacyMode?: boolean;
  className?: string;
}
```

**Composition:** `Text` (verdict), `ConfidenceFrame`, `Tag` × N (override flags), `Button` × N (actions).

**States:**
- Default — full display.
- Loading — verdict slot shows `—`; actions disabled.
- Error — verdict replaced with error state; actions disabled.
- Empty — N/A (verdict is always present after assessment).
- Privacy — verdict remains visible (the verdict is not PII; the applicant name is).

**Tokens:** `--type-display*`, `--type-mono`, `--color-accent`, `--color-ink`, `--color-ink-60`, `--color-positive`, `--color-negative`, `--space-7`, `--space-9`.

**Accessibility:**
- The verdict is the page's H1.
- Actions have visible focus rings.
- Override flags are `Tag` components with `aria-label` describing the flag.

**Dependencies:** `Text`, `ConfidenceFrame`, `Tag`, `Button`.

---

### 2.2 `ConfidenceFrame`

**Category:** Molecule
**File:** `src/components/molecules/ConfidenceFrame/ConfidenceFrame.tsx`
**Owner:** Decision Spine

**Purpose:** A single-line display of probability and range, plus override flags. Sits between the verdict and the drivers.

**Props:**

```ts
interface ConfidenceFrameProps {
  probability?: number;         // 0..1
  range?: [number, number];     // e.g., [0.61, 0.74]
  overrideFlags?: string[];     // rendered as Tag row
  className?: string;
}
```

**Composition:** `Text` (mono, probability + range), `Tag` × N (override flags).

**States:**
- Default — text + flags visible.
- Loading — "—" placeholder.
- Privacy — N/A.

**Tokens:** `--type-mono`, `--color-ink`, `--color-ink-60`, `--color-positive`, `--color-negative`, `--color-accent`.

**Accessibility:**
- Renders `<div role="group" aria-label="Decision confidence">`.
- Override flags are individually focusable via `Tab`.

**Dependencies:** `Text`, `Tag`.

---

### 2.3 `DriverList`

**Category:** Molecule
**File:** `src/components/molecules/DriverList/DriverList.tsx`
**Owner:** Decision Spine

**Purpose:** A ranked list of the top 3–5 factors that influenced the verdict. Each driver is a row (not a card).

**Props:**

```ts
interface Driver {
  name: string;                 // e.g., "Annual income"
  value: string;                // e.g., "₹1,20,000"
  contribution: number;         // signed: -1.0..+1.0
  isLargestPositive?: boolean;
  isLargestNegative?: boolean;
}

interface DriverListProps {
  drivers: Driver[];            // 3-5 items
  className?: string;
  ariaLabel?: string;           // default: "Top drivers"
}
```

**Composition:** `DriverItem` × N, `Rule` between items.

**States:**
- Default — full list visible.
- Loading — `LoadingCounter` inside.
- Empty — N/A (drivers are always present).
- Privacy — N/A.

**Tokens:** `--type-body`, `--type-data`, `--type-mono`, `--color-ink`, `--color-accent`, `--color-negative`, `--color-rule`, `--space-3`, `--space-4`.

**Accessibility:**
- Renders `<ol role="list" aria-label={ariaLabel}>`.
- Each item is a `<li>`.

**Dependencies:** `DriverItem`, `Rule`, `LoadingCounter`.

---

### 2.4 `DriverItem`

**Category:** Molecule
**File:** `src/components/molecules/DriverItem/DriverItem.tsx`
**Owner:** Decision Spine

**Purpose:** A single factor: name, value, sign indicator, contribution bar. A row, not a card.

**Props:**

```ts
interface DriverItemProps {
  name: string;
  value: string;
  contribution: number;         // signed
  isLargestPositive?: boolean;
  isLargestNegative?: boolean;
  className?: string;
}
```

**Composition:** `Text` × 3 (name, value, sign), contribution bar (CSS only).

**States:**
- Default — full row.
- Hover — no visual change (not interactive).
- Privacy — N/A.

**Tokens:** `--type-body`, `--type-data`, `--type-mono`, `--color-ink`, `--color-accent`, `--color-negative`, `--space-2`, `--space-3`.

**Accessibility:**
- Renders `<li>`.
- Sign indicator `+`/`−` in mono, 12pt, `var(--color-ink-60)`.
- Color is the third redundant signal (per M18); not the primary.

**Dependencies:** `Text`.

---

### 2.5 `RecommendationsList`

**Category:** Molecule
**File:** `src/components/molecules/RecommendationsList/RecommendationsList.tsx`
**Owner:** Decision Spine

**Purpose:** A list of recommended next actions. Semantically distinct from `DriverList` (action vs. mechanism). Adjacent to drivers, separated by a hairline and a label.

**Props:**

```ts
interface Recommendation {
  action: string;               // e.g., "Verify income before final decision"
  severity?: "low" | "medium" | "high";
  tag?: string;                 // optional Tag text
}

interface RecommendationsListProps {
  recommendations: Recommendation[];
  className?: string;
  ariaLabel?: string;           // default: "What to do"
}
```

**Composition:** `Text` (label), `Recommendation` × N, `Rule` between items.

**States:**
- Default — full list.
- Loading — `LoadingCounter` inside.
- Empty — N/A.

**Tokens:** `--type-subheading`, `--type-body`, `--color-ink`, `--color-accent`, `--color-positive`, `--color-negative`, `--color-rule`, `--space-2`, `--space-3`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<section aria-labelledby="recommendations-heading">`.
- Heading is H2.

**Dependencies:** `Text`, `Rule`, `Tag`, `LoadingCounter`.

---

### 2.6 `BreakdownTable`

**Category:** Molecule
**File:** `src/components/molecules/BreakdownTable/BreakdownTable.tsx`
**Owner:** Decision Spine

**Purpose:** A tabular view of input fields and their contributions. Renders as a table on tablet/desktop, a stacked list on mobile.

**Props:**

```ts
interface BreakdownRow {
  field: string;                // e.g., "annual_income"
  displayName: string;          // e.g., "Annual income"
  value: string | number;
  contribution?: number;        // signed, optional
  imputed?: boolean;            // shows "imputed" indicator
  imputationNote?: string;      // e.g., "Income imputed as ₹4,200/mo from monthly expenses"
}

interface BreakdownTableProps {
  rows: BreakdownRow[];
  className?: string;
  ariaLabel?: string;
}
```

**Composition:** Table on tablet/desktop, stacked list on mobile. Per-row components: `Text` × 3, optional `Tag` (imputed).

**States:**
- Default — full table/list.
- Loading — `LoadingCounter` inside a `DomainSection`.
- Empty — `EmptyState` inside the section.

**Tokens:** `--type-body`, `--type-data`, `--type-mono`, `--type-mono-small`, `--color-ink`, `--color-ink-60`, `--color-ink-40`, `--color-accent`, `--color-negative`, `--color-rule`, `--space-2`, `--space-3`, `--space-4`.

**Accessibility:**
- Renders `<table>` on tablet/desktop with `<thead>`, `<tbody>`, `<th scope="col">`, `<th scope="row">`.
- Renders `<ul>` on mobile.
- `aria-label` describes the table.
- Imputed values have an `aria-describedby` linking to the imputation note.

**Dependencies:** `Text`, `Tag`, `Rule`, `LoadingCounter`, `EmptyState`.

---

### 2.7 `DomainSection`

**Category:** Molecule
**File:** `src/components/molecules/DomainSection/DomainSection.tsx`
**Owner:** Decision Spine

**Purpose:** A collapsible group of related breakdown fields (e.g., Financial Health, Risk Tier, Archetype).

**Props:**

```ts
interface DomainSectionProps {
  id: string;                   // for aria-labelledby
  heading: string;              // e.g., "Financial health"
  defaultExpanded?: boolean;    // default: true
  children: React.ReactNode;    // BreakdownTable or list
  className?: string;
}
```

**Composition:** `Text` (heading), `Rule`, `Button` (expand/collapse trigger), children.

**States:**
- Default — expanded (if `defaultExpanded`).
- Collapsed — children hidden, button shows "Show".
- Loading — children replaced by `LoadingCounter`.

**Tokens:** `--type-subheading`, `--type-body`, `--color-ink`, `--color-rule`, `--color-accent`, `--space-3`, `--space-4`, `--space-5`, `--motion-enter`, `--focus-color`.

**Accessibility:**
- Renders `<section aria-labelledby={id}>`.
- Heading is H3.
- Expand/collapse button has `aria-expanded`, `aria-controls={contentId}`.
- Collapsed content has `hidden` attribute (not `display: none`).

**Dependencies:** `Text`, `Rule`, `Button`, `LoadingCounter`.

---

### 2.8 `ApplicantIdentity`

**Category:** Molecule
**File:** `src/components/molecules/ApplicantIdentity/ApplicantIdentity.tsx`
**Owner:** Decision Spine

**Purpose:** The applicant identity block at the top of the decision spine. Renders name, age, business, loan request. Supports privacy mode.

**Props:**

```ts
interface ApplicantIdentityProps {
  name: string;
  age: number;
  business: string;
  loanRequest: string;
  generatedAt: string;          // ISO 8601
  privacyMode?: boolean;
  className?: string;
  ariaLabel?: string;           // default: "Applicant identity"
}
```

**Composition:** `Text` × N (name, details), `MetadataStrip` (timestamp, model version, correlation ID, decision version, schema version), `Rule` (hairline below).

**States:**
- Default — full identity + metadata strip.
- Loading — name placeholder ("—"), metadata strip loading.
- Privacy — name → monogram, age → band, business → category, loan → band. Correlation ID preserved.
- Empty — N/A.

**Tokens:** `--type-subheading`, `--type-body`, `--type-mono`, `--color-ink`, `--color-ink-60`, `--color-ink-80`, `--color-rule`, `--space-3`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<header aria-label={ariaLabel}>`.
- The name is the H2 (per accessibility tree).
- Privacy mode: each redacted field has `aria-label` describing the redaction (e.g., "Redacted: applicant name").
- `MetadataStrip` is a nested `role="region"`.

**Dependencies:** `Text`, `MetadataStrip`, `Rule`.

---

### 2.9 `AuditFooter`

**Category:** Molecule
**File:** `src/components/molecules/AuditFooter/AuditFooter.tsx`
**Owner:** Global

**Purpose:** The page-bottom audit metadata. Always rendered. Full version with model lineage, decision version, schema version, timestamp, correlation ID.

**Props:**

```ts
interface AuditFooterProps {
  modelVersion: string;
  decisionVersion: string;
  schemaVersion: string;
  timestamp: string;            // ISO 8601
  correlationId: string;
  userId?: string;
  institutionId?: string;
  className?: string;
  ariaLabel?: string;           // default: "Audit metadata"
}
```

**Composition:** `Text` × N (mono), `Rule` (top border), `Kbd` (optional shortcut hint), `Link` (full audit log).

**States:**
- Default — full footer.
- Loading — N/A (footer is always present).
- Error — N/A.

**Tokens:** `--type-mono`, `--color-ink-80`, `--color-rule`, `--color-accent`, `--space-7`, `--space-5`.

**Accessibility:**
- Renders `<footer aria-label={ariaLabel}>`.
- All text is mono 14pt, 80% alpha (per M4 fix).
- Correlation ID is a `<button>` (copyable) with `aria-label="Copy correlation ID"`.
- Full audit log link is a `Link` component.

**Dependencies:** `Text`, `Rule`, `Kbd`, `Link`, `Button` (for copy).

---

### 2.10 `FilterDisclosure`

**Category:** Molecule
**File:** `src/components/molecules/FilterDisclosure/FilterDisclosure.tsx`
**Owner:** History

**Purpose:** A collapsible filter panel for the history list. Replaces `FilterBar`. Trigger is a single text link; expanded state shows date range, type, verdict, applicant name fields.

**Props:**

```ts
interface FilterValues {
  from?: string;                // ISO date
  to?: string;                  // ISO date
  type?: "person_a" | "person_b";
  verdict?: "Ready" | "Moderately Ready" | "Needs Improvement" | "Not Ready";
  applicantName?: string;
}

interface FilterDisclosureProps {
  values: FilterValues;
  onChange: (values: FilterValues) => void;
  defaultExpanded?: boolean;    // default: false
  className?: string;
  ariaLabel?: string;           // default: "Filter assessments"
}
```

**Composition:** `Button` (trigger), `Rule`, `FormField` × N (date range, type select, verdict select, applicant name input).

**States:**
- Default — collapsed (trigger visible).
- Expanded — fields visible, filter applied in real time.
- Loading — N/A.
- Error — N/A (form-level).
- Privacy — N/A.

**Tokens:** `--type-body`, `--type-mono`, `--color-ink`, `--color-rule`, `--color-accent`, `--space-2`, `--space-3`, `--space-4`, `--motion-enter`, `--focus-color`.

**Accessibility:**
- Renders `<div role="group" aria-label={ariaLabel}>`.
- Trigger button has `aria-expanded`, `aria-controls={contentId}`.
- Fields are real `Input` and `Select` components with full label association.
- Filters apply in real time (no Apply button). The user does not need to confirm.

**Dependencies:** `Button`, `Rule`, `FormField` (composed of `Label` + `Input` + `Select`).

---

### 2.11 `HistoryItem`

**Category:** Molecule
**File:** `src/components/molecules/HistoryItem/HistoryItem.tsx`
**Owner:** History

**Purpose:** A single item in the history list. A typographic block: name, date, verdict band, one-line top driver summary. Replaces `HistoryRow` (a table row).

**Props:**

```ts
interface HistoryItemProps {
  id: string;                   // assessment ID
  applicantName: string;
  userType: "person_a" | "person_b";
  verdict: "Ready" | "Moderately Ready" | "Needs Improvement" | "Not Ready";
  date: string;                 // ISO 8601
  topDriverSummary: string;     // e.g., "Income imputed as ₹4,200/mo"
  privacyMode?: boolean;
  className?: string;
}
```

**Composition:** `Link` (wraps the row), `Text` × N (name, date, summary), `Tag` (verdict band).

**States:**
- Default — full item visible.
- Hover — link underline appears (the item is a link).
- Focus — focus ring on the link.
- Active/Pressed — link active state.
- Loading — skeleton (`LoadingCounter` with "Loading…").
- Privacy — applicant name → monogram; verdict band preserved.
- Empty — N/A.

**Tokens:** `--type-body`, `--type-body-small`, `--type-mono`, `--color-ink`, `--color-ink-60`, `--color-accent`, `--color-positive`, `--color-negative`, `--color-rule`, `--space-3`, `--space-5`, `--focus-color`, `--touch-min`.

**Accessibility:**
- Renders `<li>` containing a `<Link>` (anchor).
- `aria-label` on the link: "View assessment for [name], [verdict], [date]".
- Touch target: 56×56px tappable region (the entire row).

**Dependencies:** `Link`, `Text`, `Tag`, `LoadingCounter`.

---

### 2.12 `SearchField`

**Category:** Molecule
**File:** `src/components/molecules/SearchField/SearchField.tsx`
**Owner:** Global

**Purpose:** A search input in the top bar, with a results dropdown. Replaces `CommandPalette` (Cmd-K modal). Keyboard shortcut: `/` to focus.

**Props:**

```ts
interface SearchResult {
  id: string;
  type: "assessment" | "applicant" | "report";
  label: string;
  href: string;
}

interface SearchFieldProps {
  onSearch: (query: string) => Promise<SearchResult[]>;
  placeholder?: string;         // default: "Search assessments, applicants, reports…"
  shortcut?: string;            // default: "/"
  maxResults?: number;          // default: 10
  className?: string;
  ariaLabel?: string;           // default: "Search"
}
```

**Composition:** `Input` (text), result dropdown (`Link` × N).

**States:**
- Default — input visible, no results.
- Focus — input focused, `/` shortcut triggered.
- Typing — debounced 200ms, results render in dropdown.
- Results shown — dropdown visible.
- No results — "No results for 'query'." (per empty state).
- Loading — `LoadingCounter` in dropdown.
- Error — N/A (form-level).

**Tokens:** `--type-body`, `--type-mono`, `--color-ink`, `--color-ink-60`, `--color-accent`, `--color-rule`, `--color-paper`, `--space-2`, `--space-3`, `--motion-enter`, `--z-overlay`, `--focus-color`, `--touch-min`, `--radius-none`.

**Accessibility:**
- Renders `<div role="search">`.
- Input has `role="combobox"`, `aria-expanded`, `aria-controls={listboxId}`.
- Results list is `<ul role="listbox">`.
- Arrow keys navigate results; Enter selects; Escape closes.
- `aria-live="polite"` announces result count.

**Dependencies:** `Input`, `Link`, `Text`, `LoadingCounter`, `EmptyState`.

---

### 2.13 `ConnectionIndicator`

**Category:** Molecule
**File:** `src/components/molecules/ConnectionIndicator/ConnectionIndicator.tsx`
**Owner:** Global

**Purpose:** The top-bar network state indicator. Typographic only. No colored dots. Three states: connected, reconnecting, offline.

**Props:**

```ts
type ConnectionState = "connected" | "reconnecting" | "offline";

interface ConnectionIndicatorProps {
  state: ConnectionState;
  className?: string;
  ariaLabel?: string;           // default: "Connection status"
}
```

**Composition:** `Text` (mono), `Tag` (state).

**States:**
- Connected — no visible indicator (or "Connected" in mono 12pt).
- Reconnecting — "Reconnecting…" in mono.
- Offline — "Offline — your work is saved." in mono.
- Loading — N/A.
- Error — N/A.

**Tokens:** `--type-mono`, `--type-mono-small`, `--color-ink`, `--color-ink-60`, `--color-negative`, `--space-2`, `--space-3`.

**Accessibility:**
- Renders `<div role="status" aria-live="polite" aria-label={ariaLabel}>`.
- Screen reader announces state changes.

**Dependencies:** `Text`, `Tag`.

---

### 2.14 `EmptyState`

**Category:** Molecule
**File:** `src/components/molecules/EmptyState/EmptyState.tsx`
**Owner:** States

**Purpose:** An empty list or no-results state. One line of text, one optional text link. Two lines maximum.

**Props:**

```ts
interface EmptyStateProps {
  message: string;              // one line, e.g., "No assessments in this date range."
  actionLabel?: string;         // optional link text
  actionHref?: string;          // optional link href
  onAction?: () => void;        // optional click handler
  className?: string;
}
```

**Composition:** `Text` (one line), optional `Link`.

**States:** None (always visible when present).

**Tokens:** `--type-body-large`, `--color-ink-60`, `--color-accent`, `--space-3`, `--space-5`.

**Accessibility:**
- Renders `<div role="status">`.
- The action link is a `Link` component with full keyboard support.

**Dependencies:** `Text`, `Link`.

---

### 2.15 `ErrorBoundary`

**Category:** Molecule
**File:** `src/components/molecules/ErrorBoundary/ErrorBoundary.tsx`
**Owner:** States

**Purpose:** A React error boundary fallback. Three levels: root, route, component. Each level has appropriate copy.

**Props:**

```ts
type ErrorLevel = "root" | "route" | "component";

interface ErrorBoundaryProps {
  level: ErrorLevel;
  error?: Error;
  onRetry?: () => void;
  onSignOut?: () => void;
  correlationId?: string;
  children?: React.ReactNode;   // not used directly; wraps via <ErrorBoundary> from react-error-boundary
}
```

**Composition:** `Text` × N (heading, message, correlation ID), `Button` × N (retry, sign out), `Rule` (top border).

**States:**
- Default — error display.
- Loading — N/A.
- Empty — N/A.

**Tokens:** `--type-heading`, `--type-body`, `--type-mono`, `--color-ink`, `--color-ink-60`, `--color-negative`, `--color-accent`, `--color-rule`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<div role="alert" aria-live="assertive">`.
- Heading is H1 (root) or H2 (route/component).
- Correlation ID is copyable.
- Focus moves to the heading on render.

**Dependencies:** `Text`, `Button`, `Rule`.

---

### 2.16 `ReportPanel`

**Category:** Molecule
**File:** `src/components/molecules/ReportPanel/ReportPanel.tsx`
**Owner:** Report

**Purpose:** The report generation page content. Shows loading state, success state (download button, open PDF link), error state.

**Props:**

```ts
interface ReportPanelProps {
  state: "idle" | "generating" | "ready" | "error";
  reportId?: string;
  pdfBlob?: Blob;
  correlationId?: string;
  errorMessage?: string;
  onDownload: () => void;
  onOpenPdf: () => void;
  onCancel: () => void;
  onBack: () => void;
  className?: string;
}
```

**Composition:** `Text` × N, `Button` × N (download, open, cancel, back), `LoadingCounter`, `Rule`.

**States:**
- Idle — "Generate report" button.
- Generating — `LoadingCounter`, "Cancel" button.
- Ready — "Download" and "Open PDF" buttons, correlation ID.
- Error — error message, "Retry" button, correlation ID.

**Tokens:** `--type-heading`, `--type-body`, `--type-mono`, `--color-ink`, `--color-ink-60`, `--color-accent`, `--color-negative`, `--color-rule`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<main aria-labelledby="report-heading">`.
- Heading is H1.
- Buttons have visible focus rings.

**Dependencies:** `Text`, `Button`, `LoadingCounter`, `Rule`.

---

### 2.17 `FormField`

**Category:** Molecule
**File:** `src/components/molecules/FormField/FormField.tsx`
**Owner:** Forms

**Purpose:** A composed form field: label + input + optional error or hint. The only way to render a form field in the product.

**Props:**

```ts
type FormFieldInput =
  | { kind: "input"; props: InputProps }
  | { kind: "select"; props: SelectProps }
  | { kind: "checkbox"; props: CheckboxProps }
  | { kind: "radio-group"; props: RadioGroupProps }
  | { kind: "textarea"; props: TextareaProps };

interface FormFieldProps {
  id: string;
  label: string;
  required?: boolean;
  hint?: string;                // help text below the field
  error?: string;               // error message (overrides hint when present)
  disabled?: boolean;
  input: FormFieldInput;
  className?: string;
}
```

**Composition:** `Label`, child input component, `Text` (hint or error).

**States:** Inherits from child input. Plus:
- Error — error message visible, child input marked invalid.
- Loading — N/A.
- Empty — N/A.

**Tokens:** `--type-label`, `--type-body-small`, `--color-ink`, `--color-ink-60`, `--color-negative`, `--space-1`, `--space-2`, `--space-3`.

**Accessibility:**
- Renders `<div>` containing `Label` + child + `Text` (hint/error).
- `Label` `htmlFor` points to child's `id`.
- Hint/error has `id={id}-hint` and `id={id}-error`; child has `aria-describedby` pointing to the active one.
- Error replaces hint visually and via `aria-describedby`.

**Dependencies:** `Label`, `Input`, `Select`, `Checkbox`, `Radio`, `Textarea` (composed), `Text`.

---

## 3. Organisms

### 3.1 `AppShell`

**Category:** Organism
**File:** `src/components/organisms/AppShell/AppShell.tsx`
**Owner:** Global

**Purpose:** The page shell. Renders top bar, optional left rail, content, and audit footer. Always renders top bar and audit footer.

**Props:**

```ts
interface AppShellProps {
  children: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];   // optional breadcrumb
  showLeftRail?: boolean;            // default: true (desktop), false (mobile)
  showBottomNav?: boolean;           // default: true (mobile), false (desktop)
  className?: string;
}

interface BreadcrumbItem {
  label: string;
  href?: string;                    // if omitted, the item is the current page
}
```

**Composition:** `TopBar`, `NavRail` (conditional), `MobileNav` (conditional), children, `AuditFooter`.

**States:**
- Default — full shell.
- Loading — children render `LoadingCounter`.
- Error — children replaced by `ErrorBoundary`.

**Tokens:** All shell-level tokens (--space-*, --color-*, --type-*).

**Accessibility:**
- Renders `<div className="app-shell">`.
- Top bar is `<header>`. Nav rail is `<nav aria-label="Primary">`. Main is `<main>`. Footer is `<footer>`.
- Skip links: "Skip to main content" → `<main>`. "Skip to audit footer" → `<footer>`. On decision spine: "Skip to verdict" → `<section id="verdict">`.

**Dependencies:** `TopBar`, `NavRail`, `MobileNav`, `AuditFooter`, all route organisms.

---

### 3.2 `TopBar`

**Category:** Organism
**File:** `src/components/organisms/TopBar/TopBar.tsx`
**Owner:** Global

**Purpose:** The top bar. Product monogram, search field, connection indicator, privacy toggle, user identity dropdown. 56px desktop, 48px mobile. Auto-hides on scroll-down on decision spine.

**Props:**

```ts
interface TopBarProps {
  productName?: string;             // default: "RiskIntel"
  privacyMode: boolean;
  onPrivacyToggle: () => void;
  user: {
    name: string;
    role: string;
    institution: string;
  };
  onSignOut: () => void;
  connectionState: ConnectionState;
  autoHide?: boolean;               // default: false (set true on decision spine)
  className?: string;
}
```

**Composition:** `Text` (monogram), `SearchField`, `ConnectionIndicator`, `Button` (privacy toggle), `Dropdown` (user identity), `Link` (sign out).

**States:**
- Default — fully visible.
- Auto-hide — `transform: translateY(-100%)` on scroll-down; reverse on scroll-up.
- Privacy — toggle is active.

**Tokens:** `--space-3`, `--space-4`, `--type-subheading`, `--type-body`, `--type-mono`, `--color-ink`, `--color-paper`, `--color-accent`, `--color-rule`, `--motion-enter`, `--z-sticky`, `--touch-min`.

**Accessibility:**
- Renders `<header>`.
- Privacy toggle has `aria-pressed`.
- User identity is a `<button aria-expanded aria-haspopup="menu">`.
- Sign out is a `Link` in the dropdown.
- Touch target: 56×56px for all interactive elements on mobile.

**Dependencies:** `Text`, `SearchField`, `ConnectionIndicator`, `Button`, `Link`, `Dropdown` (custom or native).

---

### 3.3 `NavRail`

**Category:** Organism
**File:** `src/components/organisms/NavRail/NavRail.tsx`
**Owner:** Global

**Purpose:** The left navigation rail. 32px collapsed, 200px expanded on hover/focus. Replaces `LeftRail`. Section-specific items.

**Props:**

```ts
type NavSection = "assess" | "history" | "settings";

interface NavRailProps {
  currentSection: NavSection;
  currentPath: string;
  onNavigate: (path: string) => void;
  className?: string;
}
```

**Composition:** `Link` × N (section items).

**States:**
- Default — 32px collapsed, icons only (typographic monogram labels).
- Hover — 200px expanded, full labels visible.
- Focus — same as hover (keyboard focus expands).
- Active — current section is underlined.

**Tokens:** `--space-2`, `--space-3`, `--type-body-small`, `--type-mono`, `--color-ink`, `--color-accent`, `--color-rule`, `--motion-enter`, `--z-sticky`.

**Accessibility:**
- Renders `<nav aria-label="Primary">`.
- `aria-current="page"` on the current section.
- Keyboard: Tab to focus, expands; arrow keys (if multi-item).
- Touch target: 56×56px on mobile (rail not used on mobile).

**Dependencies:** `Link`, `Text`.

---

### 3.4 `MobileNav`

**Category:** Organism
**File:** `src/components/organisms/MobileNav/MobileNav.tsx`
**Owner:** Global

**Purpose:** The mobile bottom navigation. 40px visible, 56×56px tappable. Auto-hides on decision spine only.

**Props:**

```ts
interface MobileNavProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  autoHide?: boolean;               // default: false
  className?: string;
}
```

**Composition:** `Link` × 4 (New, History, Settings, Sign Out).

**States:**
- Default — visible.
- Auto-hide — hidden on scroll-down (decision spine only).

**Tokens:** `--space-2`, `--type-mono-small`, `--color-ink`, `--color-accent`, `--color-rule`, `--motion-enter`, `--z-sticky`, `--touch-min`.

**Accessibility:**
- Renders `<nav aria-label="Primary">` (only visible on mobile, hidden on tablet+).
- `aria-current="page"` on the current section.
- Touch target: 56×56px.

**Dependencies:** `Link`.

---

### 3.5 `DecisionSpine`

**Category:** Organism
**File:** `src/components/organisms/DecisionSpine/DecisionSpine.tsx`
**Owner:** Routes

**Purpose:** The hero screen. Composes metadata strip, applicant identity, verdict block, driver list, recommendations, breakdown, audit footer. Renders the layout per FRONTEND_ARCHITECTURE_V1.1 §8.

**Props:**

```ts
interface DecisionSpineProps {
  assessment: Assessment;         // typed from OpenAPI
  privacyMode: boolean;
  onApprove: () => void;
  onDecline: () => void;
  onEscalate: () => void;         // stub in v1
  onGenerateReport: () => void;
  className?: string;
}
```

**Composition:** `MetadataStrip`, `ApplicantIdentity`, `VerdictBlock`, `DriverList`, `RecommendationsList`, `DomainSection` × N, `AuditFooter`.

**States:**
- Default — full spine.
- Loading — verdict slot "—", sections lazy-load.
- Error — replaced by `ErrorBoundary`.
- Privacy — applicant identity redacted.

**Tokens:** All `--type-*`, `--color-*`, `--space-*`. Layout per §8.

**Accessibility:**
- Renders `<main aria-labelledby="verdict-heading">`.
- Verdict is the H1.
- Each major section is a `<section>` with `aria-labelledby`.
- Skip link "Skip to verdict" present.
- Screen-reader structure per FRONTEND_ARCHITECTURE_V1.1 §3.3.

**Dependencies:** `MetadataStrip`, `ApplicantIdentity`, `VerdictBlock`, `DriverList`, `RecommendationsList`, `DomainSection`, `BreakdownTable`, `AuditFooter`, `Button`, `LoadingCounter`, `Rule`.

---

### 3.6 `IntakeForm`

**Category:** Organism
**File:** `src/components/organisms/IntakeForm/IntakeForm.tsx`
**Owner:** Routes

**Purpose:** The intake form for Person A or Person B. Composes form fields grouped into domain sections, with a submit button.

**Props:**

```ts
type IntakeType = "person_a" | "person_b";

interface IntakeFormProps {
  type: IntakeType;
  initialValues?: Record<string, unknown>;
  draftKey: string;               // for localStorage draft
  onSubmit: (values: Record<string, unknown>) => void;
  className?: string;
}
```

**Composition:** `FormField` × N (per schema), grouped into `DomainSection`, `Button` (submit).

**States:**
- Default — empty or restored from draft.
- Filling — fields validated on blur.
- Submitting — button "Submitting…", form not cleared.
- Success — navigates to decision spine.
- Error — server errors render, form preserved.

**Tokens:** All `--space-*`, `--type-*`, `--color-*`.

**Accessibility:**
- Renders `<form aria-labelledby="intake-heading">`.
- All fields have associated labels.
- First invalid field receives focus on submit error.
- Submit button has `aria-busy` during submission.

**Dependencies:** `FormField`, `DomainSection`, `Button`, `Rule`, `Text`, `LoadingCounter`.

---

### 3.7 `TypeSelector`

**Category:** Organism
**File:** `src/components/organisms/TypeSelector/TypeSelector.tsx`
**Owner:** Routes

**Purpose:** The intake type selector at `/assess/new`. Two text links side by side (or stacked on mobile), separated by a hairline. Replaces two cards (per M10).

**Props:**

```ts
interface TypeSelectorProps {
  onSelectPersonA: () => void;
  onSelectPersonB: () => void;
  defaultType?: "person_a" | "person_b";  // pre-selects one for MFI users
  className?: string;
}
```

**Composition:** `Link` × 2, `Text` (descriptions), `Rule` (vertical hairline between).

**States:**
- Default — both options visible.

**Tokens:** `--type-display-size`, `--type-display-mobile-size`, `--type-body`, `--color-ink`, `--color-accent`, `--color-rule`, `--space-5`, `--space-7`, `--space-9`, `--focus-color`.

**Accessibility:**
- Renders `<main aria-labelledby="type-selector-heading">`.
- Heading is H1: "Start a new assessment."
- Each link is a `<Link>` (anchor) with `aria-label`: "Person A, documented borrower. Start assessment."
- Keyboard: Tab between the two links.

**Dependencies:** `Link`, `Text`, `Rule`.

---

### 3.8 `HistoryList`

**Category:** Organism
**File:** `src/components/organisms/HistoryList/HistoryList.tsx`
**Owner:** Routes

**Purpose:** The history list. A chronological reading list with filter disclosure and load-more button. Replaces `HistoryTable`.

**Props:**

```ts
interface HistoryListProps {
  items: HistoryItemData[];       // typed from API
  filters: FilterValues;
  onFilterChange: (filters: FilterValues) => void;
  onLoadMore: () => void;
  hasMore: boolean;
  isLoading: boolean;
  isLoadingMore: boolean;
  scope: "own" | "team" | "institution";
  privacyMode: boolean;
  className?: string;
}
```

**Composition:** `Text` (scope label), `FilterDisclosure`, `HistoryItem` × N, `Button` (load more), `EmptyState` (when empty), `LoadingCounter` (when loading).

**States:**
- Default — list visible, items rendered.
- Loading — `LoadingCounter` above list.
- Loading more — `LoadingCounter` in load-more button.
- Empty — `EmptyState` (no assessments, or no filter match).
- Error — `ErrorBoundary`.
- Privacy — names redacted in `HistoryItem`.

**Tokens:** `--type-subheading`, `--type-body`, `--type-mono`, `--color-ink`, `--color-ink-60`, `--color-accent`, `--color-rule`, `--space-3`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<main aria-labelledby="history-heading">`.
- Heading is H1: "Decision history. [Scope]."
- The list is `<ol role="list">`.
- Load more is a `<Button>` with `aria-busy` during loading.
- Filter disclosure is a `FilterDisclosure` (collapsible).

**Dependencies:** `Text`, `FilterDisclosure`, `HistoryItem`, `Button`, `LoadingCounter`, `EmptyState`, `ErrorBoundary`.

---

### 3.9 `ReportPage`

**Category:** Organism
**File:** `src/components/organisms/ReportPage/ReportPage.tsx`
**Owner:** Routes

**Purpose:** The report generation page. A separate page (not a modal). Shows loading, ready, error states.

**Props:**

```ts
interface ReportPageProps {
  assessmentId: string;
  className?: string;
}
```

**Composition:** `ReportPanel`, `Text` (correlation ID, metadata), `Button` (back), `Rule`.

**States:** Inherits from `ReportPanel`.

**Tokens:** `--type-heading`, `--type-body`, `--type-mono`, `--color-ink`, `--color-accent`, `--color-rule`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<main aria-labelledby="report-heading">`.
- Heading is H1.

**Dependencies:** `ReportPanel`, `Text`, `Button`, `Rule`.

---

### 3.10 `SettingsPage`

**Category:** Organism
**File:** `src/components/organisms/SettingsPage/SettingsPage.tsx`
**Owner:** Routes

**Purpose:** The settings page. A single page with three sections (Profile, Defaults, Security), separated by hairlines. No sub-routes.

**Props:**

```ts
interface SettingsPageProps {
  user: UserData;
  preferences: PreferencesData;
  onSaveProfile: (data: ProfileData) => void;
  onSavePreferences: (data: PreferencesData) => void;
  onChangePassword: () => void;
  className?: string;
}
```

**Composition:** `FormField` × N per section, `Button` (save per section), `Rule` (between sections).

**States:**
- Default — sections visible, values populated.
- Editing — fields enabled.
- Saving — button "Saving…", disabled.
- Success — typographic "Saved." (no toast).
- Error — field-level errors or page-level error.

**Tokens:** `--type-subheading`, `--type-body`, `--type-label`, `--color-ink`, `--color-rule`, `--color-accent`, `--space-3`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<main aria-labelledby="settings-heading">`.
- Heading is H1: "Settings."
- Each section is `<section aria-labelledby="...">`.
- Save buttons have `aria-busy` during save.

**Dependencies:** `Text`, `FormField`, `Button`, `Rule`, `LoadingCounter`.

---

### 3.11 `SignIn`

**Category:** Organism
**File:** `src/components/organisms/SignIn/SignIn.tsx`
**Owner:** Auth

**Purpose:** The sign-in form. Three fields: email, password, institution code. "Forgot password" link.

**Props:**

```ts
interface SignInProps {
  from?: string;                  // redirect path after sign-in
  sessionExpired?: boolean;       // shows "Your session expired." message
  className?: string;
}
```

**Composition:** `Text` (heading, optional session-expired message), `FormField` × 3, `Button` (submit), `Link` (forgot).

**States:**
- Default — empty form.
- Filling — fields validated on blur.
- Submitting — button "Signing in…", disabled.
- Success — navigates to `from` or `/assess/new`.
- Error — form-level error or field-level errors.

**Tokens:** `--type-display-size`, `--type-display-mobile-size`, `--type-body`, `--type-mono`, `--color-ink`, `--color-accent`, `--color-rule`, `--color-negative`, `--space-3`, `--space-5`, `--space-7`, `--space-9`.

**Accessibility:**
- Renders `<main aria-labelledby="signin-heading">`.
- Heading is H1: "Sign in."
- All fields labeled.
- Forgot link is a `Link`.

**Dependencies:** `Text`, `FormField`, `Button`, `Link`, `Rule`.

---

### 3.12 `NotFound`

**Category:** Organism
**File:** `src/components/organisms/NotFound/NotFound.tsx`
**Owner:** Errors

**Purpose:** The 404 page. Plain text, hairline, back link. No illustration.

**Props:** None (uses router context for back link).

**Composition:** `Text` (heading, message), `Link` (back), `Rule`.

**States:** None.

**Tokens:** `--type-heading`, `--type-body`, `--color-ink`, `--color-accent`, `--color-rule`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<main aria-labelledby="notfound-heading">`.
- Heading is H1.

**Dependencies:** `Text`, `Link`, `Rule`.

---

### 3.13 `ServerError`

**Category:** Organism
**File:** `src/components/organisms/ServerError/ServerError.tsx`
**Owner:** Errors

**Purpose:** The 500 page. Plain text, correlation ID, retry button.

**Props:**

```ts
interface ServerErrorProps {
  correlationId?: string;
  onRetry?: () => void;
  className?: string;
}
```

**Composition:** `Text` × N, `Button` (retry), `Rule`.

**States:**
- Default — error display.
- Loading — N/A.

**Tokens:** `--type-heading`, `--type-body`, `--type-mono`, `--color-ink`, `--color-accent`, `--color-negative`, `--color-rule`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<main aria-labelledby="servererror-heading">`.
- Heading is H1.
- Correlation ID is copyable.

**Dependencies:** `Text`, `Button`, `Link`, `Rule`.

---

### 3.14 `SessionExpired`

**Category:** Organism
**File:** `src/components/organisms/SessionExpired/SessionExpired.tsx`
**Owner:** Auth

**Purpose:** The session-expired page. Single message, single button. No "stay signed in" toggle.

**Props:**

```ts
interface SessionExpiredProps {
  from?: string;
  className?: string;
}
```

**Composition:** `Text` (message), `Button` (sign in), `Rule`.

**States:** None.

**Tokens:** `--type-heading`, `--type-body`, `--color-ink`, `--color-accent`, `--color-rule`, `--space-5`, `--space-7`.

**Accessibility:**
- Renders `<main aria-labelledby="sessionexpired-heading">`.
- Heading is H1: "Session expired."

**Dependencies:** `Text`, `Button`, `Rule`.

---

### 3.15 `LegalPage`

**Category:** Organism
**File:** `src/components/organisms/LegalPage/LegalPage.tsx`
**Owner:** Legal

**Purpose:** Static legal content (terms, privacy). Fetches content from API.

**Props:**

```ts
type LegalDoc = "terms" | "privacy";

interface LegalPageProps {
  doc: LegalDoc;
  className?: string;
}
```

**Composition:** `Text` × N (content), `Rule`.

**States:**
- Default — content visible.
- Loading — `LoadingCounter`.
- Error — `ErrorBoundary`.

**Tokens:** `--type-subheading`, `--type-body`, `--color-ink`, `--color-rule`, `--space-3`, `--space-5`, `--space-7`, `--space-9`.

**Accessibility:**
- Renders `<main aria-labelledby="legal-heading">`.
- Heading is H1.
- Max-width 720px for comfortable reading.

**Dependencies:** `Text`, `Rule`, `LoadingCounter`, `ErrorBoundary`.

---

## 4. Page Templates

Page templates are not separate components; they are route render functions. Each route renders one template. The template composes the route's organism inside the `AppShell`.

### 4.1 `IntakePage`

**Route:** `/assess/person-a`, `/assess/person-b`
**File:** `src/components/templates/IntakePage.tsx`

**Composition:** `AppShell` + `IntakeForm` (with route-specific draft key and schema).

---

### 4.2 `DecisionPage`

**Route:** `/assess/$id`, `/history/$id`
**File:** `src/components/templates/DecisionPage.tsx`

**Composition:** `AppShell` + `DecisionSpine` (with assessment data from query).

---

### 4.3 `TypeSelectPage`

**Route:** `/assess/new`
**File:** `src/components/templates/TypeSelectPage.tsx`

**Composition:** `AppShell` + `TypeSelector`.

---

### 4.4 `ReportPage`

**Route:** `/assess/$id/report`
**File:** `src/components/templates/ReportPage.tsx`

**Composition:** `AppShell` + `ReportPage` (organism).

---

### 4.5 `HistoryPage`

**Route:** `/history`
**File:** `src/components/templates/HistoryPage.tsx`

**Composition:** `AppShell` + `HistoryList`.

---

### 4.6 `SettingsPage`

**Route:** `/settings`
**File:** `src/components/templates/SettingsPage.tsx`

**Composition:** `AppShell` + `SettingsPage` (organism).

---

### 4.7 `SignInPage`

**Route:** `/auth/sign-in`
**File:** `src/components/templates/SignInPage.tsx`

**Composition:** `AppShell` (no nav rail) + `SignIn`.

---

### 4.8 `ErrorPage`

**Route:** `/404`, `/500`
**File:** `src/components/templates/ErrorPage.tsx`

**Composition:** `AppShell` + `NotFound` or `ServerError`.

---

### 4.9 `LegalPage`

**Route:** `/legal/terms`, `/legal/privacy`
**File:** `src/components/templates/LegalPage.tsx`

**Composition:** `AppShell` + `LegalPage` (organism).

---

## 5. Component Dependency Graph

```
AppShell
├── TopBar
│   ├── Text
│   ├── SearchField
│   │   ├── Input
│   │   ├── Link
│   │   ├── Text
│   │   ├── LoadingCounter
│   │   └── EmptyState
│   ├── ConnectionIndicator
│   │   ├── Text
│   │   └── Tag
│   ├── Button
│   └── Link
├── NavRail
│   ├── Link
│   └── Text
├── MobileNav
│   └── Link
├── (route organism)
└── AuditFooter
    ├── Text
    ├── Rule
    ├── Kbd
    ├── Link
    └── Button

DecisionSpine
├── MetadataStrip
│   ├── Text
│   ├── Rule
│   └── Kbd
├── ApplicantIdentity
│   ├── Text
│   ├── MetadataStrip (above)
│   └── Rule
├── VerdictBlock
│   ├── Text
│   ├── ConfidenceFrame
│   │   ├── Text
│   │   └── Tag
│   ├── Tag
│   └── Button
├── DriverList
│   ├── DriverItem
│   │   └── Text
│   ├── Rule
│   └── LoadingCounter
├── RecommendationsList
│   ├── Text
│   ├── Rule
│   ├── Tag
│   └── LoadingCounter
├── DomainSection × N
│   ├── Text
│   ├── Rule
│   ├── Button
│   ├── LoadingCounter
│   └── BreakdownTable
│       ├── Text
│       ├── Tag
│       ├── Rule
│       ├── LoadingCounter
│       └── EmptyState
└── (AuditFooter from AppShell)

IntakeForm
├── FormField × N
│   ├── Label
│   ├── Input (or Select, Checkbox, Radio, Textarea)
│   └── Text
├── DomainSection
├── Button
├── Text
├── Rule
└── LoadingCounter

HistoryList
├── Text
├── FilterDisclosure
│   ├── Button
│   ├── Rule
│   └── FormField × N
├── HistoryItem × N
│   ├── Link
│   ├── Text
│   ├── Tag
│   └── LoadingCounter
├── Button
├── LoadingCounter
├── EmptyState
└── ErrorBoundary
```

---

## 6. Sign-off

This component specification is frozen for build. Any change is a design decision requiring Frontend Architect sign-off, recorded in `COMPONENT_SPEC_CHANGELOG.md`.

**Build signal:** Approved. The component library is closed. 15 atoms, 17 molecules, 15 organisms, 9 templates. No new components in v1.1.

**Coverage:** Every screen in v1.1 has a routed organism. Every organism composes only documented molecules. Every molecule composes only documented atoms. The dependency graph is acyclic (organisms do not reference other organisms).

**Forbidden list (not in this file):** See FRONTEND_ARCHITECTURE_V1.1.md §4 and §5.4. Any component matching a forbidden pattern is rejected at code review.
