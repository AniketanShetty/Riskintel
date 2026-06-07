# RiskIntel — Product Design Brief

**Version:** 1.0
**Status:** Frozen for handoff
**Audience:** Product, Design, Engineering, Compliance
**Author:** Principal Product Designer, Senior UX Researcher, Fintech Design Lead

---

## 0. Mission Statement

RiskIntel is a decision-support surface for the people who decide who gets capital. The product's job is to make every underwriting decision **legible, defensible, and humane** — to the loan officer, to the institution, and to the borrower whose life the decision will touch.

We are not building a dashboard. We are building the place where consequential decisions are made, recorded, and explained.

---

## 1. Emotional Experience

### The feeling we are designing for

**Calm authority.** Not excitement. Not gamified delight. Not reassurance theatre. The user — a loan officer or credit analyst — should feel, on every screen, that the product is in command of the material, that nothing has been hidden, and that the next click will not betray them.

The secondary feeling, held simultaneously: **dignity.** Every borrower whose data appears in this product is a person. The interface must never aestheticize their data, gamify their risk profile, or reduce them to a number they would not want to see. The loan officer is the audience; the borrower is the subject. Both must be respected.

### The feelings we are explicitly designing against

| Anti-feeling | What it would look like | Why we reject it |
|---|---|---|
| "Fintech-bro" exuberance | Confetti on approval, streaks, badges | The decision is not a game. The borrower's livelihood is not a reward loop. |
| Casino / trading-floor energy | Tickers, neon greens and reds, pulsing charts | Risk is real here. Aesthetics of volatility erode the gravitas of the decision. |
| Patronizing simplicity | Cartoon illustrations, "fun" metaphors | MFI staff and analysts are professionals. Patronage insults them and obscures the model. |
| Cold bureaucratic opacity | Gray tables, hidden methodology | The system must show its work. Opacity is the original sin in credit. |
| Vendor anxiety | Promotional CTAs, upsells, "did you know" tips | This is a tool, not a product surface. The product ends at the decision. |

### The borrower's mirror

Loan officers know — consciously or not — that the interface is a proxy for how the institution treats the people on the other side of the loan. A product that talks down to the loan officer will be the same product that talks down to the borrower. A product that respects the officer's intelligence and time will be the same product that, downstream, protects the borrower's dignity.

**We design for the loan officer the way we would want a product to be designed for the borrower's loan officer.**

---

## 2. Visual Direction

### North-star references

- **The Economist** — editorial gravitas, serif headlines, considered color, data-as-story
- **Stripe Press** — restraint as luxury, generosity of whitespace, type-driven hierarchy
- **Linear / Vercel docs** — density without clutter, monospace where it earns its place
- **RBI / Federal Reserve research bulletins** — institutional seriousness, footnotes, primary-source feel

### Color

A **two-tone foundation, single accent** system. No multi-color palette. No semantic traffic-light defaults.

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#0E1217` | Primary text, lines, structure. Used for everything by default. |
| `--paper` | `#F7F5F0` | Background. Off-white, warm, low-glare. Not pure white. |
| `--rule` | `#1F2937` at 12% alpha | Dividers, table grids, baseline hairlines. |
| `--accent` | `#9A5A1F` (burnt sienna) | **Decision accent.** Used for verdict, primary CTA, key metric. Limited to ≤ 8% of any screen. |
| `--positive` | `#2F6B4A` (deep forest) | Reserved for "Ready" verdicts. Used sparingly, never as fill. |
| `--negative` | `#8B2E2A` (oxblood) | Reserved for "Not Ready" verdicts. Never used decoratively. |

**Rules**
- No gradients. No drop shadows. No glow. No glassmorphism.
- No color used to indicate status on data rows — only on the verdict itself.
- Accent color is rationed. If everything is accent, nothing is.
- Charts: monochrome (`--ink` at varying alpha) with `--accent` reserved for the "answer."

### Typography

