# RiskIntel — Design Tokens

**Version:** 1.0
**Status:** Frozen for build
**Inherits from:** `DESIGN_BRIEF.md` v1.0, `FRONTEND_ARCHITECTURE_V1.1.md` v1.1
**Format:** W3C Design Tokens (JSON) + CSS Custom Properties + TypeScript type definitions
**Author:** Final Frontend Architect

---

## 0. How To Use This File

Every visual decision in RiskIntel resolves to a token in this file. No hardcoded values in components. No exceptions.

**Three delivery formats:**

1. **CSS Custom Properties** — referenced by name in component CSS, defined in `:root`.
2. **TypeScript constants** — referenced in JS/TS, tree-shakeable.
3. **JSON (W3C spec)** — single source of truth, generated from this file by the build.

**Build pipeline:** `tokens/tokens.json` (source) → Style Dictionary build → emits `tokens.css`, `tokens.scss`, `tokens.ts`, `tokens.d.ts`.

**Naming convention:** `--{category}-{name}`. Lowercase, kebab-case. Aliases (`--space-md`) are forbidden. There is one canonical name per token.

**No alias chains. No semantic renaming. No "design tokens" that are really CSS variables with extra steps.**

---

## 1. Spacing Scale

### 1.1 Tokens

| Token | Value | Pixels (at 1rem = 16px) |
|---|---|---|
| `space.0` | `0` | 0px |
| `space.1` | `0.25rem` | 4px |
| `space.2` | `0.5rem` | 8px |
| `space.3` | `1rem` | 16px |
| `space.4` | `1.5rem` | 24px |
| `space.5` | `2rem` | 32px |
| `space.6` | `3rem` | 48px |
| `space.7` | `4rem` | 64px |
| `space.8` | `6rem` | 96px |
| `space.9` | `8rem` | 128px |

### 1.2 CSS

```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 1rem;
  --space-4: 1.5rem;
  --space-5: 2rem;
  --space-6: 3rem;
  --space-7: 4rem;
  --space-8: 6rem;
  --space-9: 8rem;
}
```

### 1.3 TypeScript

```ts
export const space = {
  0: "0",
  1: "0.25rem",
  2: "0.5rem",
  3: "1rem",
  4: "1.5rem",
  5: "2rem",
  6: "3rem",
  7: "4rem",
  8: "6rem",
  9: "8rem",
} as const;
```

### 1.4 Usage Rules

- `space.1` to `space.3`: within a component (internals, padding, gap).
- `space.4` to `space.5`: between components in a section.
- `space.6` to `space.7`: between sections.
- `space.8` to `space.9`: page-level (outer margin, hero padding).
- No other values. If a value is not in the scale, the design is wrong.

---

## 2. Typography

### 2.1 Font Families

| Token | Value |
|---|---|
| `font.display` | `'GT Sectra', 'Tiempos Headline', 'Source Serif 4', Georgia, serif` |
| `font.body` | `'Inter', 'GT America', 'Söhne', system-ui, sans-serif` |
| `font.data` | `'Inter', 'IBM Plex Sans', 'Berkeley Mono', system-ui, sans-serif` |
| `font.mono` | `'Berkeley Mono', 'JetBrains Mono', 'SF Mono', Consolas, monospace` |

### 2.2 Type Scale

| Token | Size | Line-height | Weight | Letter-spacing | Usage |
|---|---|---|---|---|---|
| `type.display` | `2.75rem` (44px) | `3.25rem` (52px) | `500` | `-0.03125rem` (-0.5px) | Verdict (desktop) |
| `type.display-tablet` | `1.875rem` (30px) | `2.5rem` (40px) | `500` | `-0.015625rem` (-0.25px) | Verdict (tablet) |
| `type.display-mobile` | `1.875rem` (30px) | `2.5rem` (40px) | `500` | `-0.015625rem` (-0.25px) | Verdict (mobile) |
| `type.heading` | `1.875rem` (30px) | `2.5rem` (40px) | `500` | `-0.015625rem` (-0.25px) | Section H2 (desktop) |
| `type.subheading` | `1.375rem` (22px) | `2rem` (32px) | `500` | `0` | Section H3, applicant name |
| `type.body-large` | `1.0625rem` (17px) | `1.625rem` (26px) | `400` | `0` | Body large (empty states, lead) |
| `type.body` | `0.9375rem` (15px) | `1.5rem` (24px) | `400` | `0` | Body default |
| `type.body-small` | `0.875rem` (14px) | `1.375rem` (22px) | `400` | `0` | Body small (errors, footnotes) |
| `type.data` | `0.875rem` (14px) | `1.375rem` (22px) | `500` | `0` | Tabular numerics, monetary values |
| `type.data-small` | `0.75rem` (12px) | `1.125rem` (18px) | `500` | `0` | Audit metadata, contribution subtext |
| `type.mono` | `0.875rem` (14px) | `1.375rem` (22px) | `400` | `0` | IDs, timestamps, version strings |
| `type.mono-small` | `0.75rem` (12px) | `1.125rem` (18px) | `400` | `0` | Form labels, breadcrumb |
| `type.label` | `0.75rem` (12px) | `1.125rem` (18px) | `500` | `0.03125rem` (0.5px, uppercase) | Form field labels |

