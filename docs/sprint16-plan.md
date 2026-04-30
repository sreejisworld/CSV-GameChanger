# Sprint 16 Plan — Defensibility & First-Time-User Wow

**Sprint window:** 2026-04-29 → 2026-05-01 (target ~1.5 working days)
**Theme:** Make the platform *legible*, *demo-able*, and *defensible* — directly addressing 5 customer-demo pain points captured 2026-04-28.

---

## Why this sprint exists (the customer signal)

Five distinct demo signals collapsed into one coherent sprint:

| # | Customer feedback | Sub-feature |
|---|------------------|-------------|
| 1 | "Black background — can't read the text" | **16.1 Light theme** |
| 2 | "Pros are scared of AI tools, want minimum training" | Implicit in 16.1 + 16.4 (familiar light UI + visible audit trail) |
| 3 | "First 30s wow + last 30s wow" | **16.2 Sample/Demo Mode** + **16.3 Validation Defense Package** |
| 4 | "Each module needs an easy look — let me feed real use cases end-to-end" | **16.2** anchored on a real LIMS scenario |
| 5 | *"I can do requirements with $40 ChatGPT subscription"* (founder critique 2026-04-29) | **16.3** + **16.4** — make the moat visible: audit trail, hash chain, signed evidence package |

**One-line positioning to encode in product:** *Most "AI for pharma" tools are AI tools that occasionally produce pharma artifacts. EVOLV is a regulated system of record that uses AI to fill it faster.* The model isn't the moat — the system around it is. Sprint 16 makes that system visible.

---

## Sub-feature 16.1 — Light Theme (default light, toggle to dark)

**Goal:** Unblock pilot conversations where users literally can't read the screen.