| Role | Family | Weight | Notes |
|---|---|---|---|
| Display (verdict, headers) | Serif — GT Sectra, Tiempos Headline, or Source Serif 4 | 500 | Tight tracking. Always sentence case. |
| Body | Humanist sans — Inter, GT America, or Söhne | 400 / 500 | Generous leading (1.55). |
| Data / numerics | Tabular sans — Inter, IBM Plex Sans, or Berkeley Mono | 500 with `font-variant-numeric: tabular-nums` | All numerics align to a 4dp grid. |
| Audit / metadata | Monospace — Berkeley Mono or JetBrains Mono | 400 | Smaller, secondary, never used for headings. |

Type sizes: 14/15/17/22/30/44 pt scale. No 16. No 12.

### Layout & density

- **Baseline grid: 8px.** All vertical rhythm snaps to it. No exceptions.
- **Margins: generous.** Page-level content uses 96px outer; card content uses 32px inner. Density is achieved through line-height and column count, not by shrinking margins.
- **One column for decisions, two for evidence.** The verdict column is always single. Supporting evidence can be two-column on desktop, single on tablet, never below 360px.
- **No card soup.** Hierarchy is created by type scale, whitespace, and hairlines — not by colored rectangles stacked on a gray background.
- **Asymmetric.** A full-width hero verdict anchors every assessment page. The evidence is offset, indented, given room. The eye should travel, not scan.

### Iconography

- **Line icons, 1.5px stroke, 20px default.** No filled icons. No emoji. No illustrations of people.
- **Icons are verbs, not nouns.** "Compare" not "comparison." "Audit" not "magnifying glass."
- **No status icons in the decision path.** The verdict is text, not an icon.

### Imagery

- **No stock photography of any kind.** No farmers. No villages. No hands holding money. No diverse-boardroom shots.
- **No illustrations.** The product deals in data; illustrations would aestheticize risk.
- **Where a visual is genuinely needed** (a placeholder for an applicant photo, for instance), use a typographic monogram against `--paper`. That is the only visual identity the borrower's portrait gets, and it is dignified.

### Motion

- **Animation is feedback, not decoration.** A state change animates. A landing does not.
- **Transitions: 160ms ease-out for entrances, 120ms ease-in for exits.** Faster feels nervous; slower feels sluggish.
- **No spring physics. No bounce. No parallax.**
- **Skeleton screens are forbidden.** Use a real loading state with a static typographic indicator ("Loading 4 of 7 signals…") — uncertainty is honest.
- **Hover states: underline + color shift only.** No background fills. No scale transforms.

---

## 3. Information Hierarchy

### The decision spine

Every assessment page in RiskIntel follows the same five-layer hierarchy. The layers are **always** in this order, top to bottom, on every device:

1. **Verdict** — the answer. One phrase. The largest type on the page. Above the fold. Unmistakable.
2. **Confidence frame** — the band score, probability range, and override flags, set in a single hairline-bounded block. Tells the officer *how much* to trust the answer.
3. **Top drivers** — three to five factors that most influenced the verdict, positive and negative, ranked. The officer can act on this without scrolling.
4. **Full breakdown** — every input and its contribution, in a table the officer can read, filter, and expand. Reachable by scrolling, not by clicking through.
5. **Audit trail** — model lineage, decision version, schema version, timestamp, correlation id. Always visible at the page footer, not hidden behind a tab.

### Why this order

Loan officers process decisions quickly, but they are held accountable for them. The product must let them act fast **and** defend the action later. The hierarchy serves the act first (verdict, confidence), the explanation second (drivers, breakdown), and the defense last (audit). Inverting this order — putting the breakdown before the verdict — is a pattern we explicitly reject. It optimizes for the auditor, not the officer, and trains the officer to ignore the answer.

### The applicant identity

The applicant's name, age, business, and loan request appear in a single identity block at the top of the page, above the verdict. The identity is **always** the same on every screen and every report. No rotating avatars. No animated reveals. A person, named, on a clean background.