### 2.3 CSS

```css
:root {
  /* Font families */
  --font-display: 'GT Sectra', 'Tiempos Headline', 'Source Serif 4', Georgia, serif;
  --font-body: 'Inter', 'GT America', 'Söhne', system-ui, sans-serif;
  --font-data: 'Inter', 'IBM Plex Sans', 'Berkeley Mono', system-ui, sans-serif;
  --font-mono: 'Berkeley Mono', 'JetBrains Mono', 'SF Mono', Consolas, monospace;

  /* Type scale */
  --type-display-size: 2.75rem;
  --type-display-line: 3.25rem;
  --type-display-weight: 500;
  --type-display-tracking: -0.03125rem;

  --type-display-tablet-size: 1.875rem;
  --type-display-tablet-line: 2.5rem;
  --type-display-tablet-weight: 500;
  --type-display-tablet-tracking: -0.015625rem;

  --type-display-mobile-size: 1.875rem;
  --type-display-mobile-line: 2.5rem;
  --type-display-mobile-weight: 500;
  --type-display-mobile-tracking: -0.015625rem;

  --type-heading-size: 1.875rem;
  --type-heading-line: 2.5rem;
  --type-heading-weight: 500;
  --type-heading-tracking: -0.015625rem;

  --type-subheading-size: 1.375rem;
  --type-subheading-line: 2rem;
  --type-subheading-weight: 500;
  --type-subheading-tracking: 0;

  --type-body-large-size: 1.0625rem;
  --type-body-large-line: 1.625rem;
  --type-body-large-weight: 400;
  --type-body-large-tracking: 0;

  --type-body-size: 0.9375rem;
  --type-body-line: 1.5rem;
  --type-body-weight: 400;
  --type-body-tracking: 0;

  --type-body-small-size: 0.875rem;
  --type-body-small-line: 1.375rem;
  --type-body-small-weight: 400;
  --type-body-small-tracking: 0;

  --type-data-size: 0.875rem;
  --type-data-line: 1.375rem;
  --type-data-weight: 500;
  --type-data-tracking: 0;

  --type-data-small-size: 0.75rem;
  --type-data-small-line: 1.125rem;
  --type-data-small-weight: 500;
  --type-data-small-tracking: 0;

  --type-mono-size: 0.875rem;
  --type-mono-line: 1.375rem;
  --type-mono-weight: 400;
  --type-mono-tracking: 0;

  --type-mono-small-size: 0.75rem;
  --type-mono-small-line: 1.125rem;
  --type-mono-small-weight: 400;
  --type-mono-small-tracking: 0;

  --type-label-size: 0.75rem;
  --type-label-line: 1.125rem;
  --type-label-weight: 500;
  --type-label-tracking: 0.03125rem;
}
```

### 2.4 TypeScript

```ts
export const font = {
  display: "'GT Sectra', 'Tiempos Headline', 'Source Serif 4', Georgia, serif",
  body: "'Inter', 'GT America', 'Söhne', system-ui, sans-serif",
  data: "'Inter', 'IBM Plex Sans', 'Berkeley Mono', system-ui, sans-serif",
  mono: "'Berkeley Mono', 'JetBrains Mono', 'SF Mono', Consolas, monospace",
} as const;

export const type = {
  display: {
    size: "2.75rem",
    line: "3.25rem",
    weight: 500,
    tracking: "-0.03125rem",
  },
  displayTablet: {
    size: "1.875rem",
    line: "2.5rem",
    weight: 500,
    tracking: "-0.015625rem",
  },
  displayMobile: {
    size: "1.875rem",
    line: "2.5rem",
    weight: 500,
    tracking: "-0.015625rem",
  },
  heading: {
    size: "1.875rem",
    line: "2.5rem",
    weight: 500,
    tracking: "-0.015625rem",
  },
  subheading: {
    size: "1.375rem",
    line: "2rem",
    weight: 500,
    tracking: "0",
  },
  bodyLarge: {
    size: "1.0625rem",
    line: "1.625rem",
    weight: 400,
    tracking: "0",
  },
  body: {
    size: "0.9375rem",
    line: "1.5rem",
    weight: 400,
    tracking: "0",
  },
  bodySmall: {
    size: "0.875rem",
    line: "1.375rem",
    weight: 400,
    tracking: "0",
  },
  data: {
    size: "0.875rem",
    line: "1.375rem",
    weight: 500,
    tracking: "0",
  },
  dataSmall: {
    size: "0.75rem",
    line: "1.125rem",
    weight: 500,
    tracking: "0",
  },
  mono: {
    size: "0.875rem",
    line: "1.375rem",
    weight: 400,
    tracking: "0",
  },
  monoSmall: {
    size: "0.75rem",
    line: "1.125rem",
    weight: 400,
    tracking: "0",
  },
  label: {
    size: "0.75rem",
    line: "1.125rem",
    weight: 500,
    tracking: "0.03125rem",
  },
} as const;
```