**Specs:**
- All colors route through CSS variables in `:root`, swapped via `[data-theme='light']` / `[data-theme='dark']` selectors.
- Default theme: `light` for new users (localStorage key `evolv-theme`, mirrors existing `evolv-fontsize` pattern).
- Toggle lives in `TopHeader` next to the font-size toggle. Sun/moon icon, two-state.
- Both themes preserve brand: `--evolv-blue` (#007FFF) stays the same in both; status colors get tone-adjusted variants for AA contrast.

**Proposed light palette (will lock during implementation after contrast audit):**

| Token | Light value | Dark value (current) |
|-------|-------------|---------------------|
| `--bg-base` | `#ffffff` | `#0a0e1a` |
| `--bg-surface` | `#f8fafc` (slate-50) | `#131826` |
| `--bg-elevated` | `#f1f5f9` (slate-100) | `#1c2233` |
| `--text-primary` | `#0f172a` (slate-900) | `#e7ebf3` |
| `--text-muted` | `#475569` (slate-600 — AAA on white) | `#7a8fa3` |
| `--border-subtle` | `rgba(15,23,42,0.1)` | `rgba(255,255,255,0.08)` |
| `--evolv-blue` | `#007FFF` | `#007FFF` |
| `--evolv-lime` | `#16a34a` (green-600 for AA) | `#32CD32` |
| `--error-red` | `#dc2626` (red-600) | `#ef4444` |
| `--warn-amber` | `#d97706` (amber-600) | `#f59e0b` |
| `--adhoc-purple` | `#9333ea` (purple-600) | `#a855f7` |

**Phase 0 — Color audit (must run before coding):**
1. Grep `react-platform/src/` for hardcoded hex (`#[0-9a-fA-F]{3,8}`) outside `index.css` / theme files
2. Grep for hardcoded Tailwind colors that would break in light mode (`bg-slate-900`, `text-white`, etc.)
3. List components needing fixes — if list is over ~10 files, allocate extra time

**Acceptance criteria:**
- [ ] Toggle in TopHeader works, persists across reloads
- [ ] Default theme is light for users who've never set a preference
- [ ] No remaining hardcoded `#hex` in component files (all routed via CSS vars or Tailwind theme)
- [ ] Both themes pass AA contrast (4.5:1 body, 3:1 large text) — verified via DevTools Lighthouse or manual `getContrastRatio` check
- [ ] EVOLV brand kit (`marketing/evolv-brand-kit.md`) updated with light-theme palette

---

## Sub-feature 16.2 — Sample Use Case + Demo Mode

**Goal:** Solve the "first 30s wow" + give Sreejith a one-click way to feed a real end-to-end use case through all 6 modules.

**Anchor scenario:** **Cloud LIMS — Sample Receipt to Disposition**

Why this scenario (not warehouse temp, not lot release):
- Touches all GAMP 5 categories (Cat 1 infra, Cat 3 OOTB receipt module, Cat 4 configured workflows, Cat 5 ELN integration)
- Natural risk variation: administrative receipt = GxP Indirect, CPP testing = GxP Direct
- Universal across biotech + pharma
- Cloud LIMS validation is the most-asked vendor topic in 2026 (legacy systems being replaced)

**Sample data shape (`react-platform/src/data/sampleScenarios.js`):**

```js
export const LIMS_SAMPLE = {
  systemName: "LabCore LIMS v4.2 (Cloud)",
  description: "Cloud-hosted LIMS for sample receipt, testing, disposition.",
  requirements: [
    "The system shall log every sample receipt with operator ID and timestamp.",
    "The system shall enforce 21 CFR Part 11 e-signature for batch disposition.",
    "The system shall block disposition until all CPP tests pass.",
    // 5–7 well-formed reqs across mixed criticality
  ],
  riskMatrix: { /* pre-filled GxP classifications per req */ },
  testBundles: [ /* pre-generated bundles with citations */ ],
  executionResults: [ /* pre-populated pass/fail/adhoc state */ ],
  defects: [ /* one realistic defect with full context */ ],
  // ...all the way to a fully signed Defense Package
};
```

**UI moves:**
- Each module gets a **"Try Sample Use Case"** button in its empty state (top-right of empty-state cards)
- Top-level **"Demo Mode"** toggle in TopHeader — when enabled, all modules show the LIMS sample data without writing to user's actual project
- Demo Mode shows a thin banner: *"Demo Mode — viewing pre-loaded LabCore LIMS sample. Your project data is unaffected."*
- Banner has a **"Restart demo from start"** link that resets state and walks the user from Risk → Requirements → Design → Verify → Release in 60 seconds

**Acceptance criteria:**
- [ ] One full end-to-end LIMS scenario plays through Risk → Requirements → Design → Verify → Release
- [ ] Each phase app has a "Try Sample" button on its empty state
- [ ] Demo Mode toggle in TopHeader, persisted in Zustand under `demoMode: true/false`
- [ ] When Demo Mode is on, the user sees pre-populated state in every module without losing their real project data
- [ ] Sample data feels real (not lorem ipsum) — has actual GAMP 5 references, real RPN scores, real test step text

---

## Sub-feature 16.3 — Validation Defense Package (Release phase reframe)

**Goal:** Make the last 30s of the lifecycle screenshot-worthy. Make it the artifact that visibly answers the $40 ChatGPT critique.

**Reframe:** Today's `Release.jsx` is bare. It becomes the **Validation Defense Package** — the artifact a QA Head would send their VP after a successful validation.

**Page sections (top to bottom):**

1. **Hero** — *"Validation Defense Package — LabCore LIMS v4.2"*
   - Status badge: ✓ Validated · Locked 2026-04-29 14:38 UTC
   - 4 compliance attestation badges (large, click-to-expand):
     - 21 CFR Part 11 ✓
     - EU Annex 11 ✓
     - ALCOA+ ✓
     - GAMP 5 Category 4 ✓
2. **Time-saved card** — *"This validation took 38 minutes. Industry benchmark: 47 hours. Saved 46h 22m."*
   - Footnote: *"Backed by audit trail entries [hash:7f3a...] through [hash:9e2c...]"* — clickable, opens audit drawer (16.4) filtered to this validation
3. **Portfolio context strip** — *"4th validation in your SAP+LIMS landscape · Coverage: 92% · Avg risk: Medium"*
4. **Hash chain visualization** — vertical chain of 8–12 hash blocks, each showing the agent that wrote it, timestamp, action. Visual proof of integrity. Hover to expand.
5. **Download / Share row** — three primary CTAs:
   - **Download Signed PDF** (validation report — already exists in `utils/pdf_generator.py:generate_validation_report_pdf()`)
   - **Copy Auditor Link** (read-only public URL — for Sprint 16, mock with a copy-to-clipboard placeholder; real implementation in Sprint 17)
   - **Export Evidence Bundle** (.zip with PDF + audit trail CSV + logic archives — for Sprint 16, just the PDF)

**Tone:** confident, calm, evidence-first. No emojis except the four ✓ marks. Inter for body, Space Grotesk for hero.

**Acceptance criteria:**
- [ ] Release.jsx renders the Defense Package page when `phaseStatus.release === 'complete'`
- [ ] All 4 compliance badges visible and click-to-expand with what-was-checked detail
- [ ] Time-saved metric pulls from real audit trail timestamps (or sample data in Demo Mode)
- [ ] Hash chain shows actual hashes from `auditTrail` Zustand slice (or simulated hashes in Demo Mode)
- [ ] Download Signed PDF button works end-to-end
- [ ] Page is screenshot-worthy at 1920×1080 (test by taking one)

---

## Sub-feature 16.4 — Live Audit Trail Drawer

**Goal:** Make the moat visible from second 1 of every demo. Every action a user takes appears in the drawer, hash-chained, time-stamped — instantly demonstrating the system-of-record positioning.

**UI:**
- Toggle button in TopHeader: 🔒 icon labeled *"Audit Trail"*
- Drawer slides in from right edge, 420px wide, full height
- Header: *"Live Audit Trail"* with filter dropdown (by phase, by agent, by user) and close button
- Body: vertical list of audit entries, newest at top
  - Each entry: timestamp (mono), agent name, action, user, hash (truncated to 8 chars)
  - Hover any entry → tooltip with full hash + decision logic + linked archive ref
- Footer: 2 actions — *Export current view as CSV* + *View full archive* (links to backend CSV)

**Implementation mode (Sprint 16 — frontend-only):**
- New Zustand slice: `auditTrail: AuditEntry[]` with action `logAuditEvent({agent, action, userId, decisionLogic})`
- Compute SHA-256 hash on the client (Web Crypto API) for visual proof — same shape as backend
- Wire `logAuditEvent` calls into the major Zustand actions that change validation-relevant state:
  - `setRiskAssessment` → `RISK_ASSESSED`
  - `addRequirement` / `transformUrsToUrFr` → `URS_GENERATED` / `URS_TRANSFORMED`
  - `createBundle` / `createManualBundle` → `TEST_BUNDLE_GENERATED`
  - `lockTestRun` → `TEST_RUN_LOCKED`
  - `markQaReviewSigned` → `QA_REVIEW_SIGNED`
  - `setPhaseComplete` → `PHASE_COMPLETED`
- Persist `auditTrail` to localStorage via existing Zustand persist middleware
- Backend CSV integration is **deferred to Sprint 17** — this sprint mocks the user-facing experience

**Acceptance criteria:**
- [ ] Drawer toggleable from TopHeader, persists open/closed state across reloads
- [ ] At least 8 distinct Zustand actions push entries to `auditTrail`
- [ ] Each entry has timestamp, agent, action, user, and a real SHA-256 hash computed client-side
- [ ] Filter dropdown works (by phase, by agent)
- [ ] Export CSV button downloads a 21 CFR Part 11-shaped CSV (timestamp, user_id, agent, action, decision_logic, hash)
- [ ] Drawer feels *alive* during a demo — every meaningful click adds a new entry visibly

---

## Implementation order (Wed → Thu morning)

1. **Phase 0: Color audit** (30 min) — grep hardcoded hex, list components needing fixes
2. **16.1 Light theme** (2–3 hrs) — palette, toggle, audit fixes, brand kit update
3. **16.4 Audit Trail Drawer** (2–3 hrs) — Zustand slice, drawer UI, wiring into existing actions
4. **16.3 Validation Defense Package** (2–3 hrs) — Release.jsx rebuild, badges, hash chain, time-saved card
5. **16.2 Sample data + Demo Mode** (2–3 hrs) — LIMS scenario JSON, "Try Sample" buttons, Demo Mode toggle

Why this order:
- Light theme first — everything else needs to look right in both
- Audit drawer second — 16.3 and Demo Mode both reference its data
- Defense Package third — ties together everything, validates the audit drawer's value
- Sample data last — exercises every prior feature with real data

---

## Out of scope (parking lot for Sprint 17)

- Module shell consistency rebuild (consistent layout across all 6 phase apps) — needs a design pass first
- "Why this?" AI transparency tooltips on every AI-generated output — incremental work, do as we touch each module
- First-run onboarding tour — only meaningful after light theme + sample data land
- Backend audit trail API (real `audit_trail.csv` integration) — Sprint 16 uses frontend-only mock
- Real auditor share-link with read-only public URL — placeholder copy-to-clipboard in 16.3
- Evidence Bundle .zip export with audit trail + logic archives — Sprint 16 ships PDF only
- Pure white marketing brand refresh — keep the dark-mode brand kit unchanged for social posts (dark looks better in feeds)

---

## Open questions to confirm before coding

1. **Confirm light palette tokens** — happy with the slate-50/slate-900/slate-600 picks above, or want a different base hue (e.g. warmer cream `#fefdf8`)?
2. **Confirm anchor scenario** — LIMS is my pick, but if you'd prefer Warehouse Temp or Lot Release I'll re-anchor 16.2.
3. **TopHeader real estate** — adding theme toggle + Demo Mode toggle + Audit Trail button means 3 new icons in the top bar. OK with that, or want to consolidate (e.g. Demo Mode in user-profile menu)?
4. **Time-saved benchmark** — claiming "47 hours industry benchmark." Do you have a defensible source we can cite, or use "industry estimates" as the footnote? (Citation strengthens the claim.)

---

## Definition of done for the sprint

- [ ] All 4 sub-features pass their acceptance criteria
- [ ] Light theme is the new default — no demo will ever start in dark mode again unless user opts in
- [ ] One full LIMS scenario plays end-to-end in Demo Mode in under 60 seconds with one click
- [ ] Defense Package page screenshots cleanly for marketing reuse
- [ ] Audit Trail Drawer has at least 12 entries after a Demo Mode walkthrough — visible proof of the moat
- [ ] CLAUDE.md gets URS-24.1 through URS-24.x rows for traceability
- [ ] MEMORY.md gets Sprint 16 entry under Sprint History with the "why" + pattern notes
- [ ] Single commit (or stacked commits per sub-feature, your call)