### What sits where

| Element | Position | Justification |
|---|---|---|
| Applicant identity | Top, full width, anchored | Recurring reference; the officer scans for the name first. |
| Verdict | Hero, full width, below identity | The answer. The product's reason for existing. |
| Confidence frame | Below verdict, single row | Tells the officer the strength of the answer, not just the answer. |
| Top drivers | 3-column grid (desktop), stacked (mobile) | The reason for the answer. The officer's talking points. |
| Full breakdown | Below drivers, expandable sections by domain | The audit-grade evidence. Reachable, not buried. |
| Recommendations | Adjacent to top drivers, secondary column | What to do next, in the officer's hand at the moment of decision. |
| Archetype | Below recommendations, single line | Supplementary context. Never a hero element. |
| Audit footer | Page footer, always visible | Defensibility. One scroll away, never a click. |

### Negative hierarchy

The product is anti-feed. There is no infinite scroll. There is no "see more" loop. The decision is a closed object. The officer reaches the end of the page and the next step is **act or escalate** — never "browse more."

---

## 4. Design Principles

Six principles govern every design decision in RiskIntel. They are not aspirations; they are constraints. Every shipped feature must satisfy all six. Conflicts between principles are resolved in the order listed.

### 1. Verdict-forward

**The answer is never more than one scroll away, on any device, on any screen, under any condition.**

If a screen does not show the verdict or make the verdict accessible, the screen is wrong. There is no exception for "loading," "empty state," or "first-time user." Even before the verdict exists, the product shows the verdict slot, empty, with a typographic "—" — never a spinner, never a placeholder image, never a generic "no data" state.

### 2. Evidence-anchored

**Every number on the screen is traceable to a source, a model version, a schema version, and a timestamp.**

The product is not a calculator. It is a recorder. If a number is shown, the officer must be able to click it (or, in audit mode, see it) and reach the input that produced it, the model that processed it, and the version of both. Hidden numbers, magic numbers, and "AI-generated" figures with no provenance are forbidden. The system is allowed to be wrong; it is not allowed to be unauditable.

### 3. Dignity-preserving

**The interface treats the borrower as a person, the officer as a professional, and the decision as a serious act.**

This principle governs everything that does not fall under the other five. It is the principle that prevents "cute." It prevents gamification, illustration, stock photography, exclamation points, exclamation-everything. It prevents the "fun fact" tooltip. It prevents the "did you know" tip card. The product's voice is the voice of a senior analyst, not a marketing site.

### 4. Audit-ready

**Every screen in RiskIntel is one screenshot away from being defensible to a regulator, a board, or a borrower.**

The audit trail is not a separate mode. It is not a hidden export. It is not a developer panel. It is the page footer. Always present, always visible, always copyable. The officer never has to "switch to audit view" to defend a decision. If a regulator asks for the audit record of a decision, the officer pastes a URL or a PDF. End of story.

### 5. Calm density

**The product is information-rich but never overwhelming. Density is achieved through restraint, not reduction.**

A RiskIntel page is dense with information. The decision spine shows the verdict, the confidence, the top five drivers, the recommendations, the archetype, the full breakdown, the audit metadata. All of this fits on one page. It fits because the type scale, the baseline grid, the column structure, and the color rationing all do their job. A page that "feels empty" is a failure. A page that "feels overwhelming" is also a failure. The target is the third state: a page that feels **considerable.**

### 6. Offline-resilient

**The product functions in low-bandwidth environments and degrades honestly when it cannot.**

Loan officers in rural branches do not have 5G. The product must load its critical path (verdict, top drivers, audit footer) on first paint, with the full breakdown lazy-loaded. It must never silently fail. If a section cannot load, it says so, in plain text, in the same type as the rest of the product — never a red error banner, never a popup, never a console trace.

---