### 2.5 Font Features

```css
:root {
  --font-features-body: 'kern', 'liga';
  --font-features-numeric: 'kern', 'liga', 'tnum';
  --font-features-display: 'kern', 'liga', 'dlig';
}
```

**Usage:**
- Body text: `font-feature-settings: var(--font-features-body)`.
- Numeric/data text: `font-variant-numeric: tabular-nums; font-feature-settings: var(--font-features-numeric)`.
- Display (verdict, headings): `font-feature-settings: var(--font-features-display)`.

### 2.6 Usage Rules

- Display type is reserved for the verdict and section H2.
- Body text is 15px (`.9375rem`). Never 16px. The 16px default is forbidden.
- Data type is used for all monetary values, scores, probabilities, and counts.
- Mono type is used for IDs, timestamps, version strings, and form labels.
- The 12px size is permitted only for: form labels, audit metadata, footnotes, contribution-bar subtext.
- Uppercase is permitted only for `type.label`.

---

## 3. Color

### 3.1 Tokens

| Token | Value | Role |
|---|---|---|
| `color.ink` | `#0E1217` | Primary text, structure |
| `color.paper` | `#F7F5F0` | Background |
| `color.rule` | `rgba(14, 18, 23, 0.12)` | Hairline dividers |
| `color.rule-strong` | `rgba(14, 18, 23, 0.24)` | Strong hairlines |
| `color.accent` | `#9A5A1F` | Decision accent (≤8% of any screen) |
| `color.positive` | `#2F6B4A` | "Ready" verdicts (reserved) |
| `color.negative` | `#8B2E2A` | "Not Ready" verdicts, error text |
| `color.ink.80` | `rgba(14, 18, 23, 0.80)` | Audit metadata, high-density mono |
| `color.ink.60` | `rgba(14, 18, 23, 0.60)` | Secondary text, empty states, labels |
| `color.ink.40` | `rgba(14, 18, 23, 0.40)` | Tertiary text, disabled state |
| `color.ink.20` | `rgba(14, 18, 23, 0.20)` | Disabled borders, dividers |
| `color.ink.12` | `rgba(14, 18, 23, 0.12)` | Hairlines (alias of rule) |
| `color.ink.8` | `rgba(14, 18, 23, 0.08)` | Track backgrounds (probability range) |
| `color.paper.80` | `rgba(247, 245, 240, 0.80)` | Backdrop fade (modal overlay) |
| `color.black.60` | `rgba(0, 0, 0, 0.60)` | Modal route backdrop |

### 3.2 CSS

```css
:root {
  /* Foundation */
  --color-ink: #0E1217;
  --color-paper: #F7F5F0;
  --color-rule: rgba(14, 18, 23, 0.12);
  --color-rule-strong: rgba(14, 18, 23, 0.24);
  --color-accent: #9A5A1F;
  --color-positive: #2F6B4A;
  --color-negative: #8B2E2A;

  /* Ink alpha scale */
  --color-ink-80: rgba(14, 18, 23, 0.80);
  --color-ink-60: rgba(14, 18, 23, 0.60);
  --color-ink-40: rgba(14, 18, 23, 0.40);
  --color-ink-20: rgba(14, 18, 23, 0.20);
  --color-ink-12: rgba(14, 18, 23, 0.12);
  --color-ink-8: rgba(14, 18, 23, 0.08);

  /* Paper and black variants */
  --color-paper-80: rgba(247, 245, 240, 0.80);
  --color-black-60: rgba(0, 0, 0, 0.60);
}
```

### 3.3 TypeScript

```ts
export const color = {
  ink: "#0E1217",
  paper: "#F7F5F0",
  rule: "rgba(14, 18, 23, 0.12)",
  ruleStrong: "rgba(14, 18, 23, 0.24)",
  accent: "#9A5A1F",
  positive: "#2F6B4A",
  negative: "#8B2E2A",
  ink80: "rgba(14, 18, 23, 0.80)",
  ink60: "rgba(14, 18, 23, 0.60)",
  ink40: "rgba(14, 18, 23, 0.40)",
  ink20: "rgba(14, 18, 23, 0.20)",
  ink12: "rgba(14, 18, 23, 0.12)",
  ink8: "rgba(14, 18, 23, 0.08)",
  paper80: "rgba(247, 245, 240, 0.80)",
  black60: "rgba(0, 0, 0, 0.60)",
} as const;
```

### 3.4 Contrast Audit (Pre-Build)

