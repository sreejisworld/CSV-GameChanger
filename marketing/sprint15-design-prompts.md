# Sprint 15 Animation Prompts — Claude Design Edition

**Restructured from `sprint15-animation-prompts.md` into the format Claude Design (and most timeline-based animation builders) understand best:** scene cards with explicit asset lists, timing tables, and motion verbs. Brand tokens are pulled from `evolv-brand-kit.md` — do not edit them inline.

> **Note on Claude Design specifics:** I haven't used Claude Design's exact prompt UI directly. The structure below is the universal "scene card + timing table + asset list" format that works in Claude Design, Rive, Jitter, Lottie editors, and Framer Motion. If Claude Design wants a different schema (JSON, YAML, plain prose), the content fields below are what to paste into their slots — just rearrange the wrapper.

---

## Universal Setup (paste once at the top of each Claude Design session)

```
PROJECT: EVOLV Sprint 15 social animations
CANVAS: 1080×1080 square (LinkedIn feed)
DURATION: 12 seconds, seamless loop
FRAMERATE: 30fps
EASING DEFAULT: cubic-bezier(0.4, 0, 0.2, 1)  // Material standard
LOOP HYGIENE: last frame must match first frame pixel-for-pixel

BRAND TOKENS (lock these — do not substitute):
  bg-base:        #0a0e1a
  bg-surface:     #131826
  bg-elevated:    #1c2233
  evolv-blue:     #007FFF
  evolv-lime:     #32CD32
  evolv-blue-soft:   rgba(0,127,255,0.15)
  evolv-lime-soft:   rgba(50,205,50,0.15)
  text-primary:   #e7ebf3
  text-muted:     #7a8fa3
  border-subtle:  rgba(255,255,255,0.08)
  error-red:      #ef4444
  warn-amber:     #f59e0b
  adhoc-purple:   #a855f7

FONTS (Google Fonts — request all three at scene init):
  Space Grotesk 600/700  — headers, hero text
  Inter 400/500/600       — body, captions
  JetBrains Mono 500      — IDs, timestamps, status codes

WRAPPER (every scene must have this chrome):
  Header strip:  64px tall, bg-elevated
                 left:  "EVOLV" wordmark (Space Grotesk 700, 18px, text-primary, letter-spacing 0.04em)
                 right: tag chip — see per-scene
  Demo zone:     880px tall, bg-surface, 16px corner radius
  Footer strip:  64px tall, bg-elevated
                 left:  "The Validation Factory" (Inter 500, 13px, text-muted, uppercase, ls 0.08em)
                 right: "evolv.app — coming May 2026" (Inter 500, 13px, text-muted)
```

---

## Scene 1 — Coverage Gap Detector (Sprint 15.3)

**Tag chip (header right):** `Sprint 15.3` in `evolv-blue-soft` background, `evolv-blue` text, JetBrains Mono 500, 12px, 8px×4px padding, 4px radius

**Hero line (top of demo zone):**
> **"Every UR covered. Or none of you go home."**
> Space Grotesk 700, 32px, text-primary, centered, 40px from top of demo zone

**Asset list:**
- 8 UR cards in a 4×2 grid
  - Card size: 180×100px, 12px gap between cards
  - Card bg: `bg-elevated`, 1px `border-subtle`, 12px corner radius
  - Card content (top-left, 12px padding):
    - Line 1: `UR-{N}` in JetBrains Mono 500, 14px, text-muted
    - Line 2: 2-line truncated requirement summary in Inter 500, 12px, text-primary
- Coverage progress bar (below grid, 32px gap)
  - Track: 600×8px, `bg-elevated`, 4px radius, centered
  - Fill: starts 0px, animates to 700/800ths (87.5%) of width, `evolv-lime` color
  - Label below bar: `7 of 8 GxP Direct URs covered` in Inter 600, 14px, text-primary
- Red gap banner (slides down from above the wrapper at end)
  - 1080×80px strip, `error-red` at 15% opacity backdrop, 1px `error-red` border-bottom
  - Icon left: ⚠ in 24px, error-red
  - Text: `Design phase blocked — UR-7 has no test bundle` Inter 600, 16px, text-primary
  - Right side: button-styled chip `Generate now →` in evolv-blue bg, white text