## 5. What Must Never Appear in the UI

A non-exhaustive list. Each item is forbidden for a specific, named reason. New team members should add to this list when they encounter a pattern that violates one of the principles.

### Forbidden visual patterns

- **Stock photographs of farmers, villages, hands holding currency, or "diverse" boardrooms.** Aesthetics of representation that reduce borrowers to a stock image. Reject.
- **Illustrations of people, especially stylized or cartoon figures.** A borrower's portrait is a typographic monogram, not a vector illustration.
- **Confetti, badges, streaks, "achievement unlocked" overlays, animated emoji, or any reward-pattern UI.** A loan decision is not a game.
- **Traffic-light color systems on data rows.** Color carries no semantic meaning except on the verdict. A red/green table trains the officer to react to color, not data.
- **Drop shadows, glow effects, glassmorphism, gradient fills, neon colors, "futuristic" blue.** These are aesthetics of volatility and innovation theatre. The product is not a startup pitch.
- **Pie charts, donut charts, 3D charts, radar charts.** The product's data is tabular and decomposable. Charts that hide precision are rejected. (See §6.5.)
- **Carousels, accordions-as-hero, animated hero sections, parallax scroll.** The decision is not a story to be told. It is a record to be read.
- **Modal dialogs for primary actions.** Approve, decline, escalate. None of these are modal. They are page transitions.
- **"Did you know" tip cards, "feature highlights," tour overlays, "what's new" banners.** The product does not market itself to its own users.

### Forbidden copy patterns

- **"We are excited to announce" / "Get started" / "Welcome to RiskIntel" / "Let's begin your journey."** The first-person plural, the imperative, the "journey" metaphor. All forbidden. The product speaks in the third person, in plain English, in the voice of a senior analyst.
- **"AI-powered" / "intelligent" / "smart" / "next-generation" / "revolutionary" as feature descriptions.** These are vendor adjectives. They describe nothing. The product either does the thing or it does not.
- **Probability framed as a "score" without its range.** "Score: 73" with no confidence interval is a marketing copy error. The number is a probability, with a range, in a band, in plain English.
- **Euphemisms for decline.** "We'll pass on this one" / "Maybe later" / "Not the right fit." The product says "Not Ready" or "Rejected" or "Insufficient data," as appropriate. Hedge words are forbidden.
- **Predatory urgency.** "Decision expires in 24 hours" / "Only 3 slots left" / "Limited-time override available." None of this. The decision is not a checkout.
- **Empty reassurance.** "Your data is safe with us" / "Trusted by leading institutions" / "Built by experts." The product either has a security page or it does not. The product either has clients or it does not. The product either has a team or it does not. The product does not assert these things in the workflow.

### Forbidden interaction patterns

- **Dark-pattern approvals.** No "are you sure you want to decline" if the user is confident. No "click here to confirm" if the click is the action. The action is the action.
- **Hidden costs of actions.** No feature whose consequence is not shown before the action. If overriding the model carries a flag, the flag is shown.
- **Auto-play, auto-advance, auto-refresh of decision content.** The officer is in charge of the page. The product does not move beneath their hand.
- **Push notifications for "new features" or "improvements."** The product does not market to its own users.
- **Forced feedback collection inside the decision flow.** If the institution needs CSAT, it asks elsewhere, asynchronously, after the decision is closed.

### Forbidden data patterns

- **"Black box" AI claims.** No "our model knows" language. The model does not know. The model produced a probability, with a range, against a known set of features, with a versioned lineage. That is what the product says.
- **Predictions about protected attributes.** Race, religion, caste, gender, sexuality, disability, age band beyond the actual figure. The product does not model on these. The product does not show them as features.
- **Survivorship-biased "top 10% of borrowers" or "best in class" comparisons.** If the product compares, it compares to a disclosed, versioned, named cohort.
- **Causal language for correlational outputs.** "Your income caused your approval" is forbidden. "Higher income was associated with higher probability, holding other factors constant" is the correct register.