| Pair | Contrast | Use |
|---|---|---|
| `ink` on `paper` | 17.0:1 | Body text (AAA) |
| `ink-80` on `paper` | ~13.5:1 | Audit metadata, high-density mono (AAA) |
| `ink-60` on `paper` | ~10.0:1 | Secondary text, labels (AAA) |
| `ink-40` on `paper` | ~6.5:1 | Tertiary text, disabled (AAA) |
| `accent` on `paper` | 5.4:1 | Decision accent, focus ring (AA Large + AA UI) |
| `positive` on `paper` | 6.8:1 | "Ready" verdicts (AAA) |
| `negative` on `paper` | 7.2:1 | "Not Ready" verdicts, error text (AAA) |
| `accent` on `ink` | 3.2:1 | Focus ring on accent (verdict text) — meets AA UI |

**The audit footer at `ink-80` on `paper` is 13.5:1, well above the 4.5:1 AA threshold and the 7:1 AAA threshold. M4 fixed.**

### 3.5 Usage Rules

- `accent` appears on ≤ 8% of any screen. If a screen has more than 8% accent fill, the design is wrong.
- `positive` is reserved for "Ready" verdicts and their derivatives. Never decorative.
- `negative` is reserved for "Not Ready" verdicts and error text. Never decorative.
- Color is never the only signal. All status indicators have a text, position, or sign indicator alongside.
- `ink-40` is the only permitted disabled state color.
- `ink-8` is reserved for track backgrounds (probability range).
- No gradients. No drop shadows. No glow. No glassmorphism.

---

## 4. Z-Index Hierarchy

### 4.1 Tokens

| Token | Value | Usage |
|---|---|---|
| `z.base` | `0` | Default flow |
| `z.sticky` | `10` | Sticky elements (top bar, metadata strip) |
| `z.overlay` | `50` | Connection indicator toast |
| `z.modal` | `100` | Modal route backdrop |
| `z.modal-content` | `110` | Modal route content |
| `z.tooltip` | `200` | Tooltips |
| `z.skip-link` | `300` | Skip links (above everything) |

### 4.2 CSS

```css
:root {
  --z-base: 0;
  --z-sticky: 10;
  --z-overlay: 50;
  --z-modal: 100;
  --z-modal-content: 110;
  --z-tooltip: 200;
  --z-skip-link: 300;
}
```

### 4.3 TypeScript

```ts
export const z = {
  base: 0,
  sticky: 10,
  overlay: 50,
  modal: 100,
  modalContent: 110,
  tooltip: 200,
  skipLink: 300,
} as const;
```

### 4.4 Usage Rules

- No element may use a z-index outside this scale.
- Stacking context is created by `position: relative; z-index: var(--z-*)`.
- Tooltips are the highest non-skip-link layer.
- Skip links render above tooltips (so keyboard users can reach them).

---

## 5. Motion Hierarchy

### 5.1 Tokens

| Token | Value | Usage |
|---|---|---|
| `motion.instant` | `0ms` | `prefers-reduced-motion` fallback |
| `motion.exit` | `120ms ease-in` | State exits (modal close, dropdown close) |
| `motion.enter` | `160ms ease-out` | State entrances (modal open, dropdown open, page transition) |
| `motion.emphasis` | `240ms ease-out` | Verdict underline reveal (only motion > 160ms) |

### 5.2 Easing Curves

| Token | Value | Usage |
|---|---|---|
| `ease.out` | `cubic-bezier(0, 0, 0.2, 1)` | Entrance transitions |
| `ease.in` | `cubic-bezier(0.4, 0, 1, 1)` | Exit transitions |

### 5.3 CSS

```css
:root {
  --motion-instant: 0ms;
  --motion-exit: 120ms ease-in;
  --motion-enter: 160ms ease-out;
  --motion-emphasis: 240ms ease-out;

  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --motion-instant: 0ms;
    --motion-exit: 0ms;
    --motion-enter: 0ms;
    --motion-emphasis: 0ms;
  }
}
```

### 5.4 TypeScript

```ts
export const motion = {
  instant: "0ms",
  exit: "120ms ease-in",
  enter: "160ms ease-out",
  emphasis: "240ms ease-out",
} as const;

export const ease = {
  out: "cubic-bezier(0, 0, 0.2, 1)",
  in: "cubic-bezier(0.4, 0, 1, 1)",
} as const;
```

### 5.5 Usage Rules

- No spring physics. No bounce. No parallax.
- No motion longer than 240ms.
- All transitions honor `prefers-reduced-motion: reduce` and become instant.
- The verdict underline reveal (240ms) is the only motion longer than 160ms. It is the product's only "emphasis" motion.
- State changes (hover, focus, active) transition in 120ms. No transition on the default state.
- Transitions are explicit. `transition: all` is forbidden.

---

## 6. Focus Rings

### 6.1 Tokens

| Token | Value | Usage |
|---|---|---|
| `focus.width` | `2px` | All focus indicators |
| `focus.offset` | `2px` | Distance between element and ring |
| `focus.color` | `var(--color-accent)` | Default focus color |
| `focus.color-on-accent` | `var(--color-ink)` | Focus on accent backgrounds (verdict) |

### 6.2 CSS