**Timing table:**

| Time (s) | Action | Easing |
|----------|--------|--------|
| 0.0 | Scene appears: 8 grey UR cards in grid (no fill yet), bar empty, no banner | — |
| 0.5 | Hero line fades in (opacity 0→1) and rises 20px | cubic-bezier(0.4, 0, 0.2, 1) over 400ms |
| 1.5 | Card 1 (UR-1) fills with `evolv-lime-soft` bg + `evolv-lime` left border (4px) — bar nudges to 1/8 | 250ms |
| 2.0 | Card 2 fills + bar to 2/8 | 250ms |
| 2.5 | Card 3 fills + bar to 3/8 | 250ms |
| 3.0 | Card 4 fills + bar to 4/8 | 250ms |
| 3.5 | Card 5 fills + bar to 5/8 | 250ms |
| 4.0 | Card 6 fills + bar to 6/8 | 250ms |
| 4.5 | **Card 7 (UR-7) attempts to fill — flashes `error-red` border twice and stays grey** | 400ms shake |
| 5.0 | Card 8 fills + bar to 7/8 (stops) | 250ms |
| 5.5 | Brief pause — bar pulses `warn-amber` once (entire bar fill flashes 100%→70% opacity→100%) | 600ms |
| 6.5 | Red gap banner slides down from y=-80px to y=0 above hero line, pushing content down 80px | 500ms ease-out |
| 7.5 | Banner sits steady; "Generate now →" button has subtle 2px `evolv-blue` glow pulse | 1.5s pulse loop |
| 10.5 | Banner slides back up, content returns to original Y | 500ms ease-in |
| 11.0 | All cards fade to grey, bar drains to 0, hero line fades out | 800ms |
| 12.0 | Frame matches t=0 — loop point | — |

**Sound design (if Claude Design supports it — otherwise skip):** subtle UI tick on each card fill, soft "denied" tone on UR-7 shake, low rumble swell on banner drop.

---

## Scene 2 — Pre-Lock QA Review (Sprint 15.4)

**Tag chip:** `Sprint 15.4`

**Hero line:**
> **"Two signatures. Independent. Per 21 CFR Part 11 §11.10(b)."**
> Space Grotesk 700, 28px, text-primary, centered

**Asset list:**
- Left column (520×620px, demo zone): "Test Run TR-2026-042"
  - 8 step rows stacked, each 480×56px, `bg-elevated` bg, 1px `border-subtle`, 8px gap
  - Row content: `Step {N}` in mono left, status pill right
  - Status pills: 5× `PASS` (evolv-lime-soft bg, evolv-lime text), 2× `FAIL` (error-red bg-soft, error-red text), 1× `ADHOC` (adhoc-purple bg-soft, adhoc-purple text)
- Right column (440×620px): "QA Review Panel"
  - Panel bg: `bg-surface`, 1px `border-subtle`, 12px radius, 24px padding
  - Title: `🛡 QA Review` Space Grotesk 600, 18px, text-primary
  - 4-point checklist (each row is 380×40px):
    1. ☐ Actual results documented for all failed steps
    2. ☐ Defects logged for all failures
    3. ☐ Evidence attached for all failures
    4. ☐ Adhoc steps justified
  - Reviewer name field (placeholder: "Reviewer name")
  - "Sign Review" button — 380×44px, disabled state grey at start, enabled state evolv-blue bg
- 2 signature stamps (appear at end):
  - Stamp 1 (executor): `Signed: J. Patel · 14:32:08 UTC` Inter 500, 12px, text-muted
  - Stamp 2 (reviewer): `Reviewed: M. Chen · 14:38:51 UTC` Inter 500, 12px, evolv-blue
  - Both with thin `border-subtle` 4px corner radius, 8px×4px padding

**Timing table:**