---

## 6. Five Design Directions Considered

Each direction was sketched as a complete system — color, type, layout, motion, voice — and stress-tested against the six design principles. None of these are mockups. They are described at the level a designer would defend in a crit.

### 6.1 Direction A — "Editorial Finance"

**Description:** A reading-first, type-driven product that feels like a long-form financial publication. Serif headlines, off-white paper, hairline rules, monochrome data, single accent. Layouts are asymmetric. Tables are primary; charts are absent. The decision appears as a headline. The audit trail appears as a colophon.

**Visual identity:** GT Sectra display, Inter body, Berkeley Mono for data. Off-white (`#F7F5F0`), ink (`#0E1217`), burnt sienna accent. No shadows. No color on data rows.

**Voice:** Senior analyst. "Ramesh Kumar is Moderately Ready. Probability of readiness, 0.68, with a 90% range of 0.61–0.74."

**Strengths**
- Maximally dignified. Treats the officer and the borrower as adults.
- Density without clutter. Information-rich without being noisy.
- Audit-ready by default — the visual language is already the language of disclosure.
- Differentiated. Nothing in Indian fintech or MFI tooling looks like this. The product will be remembered.

**Weaknesses**
- Higher learning curve for users accustomed to dashboard conventions. Tabular density requires literacy.
- Requires an exceptionally disciplined type system. Small errors in scale or weight will be visible.
- The aesthetic is "quiet," which can read as "underconfident" to a procurement team that wants enterprise signals.

**Verdict on principles:** ✓ 1, ✓ 2, ✓ 3, ✓ 4, ✓ 5, ✓ 6.

### 6.2 Direction B — "Clinical Dashboard"

**Description:** A Bloomberg Terminal for credit. Dense, monospace, dark, utilitarian. Information stacked in panels. Numerics primary. The verdict is a colored block. The audit trail is a status bar.

**Visual identity:** Monospace throughout (`Berkeley Mono`, `JetBrains Mono`). Dark surface (`#0A0A0A`), phosphor green for positive, oxblood for negative, single accent for emphasis.

**Voice:** Neutral, machine-like. "VERDICT: MODERATELY READY. P=0.68. CI90=[0.61, 0.74]."

**Strengths**
- Maximally information-dense. A power user can extract the same signal in half the screen.
- Familiar to analysts who use Bloomberg, Refinitiv, or any trading platform.
- The aesthetic is unambiguous about seriousness. No one confuses this with a "fun" product.

**Weaknesses**
- Dark surfaces increase glare in low-light MFI branch offices and contradict §4.6 (offline / low-bandwidth contexts may include dim environments).
- Monospace everywhere destroys the verdict-forward principle. Headlines in mono feel bureaucratic, not declarative.
- The voice reads as cold. The product is allowed to be serious without being clinical.
- The aesthetic is also already taken by every other "serious" fintech. No differentiation.

**Verdict on principles:** ✓ 1, ✓ 2, ~ 3, ✓ 4, ✓ 5, ~ 6.

### 6.3 Direction C — "Banking Heritage"

**Description:** A traditional private-bank aesthetic. Navy, gold, classical serif, ornamental details. The product feels like a Coutts statement, a JP Morgan private banking interface, a Rothschild report.

**Visual identity:** Display serif (Tiempos, Caslon), body serif (Source Serif). Navy (`#0B1E3F`), gold (`#A8842B`), cream backgrounds. Subtle ornaments, rule lines with diamond endpoints, monogram-style logo treatment.

**Voice:** Formal, institutional. "The applicant is assessed as Moderately Ready, with a 68% probability."

**Strengths**
- Conveys institutional trust unambiguously. Procurement-friendly.
- The aesthetic is rare in MFI tooling, which is its opportunity.
- Dignified for the borrower. The product's aesthetic borrows from the borrower's own aspirations, not their stereotypes.