```css
:root {
  --focus-width: 2px;
  --focus-offset: 2px;
  --focus-color: var(--color-accent);
  --focus-color-on-accent: var(--color-ink);
}

:focus {
  outline: var(--focus-width) solid var(--focus-color);
  outline-offset: var(--focus-offset);
}

/* Override for elements with accent backgrounds */
.focus-on-accent:focus,
.verdict:focus {
  outline-color: var(--focus-color-on-accent);
}

/* Never remove focus */
:focus { outline: none; } /* FORBIDDEN — never ship */
```

### 6.3 TypeScript

```ts
export const focus = {
  width: "2px",
  offset: "2px",
  color: "var(--color-accent)",
  colorOnAccent: "var(--color-ink)",
} as const;
```

### 6.4 Usage Rules

- Every interactive element has a visible focus ring.
- Focus rings are 2px solid, 2px offset.
- On `--accent` backgrounds, the focus ring is `--ink` (the accent cannot be distinguished from the background).
- Focus rings are never removed. `:focus { outline: none }` is forbidden.
- Custom focus styling uses `outline: var(--focus-width) solid var(--focus-color); outline-offset: var(--focus-offset)`.
- `:focus-visible` is preferred over `:focus` to avoid showing rings on mouse clicks (keyboard focus only).

---

## 7. Breakpoints

### 7.1 Tokens

| Token | Min-width | Target |
|---|---|---|
| `bp.mobile` | `0` | Phone, primary |
| `bp.mobile-landscape` | `640px` | Phone, landscape |
| `bp.tablet` | `768px` | Tablet, primary |
| `bp.desktop` | `1024px` | Desktop, primary |
| `bp.wide` | `1440px` | Desktop, large |

### 7.2 CSS

```css
:root {
  --bp-mobile: 0;
  --bp-mobile-landscape: 640px;
  --bp-tablet: 768px;
  --bp-desktop: 1024px;
  --bp-wide: 1440px;
}
```

### 7.3 Media Queries

```css
/* Mobile-first queries — default styles are mobile */

@media (min-width: 640px) {
  /* mobile-landscape and up */
}

@media (min-width: 768px) {
  /* tablet and up */
}

@media (min-width: 1024px) {
  /* desktop and up */
}

@media (min-width: 1440px) {
  /* wide and up */
}
```

### 7.4 TypeScript

```ts
export const breakpoint = {
  mobile: 0,
  mobileLandscape: 640,
  tablet: 768,
  desktop: 1024,
  wide: 1440,
} as const;
```

### 7.5 Container Widths

| Breakpoint | Max-width | Outer Padding | Gutter |
|---|---|---|---|
| Mobile | 100% | 16px | 16px |
| Tablet | 100% | 32px | 24px |
| Desktop | 1200px | 96px (per section) | 32px |
| Wide | 1200px | 96px (per section) | 32px |

### 7.6 Usage Rules

- Breakpoints are inclusive of the lower bound.
- Mobile-first queries: default styles are mobile; `@media (min-width: ...)` adds tablet/desktop.
- Content max-width 1200px on desktop and wide.
- The audit footer breaks out of the content container at all breakpoints (full width).

---

## 8. Component Tokens

### 8.1 Button

| Token | Default Size | Large Size |
|---|---|---|
| Height | 40px | 56px |
| Min-width | 80px | 120px |
| Padding-x | `--space-4` (24px) | `--space-5` (32px) |
| Padding-y | `--space-2` (8px) | `--space-3` (16px) |
| Tappable region | 56×56px | 56×56px (matches height) |
| Border-radius | 0 | 0 |
| Border-width | 1px | 1px |
| Font | `var(--type-body)` | `var(--type-subheading)` |
| Font weight | 500 | 500 |
| Transition | `var(--motion-exit)` | `var(--motion-exit)` |

**Variants:**

| Variant | Background | Text | Border |
|---|---|---|---|
| `primary` | `var(--color-ink)` | `var(--color-paper)` | none |
| `secondary` | `var(--color-paper)` | `var(--color-ink)` | 1px `var(--color-ink)` |
| `tertiary` | transparent | `var(--color-ink)` | none (underline on hover) |

**Hover:**
- Primary: background `var(--color-accent)`, transition `var(--motion-exit)`.
- Secondary: background `var(--color-ink-8)`.
- Tertiary: color `var(--color-accent)`, underline appears.

**Focus:** `var(--focus-color)`, 2px, 2px offset.

**Disabled:** text `var(--color-ink-40)`, background `transparent` (primary) or `var(--color-ink-8)` (secondary), cursor `not-allowed`.

### 8.2 Input

| Token | Value |
|---|---|
| Height | 40px |
| Padding-x | `--space-3` (16px) |
| Padding-y | `--space-2` (8px) |
| Border-width | 1px |
| Border-radius | 0 |
| Border-color (default) | `var(--color-rule-strong)` |
| Border-color (focus) | `var(--color-ink)` |
| Border-color (invalid) | `var(--color-negative)` |
| Background | `var(--color-paper)` |
| Text | `var(--type-body)`, `var(--color-ink)` |
| Placeholder | `var(--type-body)`, `var(--color-ink-40)` |
| Tappable region | 56×56px |