| Time (s) | Action | Easing |
|----------|--------|--------|
| 0.0 | Both columns visible, all 4 checks empty, button disabled | — |
| 0.5 | Hero line fades in | 400ms |
| 1.5 | The 2 FAIL rows + 1 ADHOC row "magnetise" toward QA panel — they don't move, but get a glowing `evolv-blue` border + 8px outer shadow | 500ms |
| 2.5 | Connecting lines (1px dashed `evolv-blue`) draw from each highlighted row to the QA panel | 600ms stroke-dashoffset |
| 4.0 | Check 1 ticks itself — checkbox fills `evolv-lime`, hint text appears below: "auto-OK · 2 fails have actual results" Inter 500, 11px, text-muted | 200ms |
| 4.5 | Check 2 ticks — hint: "auto-OK · 2 defects linked" | 200ms |
| 5.0 | Check 3 ticks — hint: "auto-OK · evidence attached" | 200ms |
| 5.5 | Check 4 ticks — hint: "auto-OK · adhoc step justified" | 200ms |
| 6.5 | Reviewer name field types out "Maya Chen" letter by letter (60ms per char) | 600ms total |
| 7.5 | Sign Review button transitions disabled→enabled (grey→evolv-blue, lift shadow appears) | 300ms |
| 8.0 | Button receives a subtle press (scale 1→0.96→1) | 200ms |
| 8.5 | Stamp 1 (executor) fades in below test run column | 300ms |
| 9.0 | Stamp 2 (reviewer) fades in below QA panel — has a subtle blue glow pulse | 300ms |
| 9.5 | Both stamps connected by a horizontal `evolv-blue` hairline (4px dashed), with center label "Independent attestation" in Inter 500 11px text-muted | 600ms |
| 11.0 | Everything fades back: stamps gone, checks unticked, name field empty, button re-disabled | 800ms |
| 12.0 | Loop point | — |

---

## Scene 3 — Adhoc Step Insertion (Sprint 15.2)

**Tag chip:** `Sprint 15.2`

**Hero line:**
> **"Tester sees something off. Adds a step. Audit trail stays bulletproof."**
> Space Grotesk 700, 24px, text-primary, centered, 2 lines

**Asset list:**
- Test execution table (centered, 800×500px)
  - Column headers: `#` `Step Title` `Status`
  - Header bg: `bg-elevated`, Inter 600 13px text-muted uppercase, 16px padding
  - 5 row stubs, each 800×60px, alternating `bg-surface` and `bg-elevated`
    - Row 1: `1` · "Login as System Owner" · ✓ PASS
    - Row 2: `2` · "Navigate to lot release screen" · ✓ PASS
    - Row 3: `3` · "Verify FR-1 — Positive case" · ✓ PASS
    - Row 4: `4` · "Verify FR-2 — Negative case" · ⏳ PENDING (text-muted)
    - Row 5: `5` · "Verify FR-3 — Edge case" · ⏳ PENDING
- Cursor (appears mid-scene): standard arrow cursor, 24px
- Insert button (appears between row 3 and row 4 on hover):
  - 800×32px dashed-border zone, `evolv-blue` 1px dashed, transparent bg
  - Label: `+ Insert adhoc step` Inter 500 13px evolv-blue, centered
- Inline form (replaces insert zone after click):
  - Same 800×{auto}px slot, `bg-surface`, 1px `border-subtle`, 12px radius
  - Title: `⚡ Adhoc Step Insertion` Space Grotesk 600 16px adhoc-purple
  - Field 1: Step title input (placeholder "What did you observe?")
  - Field 2: Justification textarea (placeholder "Why is this step needed?")
  - Buttons: `Cancel` (ghost) + `Insert as 3.1` (adhoc-purple bg)
- New row 3.1 (replaces form when submitted):
  - 800×60px, `adhoc-purple` 4px left border, otherwise normal row styling
  - Cell content: `3.1` · "Capture screenshot of label misalignment" · ⚡ ADHOC pill (adhoc-purple-soft bg, adhoc-purple text)