**Weaknesses**
- The aesthetic is performative. Gold and ornament signal luxury, not accuracy. The product's truthfulness is harder to project through this language.
- Density suffers. Heritage aesthetics reward restraint of content, which conflicts with §4.5 (calm density).
- The accent (gold) reads as decorative, not as a decision signal. The "verdict-forward" principle is harder to honor when the accent is decorative.
- Voice risks pomposity. "The applicant is assessed" vs. "Ramesh Kumar is Moderately Ready" — the second is clearer, the first more formal. Heritage direction defaults to the first.

**Verdict on principles:** ✓ 1, ✓ 2, ✓ 3, ✓ 4, ~ 5, ✓ 6.

### 6.4 Direction D — "Modern Fintech"

**Description:** Plaid, Mercury, Brex, Ramp. White background, friendly sans, soft pastels, rounded corners, generous whitespace, friendly microcopy.

**Visual identity:** Inter or Geist throughout. White (`#FFFFFF`), soft pastels for status, rounded 12px corners, soft shadows, friendly accent colors. Emoji-free but soft.

**Voice:** Warm, first-person plural. "We think Ramesh is Moderately Ready. Here's why →"

**Strengths**
- Familiar. Loan officers under 40 already use Plaid/Mercury/Ramp; the aesthetic is known and trusted.
- Approachable. Reduces perceived friction.
- Onboarding-friendly for new users.

**Weaknesses**
- Aesthetic is saturated. Every fintech in 2026 looks like this. No differentiation.
- The aesthetic signals "consumer product," not "institutional product." MFIs and credit committees will perceive it as less serious.
- The warmth is performed. The product's voice should be the officer's voice, not the vendor's. "We think" is not the officer speaking.
- Conflicts with §4.3 (dignity-preserving) for the borrower. Soft pastels and friendly illustrations are not how the borrower's data should be presented.
- "Fun" tone undermines the decision. The verdict is allowed to be warm; the verdict is not allowed to be cute.

**Verdict on principles:** ~ 1, ✓ 2, ✗ 3, ✓ 4, ~ 5, ✓ 6.

### 6.5 Direction E — "Public Sector Research"

**Description:** RBI research bulletins, Federal Reserve working papers, NBER academic style. Two-column body, footnotes, endnotes, citations, formal tables, sober color.

**Visual identity:** Charter, Source Serif, or IBM Plex Serif. Off-white paper, black ink, single muted accent. Heavy use of footnotes and inline citations. Wide margins, scholarly feel.

**Voice:** Academic, hedged. "The model estimates a readiness probability of 0.68 (95% CI: 0.61–0.74), conditional on the input features provided (n=18)."

**Strengths**
- Maximally audit-ready. The aesthetic is the aesthetic of disclosure.
- Maximally dignified. This is how research treats its subjects.
- Zero risk of being perceived as "trendy" or "startuppy."

**Weaknesses**
- The aesthetic is not the officer's aesthetic. Officers are not academics. The visual language will feel foreign to a working user.
- Footnotes and citations, done seriously, take vertical space. The verdict-forward principle (the answer is always one scroll away) becomes harder to honor.
- Voice is too hedged. "Conditional on the input features provided" is true but is not the officer's voice. The officer wants to act.
- Aesthetic is not differentiated in the *institutional finance* space; it is differentiated from it, which is the wrong direction.

**Verdict on principles:** ~ 1, ✓ 2, ✓ 3, ✓ 4, ✓ 5, ~ 6.

### 6.6 Comparison matrix