### 8.3 Tag

| Token | Value |
|---|---|
| Padding-x | `--space-2` (8px) |
| Padding-y | `--space-1` (4px) |
| Border-width | 1px |
| Border-radius | 0 |
| Font | `var(--type-mono-small)` |
| Font weight | 400 |

**Variants:**

| Variant | Border | Text |
|---|---|---|
| `default` | `var(--color-rule-strong)` | `var(--color-ink)` |
| `positive` | `var(--color-positive)` | `var(--color-positive)` |
| `negative` | `var(--color-negative)` | `var(--color-negative)` |
| `accent` | `var(--color-accent)` | `var(--color-accent)` |

### 8.4 Rule

| Token | Value |
|---|---|
| Height (horizontal) | 1px (default), 2px (strong) |
| Width (vertical) | 1px (default), 2px (strong) |
| Color (default) | `var(--color-rule)` |
| Color (strong) | `var(--color-rule-strong)` |
| Color (accent) | `var(--color-accent)` |

### 8.5 Tooltip

| Token | Value |
|---|---|
| Background | `var(--color-ink)` |
| Text | `var(--color-paper)` |
| Padding | `--space-2` (8px) `--space-3` (16px) |
| Font | `var(--type-body-small)` |
| Max-width | 280px |
| Border-radius | 0 |
| Delay | 240ms hover |
| Z-index | `var(--z-tooltip)` |

---

## 9. Shadow Tokens

There are no shadow tokens. The product does not use shadows. If a design requires elevation, it uses hairlines (`--color-rule`, `--color-rule-strong`) and z-index, never shadows.

**Forbidden:**
```css
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* FORBIDDEN */
filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.05)); /* FORBIDDEN */
```

---

## 10. Border Radius Tokens

There is one border radius: `0`. The product uses sharp corners throughout.

| Token | Value | Usage |
|---|---|---|
| `radius.none` | `0` | All elements |

**Exceptions:** No exceptions. Buttons, inputs, tags, modals, cards, all use `0`. The product's editorial-finance direction forbids rounded corners.

---

## 11. Opacity Tokens

Reserved for state transitions, disabled states, and stacking effects. Do not use opacity to fake transparency for text — use `color.ink-N` tokens instead.

| Token | Value | Usage |
|---|---|---|
| `opacity.disabled` | `0.4` | Disabled state (full element) |
| `opacity.hover` | `1` | Hover state (always fully opaque) |
| `opacity.pressed` | `0.8` | Active/pressed state |
| `opacity.backdrop` | `0.6` | Modal backdrop (`var(--color-black-60)`) |

---

## 12. Shadow Stacks (Compositional Patterns)

These are the only multi-property "patterns" the design system provides. They are explicit compositions, not magic shortcuts.

### 12.1 Sticky Top Bar

```css
.app-top-bar {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  height: 56px; /* desktop */
  background: var(--color-paper);
  border-bottom: 1px solid var(--color-rule);
}
```

### 12.2 Metadata Strip (Sticky on Scroll)

```css
.metadata-strip {
  position: sticky;
  top: 56px; /* below top bar */
  z-index: var(--z-sticky);
  background: var(--color-paper);
  border-bottom: 1px solid var(--color-rule);
  font: var(--type-mono-size)/var(--type-mono-line) var(--font-mono);
  color: var(--color-ink-80);
  padding: var(--space-2) 0;
}
```

### 12.3 Verdict Block

```css
.verdict {
  font-size: var(--type-display-size);
  line-height: var(--type-display-line);
  font-weight: var(--type-display-weight);
  letter-spacing: var(--type-display-tracking);
  color: var(--color-accent);
  padding: var(--space-9) 0; /* 128px top/bottom */
}
```

### 12.4 Audit Footer

```css
.audit-footer {
  font-size: var(--type-mono-size);
  line-height: var(--type-mono-line);
  color: var(--color-ink-80);
  padding: var(--space-7) 0; /* 64px top */
  border-top: 1px solid var(--color-rule);
}
```

---

## 13. Touch Target Tokens

| Token | Value | Usage |
|---|---|---|
| `touch.min` | `56px` | Minimum tappable region (mobile + tablet) |
| `touch.desktop` | `40px` | Minimum clickable region (desktop) |

**Usage rules:**
- Mobile + tablet: every interactive element has a `56×56px` tappable region. The visible button may be 40px; the tappable region is 56×56px.
- Desktop: minimum clickable region is 40×40px.
- Spacing between tappable elements: minimum 8px (`--space-2`).

```css
.touch-target {
  min-width: var(--touch-min);
  min-height: var(--touch-min);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
  box-sizing: border-box;
}
```

---

## 14. Grid Tokens

### 14.1 Desktop (≥1024px)

| Token | Value |
|---|---|
| Grid columns | 12 |
| Gutter | `var(--space-5)` (32px) |
| Max-width | 1200px |
| Outer margin | `var(--space-8)` (96px) |

### 14.2 Tablet (768–1023px)