- Audit toast (top-right corner of demo zone):
  - 320×80px, `bg-elevated`, 1px `border-subtle`, 12px radius, 16px padding
  - Line 1: `✓ Audit event logged` Inter 600 14px evolv-lime
  - Line 2: `tester-adhoc · M. Chen · 14:35:22 UTC` JetBrains Mono 500 11px text-muted
  - Line 3: `Reason: "Observed label misalignment"` Inter 400 11px text-muted

**Timing table:**

| Time (s) | Action | Easing |
|----------|--------|--------|
| 0.0 | Table visible, 3 PASS rows + 2 PENDING, no cursor, no form | — |
| 0.5 | Hero line fades in | 400ms |
| 1.5 | Cursor enters from bottom-right, glides to the gap between row 3 and row 4 | 800ms ease-out |
| 2.5 | Insert zone (dashed `+ Insert adhoc step`) appears with a soft `evolv-blue` glow | 250ms |
| 3.5 | Cursor clicks (small ripple effect at cursor tip) | 150ms |
| 3.7 | Insert zone morphs into inline form (height grows from 32px to 200px, content fades in) | 400ms |
| 4.5 | Step title field types: "Capture screenshot of label misalignment" (40ms per char) | 1.4s |
| 6.0 | Justification field types: "Observed label misalignment" (40ms per char) | 0.9s |
| 7.0 | Cursor moves to "Insert as 3.1" button | 300ms |
| 7.4 | Button press (scale 1→0.96→1) | 150ms |
| 7.7 | Form collapses, new row 3.1 slides into place between rows 3 and 4 — pushes rows 4–5 down by 60px | 500ms ease-out |
| 8.3 | Audit toast slides in from top-right (translateX 100%→0) with `evolv-lime` left border flash | 400ms |
| 9.0 | ⚡ ADHOC pill on row 3.1 pulses once (scale 1→1.08→1) | 400ms |
| 10.5 | Toast slides out, row 3.1 stays visible | 400ms |
| 11.5 | Row 3.1 fades out, rows 4–5 slide back up, cursor exits | 500ms |
| 12.0 | Loop point | — |

---

## Scene 4 — Manual Authoring (Sprint 15.1)

**Tag chip:** `Sprint 15.1`

**Hero line:**
> **"AI-generated when you want it. Hand-crafted when you need it."**
> Space Grotesk 700, 26px, text-primary, centered

**Asset list:**
- Mode toggle (top of demo zone, 320×40px, centered):
  - Pill background: `bg-elevated`, 20px radius
  - Two segments: `Generate with AI` (left, default active) | `Author Manually` (right)
  - Active segment: `evolv-blue` bg, white text
  - Inactive: transparent bg, text-muted
- Step composer panel (below toggle, 800×500px):
  - `bg-surface`, 1px `border-subtle`, 12px radius
  - Title: `Test Bundle: TB-UR-7` JetBrains Mono 500 14px text-muted
- 3 step rows (built up sequentially):
  - Each 760×80px, `bg-elevated`, 1px `border-subtle`, 8px radius, 8px gap
  - Row content (left to right):
    - Step number badge: 32×32px circle, `evolv-blue-soft` bg, `evolv-blue` text, JetBrains Mono 600 14px
    - Step title: Inter 600 14px text-primary
    - Step body: Inter 400 13px text-muted (2 lines max)
    - Citation chip (right edge): chip with regulation reference
- Citation chips (3 to dock onto the 3 steps):
  - Chip 1: `21 CFR §11.10(e)` evolv-blue-soft bg, evolv-blue text
  - Chip 2: `EU Annex 11 §9` evolv-lime-soft bg, evolv-lime text
  - Chip 3: `GAMP 5 Cat 4` warn-amber bg-soft, warn-amber text
  - Chip style: JetBrains Mono 500 11px, 8px×4px padding, 4px radius
- Quality gauge (bottom-right of demo zone, 200×200px):
  - Circular meter with 5 segments (each 72° arc)
  - Center text: `0 / 5` → `5 / 5` (Space Grotesk 700 32px)
  - Segment fill color: `evolv-lime` when ticked, `bg-elevated` when empty
  - Label below: `Quality checks` Inter 500 12px text-muted

**Timing table:**