| Principle | A: Editorial Finance | B: Clinical Dashboard | C: Banking Heritage | D: Modern Fintech | E: Public Sector Research |
|---|---|---|---|---|---|
| 1. Verdict-forward | ✓ | ✓ | ✓ | ~ | ~ |
| 2. Evidence-anchored | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3. Dignity-preserving | ✓ | ~ | ✓ | ✗ | ✓ |
| 4. Audit-ready | ✓ | ✓ | ✓ | ✓ | ✓ |
| 5. Calm density | ✓ | ✓ | ~ | ~ | ✓ |
| 6. Offline-resilient | ✓ | ~ | ✓ | ✓ | ~ |
| Differentiation | Strong | Weak | Moderate | Weak | Strong |
| Learnability | Moderate | Moderate | Easy | Easy | Hard |
| Procurement-friendly | Moderate | Strong | Strong | Strong | Moderate |

---

## 7. Final Direction — Editorial Finance

**RiskIntel will be designed and built in the Editorial Finance direction (Direction A).**

### Justification

**Direction A is the only direction that satisfies all six design principles without compromise.** Directions B, C, D, and E each fail or compromise at least one principle, and in every case, the compromised principle is one we are unwilling to compromise (dignity-preserving in D, audit-readiness under offline in B, calm density in C, verdict-forwardness in E).

Direction A also satisfies a requirement none of the others meet: **the aesthetic is true to the product's nature.** RiskIntel is a place where consequential decisions are read, recorded, and explained. The aesthetic that best matches that activity is the aesthetic of reading, recording, and explaining — which is the aesthetic of editorial finance. Other directions aestheticize other activities: trading, banking, transacting, researching. Direction A aestheticizes the activity the product actually performs.

**Direction A also gives RiskIntel an unfair advantage.** The MFI / rural-lending tooling space is visually undifferentiated. Every competitor in the segment uses either "modern fintech" patterns (Plaid-style) or "enterprise SaaS" patterns (Salesforce-style). Neither pattern is dignified. Neither pattern treats the borrower as anything other than a row in a table. By choosing Direction A, RiskIntel becomes the only product in the segment that looks like it takes the decision — and the borrower — seriously. This is a brand moat, not just a visual choice.

### Trade-offs we accept

In choosing Direction A, we accept three trade-offs explicitly. Each is documented here so that future contributors do not "fix" them in error.

1. **Higher learning curve.** The aesthetic is unfamiliar to officers used to dashboard conventions. We mitigate this through progressive disclosure (the verdict is always one scroll away, but advanced views are reachable) and a 90-second onboarding overlay that explains the decision spine once, the first time the user encounters it. We do not mitigate by softening the aesthetic.

2. **The aesthetic is quiet.** Procurement teams evaluating RiskIntel may initially perceive the product as "underconfident" compared to louder enterprise tools. We mitigate by publishing this brief, by carrying the design discipline into the sales motion, and by trusting the institution's eventual product people to recognize the difference. We do not mitigate by adding ornament.

3. **Type system discipline is non-negotiable.** The aesthetic fails visibly if the type scale drifts, the baseline grid slips, or the color rationing is broken. We accept that the design team must police this with more rigor than other products require, and we build the design system accordingly.

### What this brief does not cover

- Component library specifications (typography, color, spacing tokens) — to be specified in `design-tokens.md`
- Screen-by-screen wireframes — to be produced in Figma, with the brief as the constraint
- Motion specifications (easing curves, durations, interaction patterns) — to be specified in `motion.md`
- Accessibility audit and WCAG conformance plan — to be specified in `a11y.md`
- Localization and right-to-left support — to be specified in `i18n.md`
- Empty / loading / error / first-use state design — to be specified in `states.md`

These documents are downstream of this brief and inherit its principles.

---

## 8. Sign-off

This brief is frozen for handoff to the product, design, and engineering teams. Any change to the brief is a design decision and must be made by the Principal Product Designer, with review by the Senior UX Researcher and Fintech Design Lead. Brief changes are recorded in `BRIEF_CHANGELOG.md`.

The brief is reviewed quarterly. A review is triggered by:
- A new user segment entering the product
- A material change in regulatory environment
- A pattern in support tickets that the brief did not anticipate
- A drift in shipped design that the brief was meant to prevent