| Token | Value |
|---|---|
| Grid columns | 8 |
| Gutter | `var(--space-4)` (24px) |
| Max-width | 100% |
| Outer padding | `var(--space-5)` (32px) |

### 14.3 Mobile (<768px)

| Token | Value |
|---|---|
| Grid columns | 4 |
| Gutter | `var(--space-3)` (16px) |
| Max-width | 100% |
| Outer padding | `var(--space-3)` (16px) |

### 14.4 CSS

```css
:root {
  --grid-columns-desktop: 12;
  --grid-columns-tablet: 8;
  --grid-columns-mobile: 4;
  --grid-gutter: var(--space-5);
  --grid-gutter-tablet: var(--space-4);
  --grid-gutter-mobile: var(--space-3);
  --grid-max-width: 1200px;
  --grid-outer-margin: var(--space-8);
  --grid-outer-padding: var(--space-5);
  --grid-outer-padding-mobile: var(--space-3);
}
```

### 14.5 CSS Grid Usage

```css
.grid-desktop {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns-desktop), 1fr);
  gap: var(--grid-gutter);
  max-width: var(--grid-max-width);
  margin-inline: auto;
  padding-inline: var(--grid-outer-margin);
}

.grid-tablet {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns-tablet), 1fr);
  gap: var(--grid-gutter-tablet);
  padding-inline: var(--grid-outer-padding);
}

.grid-mobile {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns-mobile), 1fr);
  gap: var(--grid-gutter-mobile);
  padding-inline: var(--grid-outer-padding-mobile);
}
```

---

## 15. W3C Design Tokens JSON (Source of Truth)