| Time (s) | Action | Easing |
|----------|--------|--------|
| 0.0 | Toggle on "Generate with AI", composer empty, gauge at 0/5 | — |
| 0.5 | Hero line fades in | 400ms |
| 1.5 | Cursor glides to toggle, clicks right segment | 800ms |
| 1.7 | Toggle slides: active pill animates from left segment to right segment | 350ms ease-in-out |
| 2.0 | Composer subtitle changes from "AI will generate steps" to "Author manually" — fade swap | 250ms |
| 2.8 | Step row 1 appears empty (just frame + step number "1") | 200ms |
| 3.0 | Step 1 title types: "Login as System Owner" (40ms per char) | 0.8s |
| 3.8 | Step 1 body types: "Confirm role-based access per FR-1" (40ms per char) | 1.2s |
| 5.0 | Citation chip 1 (`21 CFR §11.10(e)`) flies in from outside frame and docks on right edge of step 1 | 400ms ease-out |
| 5.4 | Quality gauge: segment 1 fills `evolv-lime`, counter ticks `0 / 5` → `1 / 5` | 250ms |
| 5.8 | Step row 2 appears, title types: "Verify lot release approval" | 0.8s |
| 6.6 | Step 2 body types: "Trigger Approve action; confirm e-sig prompt" | 1.2s |
| 7.8 | Citation chip 2 docks onto step 2 | 400ms |
| 8.2 | Gauge: `1 / 5` → `2 / 5` | 250ms |
| 8.4 | Step row 3 appears, title types: "Capture audit trail entry" | 0.8s |
| 9.2 | Step 3 body types: "Verify ALCOA+ entry created within 5s of e-sig" | 1.2s |
| 10.0 | Citation chip 3 docks onto step 3 | 400ms |
| 10.4 | Gauge: `2 / 5` → `5 / 5` (jumps as remaining quality checks auto-pass) | 600ms |
| 10.8 | Gauge gets a 600ms `evolv-lime` glow pulse | 600ms |
| 11.4 | All steps and chips fade out, gauge drains to 0, toggle slides back to "Generate with AI" | 600ms |
| 12.0 | Loop point | — |

---

## Bonus — 30-Second Sprint 15 Hero Reel

For a "Sprint 15 wrap" post, chain all 4 scenes back-to-back at 7s each (with 0.5s crossfade between) plus a 2s end card:

**End card (2s):**
- Black bg-base canvas
- Centered:
  - EVOLV wordmark (Space Grotesk 700, 64px, text-primary)
  - Subtitle: "THE VALIDATION FACTORY" (Inter 500, 16px, text-muted, uppercase, ls 0.12em)
  - Tag line below: "Sprint 15 — Tester-in-the-Loop + Coverage Confidence" (Inter 400, 18px, evolv-blue)
  - URL: "evolv.app · pilot starts May 2026" (JetBrains Mono 500, 14px, text-muted)
- Fade in 400ms, hold 1.2s, fade out 400ms
- Final frame matches first frame of Scene 1 → seamless rewind for replay

**Total runtime:** 30 seconds. Resolution: 1920×1080 landscape (LinkedIn native video sweet spot).

---

## After Claude Design Generates the Asset

1. Download as MP4 (H.264, 1080p) — never GIF for LinkedIn (too large, low quality)
2. Verify file size is under **10MB** (LinkedIn limit before quality drop)
3. Add burned-in captions if the animation has any spoken/text-driven content
4. Save to `marketing/assets/` per the naming convention in `evolv-brand-kit.md` §9
5. Run pre-publish checklist (`evolv-brand-kit.md` §10)
6. Upload to LinkedIn natively (don't link to YouTube — kills reach)

If Claude Design's output looks off, the most common fixes are:
- **Colors drift slightly:** force-paste the BRAND TOKENS block again at the top of your prompt
- **Timing feels rushed:** double every duration in the timing table; total can grow to 14–15s, still loops fine
- **Text too small at LinkedIn feed size:** bump every type-scale value up by 4px
- **Loop visible seam:** ensure t=12.0s state matches t=0.0s state exactly — every element back to start position, opacity, scale