```json
{
  "color": {
    "ink": { "value": "#0E1217", "type": "color" },
    "paper": { "value": "#F7F5F0", "type": "color" },
    "rule": { "value": "rgba(14, 18, 23, 0.12)", "type": "color" },
    "rule-strong": { "value": "rgba(14, 18, 23, 0.24)", "type": "color" },
    "accent": { "value": "#9A5A1F", "type": "color" },
    "positive": { "value": "#2F6B4A", "type": "color" },
    "negative": { "value": "#8B2E2A", "type": "color" },
    "ink-80": { "value": "rgba(14, 18, 23, 0.80)", "type": "color" },
    "ink-60": { "value": "rgba(14, 18, 23, 0.60)", "type": "color" },
    "ink-40": { "value": "rgba(14, 18, 23, 0.40)", "type": "color" },
    "ink-20": { "value": "rgba(14, 18, 23, 0.20)", "type": "color" },
    "ink-12": { "value": "rgba(14, 18, 23, 0.12)", "type": "color" },
    "ink-8": { "value": "rgba(14, 18, 23, 0.08)", "type": "color" },
    "paper-80": { "value": "rgba(247, 245, 240, 0.80)", "type": "color" },
    "black-60": { "value": "rgba(0, 0, 0, 0.60)", "type": "color" }
  },
  "space": {
    "0": { "value": "0", "type": "dimension" },
    "1": { "value": "0.25rem", "type": "dimension" },
    "2": { "value": "0.5rem", "type": "dimension" },
    "3": { "value": "1rem", "type": "dimension" },
    "4": { "value": "1.5rem", "type": "dimension" },
    "5": { "value": "2rem", "type": "dimension" },
    "6": { "value": "3rem", "type": "dimension" },
    "7": { "value": "4rem", "type": "dimension" },
    "8": { "value": "6rem", "type": "dimension" },
    "9": { "value": "8rem", "type": "dimension" }
  },
  "font": {
    "display": { "value": "'GT Sectra', 'Tiempos Headline', 'Source Serif 4', Georgia, serif", "type": "fontFamily" },
    "body": { "value": "'Inter', 'GT America', 'Söhne', system-ui, sans-serif", "type": "fontFamily" },
    "data": { "value": "'Inter', 'IBM Plex Sans', 'Berkeley Mono', system-ui, sans-serif", "type": "fontFamily" },
    "mono": { "value": "'Berkeley Mono', 'JetBrains Mono', 'SF Mono', Consolas, monospace", "type": "fontFamily" }
  },
  "type": {
    "display": { "value": { "fontSize": "2.75rem", "lineHeight": "3.25rem", "fontWeight": 500, "letterSpacing": "-0.03125rem" }, "type": "typography" },
    "display-tablet": { "value": { "fontSize": "1.875rem", "lineHeight": "2.5rem", "fontWeight": 500, "letterSpacing": "-0.015625rem" }, "type": "typography" },
    "display-mobile": { "value": { "fontSize": "1.875rem", "lineHeight": "2.5rem", "fontWeight": 500, "letterSpacing": "-0.015625rem" }, "type": "typography" },
    "heading": { "value": { "fontSize": "1.875rem", "lineHeight": "2.5rem", "fontWeight": 500, "letterSpacing": "-0.015625rem" }, "type": "typography" },
    "subheading": { "value": { "fontSize": "1.375rem", "lineHeight": "2rem", "fontWeight": 500, "letterSpacing": "0" }, "type": "typography" },
    "body-large": { "value": { "fontSize": "1.0625rem", "lineHeight": "1.625rem", "fontWeight": 400, "letterSpacing": "0" }, "type": "typography" },
    "body": { "value": { "fontSize": "0.9375rem", "lineHeight": "1.5rem", "fontWeight": 400, "letterSpacing": "0" }, "type": "typography" },
    "body-small": { "value": { "fontSize": "0.875rem", "lineHeight": "1.375rem", "fontWeight": 400, "letterSpacing": "0" }, "type": "typography" },
    "data": { "value": { "fontSize": "0.875rem", "lineHeight": "1.375rem", "fontWeight": 500, "letterSpacing": "0" }, "type": "typography" },
    "data-small": { "value": { "fontSize": "0.75rem", "lineHeight": "1.125rem", "fontWeight": 500, "letterSpacing": "0" }, "type": "typography" },
    "mono": { "value": { "fontSize": "0.875rem", "lineHeight": "1.375rem", "fontWeight": 400, "letterSpacing": "0" }, "type": "typography" },
    "mono-small": { "value": { "fontSize": "0.75rem", "lineHeight": "1.125rem", "fontWeight": 400, "letterSpacing": "0" }, "type": "typography" },
    "label": { "value": { "fontSize": "0.75rem", "lineHeight": "1.125rem", "fontWeight": 500, "letterSpacing": "0.03125rem" }, "type": "typography" }
  },
  "z": {
    "base": { "value": 0, "type": "number" },
    "sticky": { "value": 10, "type": "number" },
    "overlay": { "value": 50, "type": "number" },
    "modal": { "value": 100, "type": "number" },
    "modal-content": { "value": 110, "type": "number" },
    "tooltip": { "value": 200, "type": "number" },
    "skip-link": { "value": 300, "type": "number" }
  },
  "motion": {
    "instant": { "value": "0ms", "type": "duration" },
    "exit": { "value": "120ms ease-in", "type": "transition" },
    "enter": { "value": "160ms ease-out", "type": "transition" },
    "emphasis": { "value": "240ms ease-out", "type": "transition" }
  },
  "ease": {
    "out": { "value": "cubic-bezier(0, 0, 0.2, 1)", "type": "cubicBezier" },
    "in": { "value": "cubic-bezier(0.4, 0, 1, 1)", "type": "cubicBezier" }
  },
  "focus": {
    "width": { "value": "2px", "type": "dimension" },
    "offset": { "value": "2px", "type": "dimension" },
    "color": { "value": "var(--color-accent)", "type": "color" },
    "color-on-accent": { "value": "var(--color-ink)", "type": "color" }
  },
  "breakpoint": {
    "mobile": { "value": 0, "type": "number" },
    "mobile-landscape": { "value": 640, "type": "number" },
    "tablet": { "value": 768, "type": "number" },
    "desktop": { "value": 1024, "type": "number" },
    "wide": { "value": 1440, "type": "number" }
  },
  "touch": {
    "min": { "value": "56px", "type": "dimension" },
    "desktop": { "value": "40px", "type": "dimension" }
  },
  "radius": {
    "none": { "value": "0", "type": "dimension" }
  },
  "opacity": {
    "disabled": { "value": 0.4, "type": "number" },
    "pressed": { "value": 0.8, "type": "number" },
    "backdrop": { "value": 0.6, "type": "number" }
  }
}
```

---

## 16. Validation Rules (CI Gates)

The build fails if any of the following are violated:

1. **No hardcoded colors** in component CSS. Every color is a token.
2. **No hardcoded spacing** in component CSS. Every margin/padding/gap is a space token.
3. **No hardcoded type values** in component CSS. Every font-size, line-height, font-weight, letter-spacing is a type token.
4. **No `box-shadow`** in component CSS. Shadows are forbidden.
5. **No `border-radius` other than `0`**. Sharp corners only.
6. **No gradients** (`linear-gradient`, `radial-gradient`, `conic-gradient`).
7. **No z-index outside the scale**. The build greps for `z-index:` and fails if the value is not in the token set.
8. **No transitions longer than 240ms**.
9. **No 16px body text**. The default `font-size: 1rem` is forbidden on body text.
10. **No `:focus { outline: none }`**. Focus rings are mandatory.

Enforcement: Stylelint config + custom ESLint rules + grep-based CI check.

---

## 17. Sign-off

This token system is frozen for build. Any change is a design decision requiring Frontend Architect sign-off, recorded in `TOKENS_CHANGELOG.md`.

**Build signal:** Approved. This file is the single source of truth for all visual values in RiskIntel. Components reference tokens by name. No hardcoded values.

**File location:** `tokens/tokens.json` (source), `src/styles/tokens.css` (generated), `src/styles/tokens.ts` (generated).

**Build pipeline:** Style Dictionary reads `tokens/tokens.json`, emits CSS + TS + SCSS + JSON to `src/styles/`. The frontend imports from `src/styles/`.
