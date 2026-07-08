# Sprint 17 Animation Prompts — for claude.ai Artifacts

Five ready-to-paste prompts that generate **8–12 second looping
animations** for the five LinkedIn posts in the Sprint 17 series
(Requirements Module Overhaul). Plus a **30-second hero animation**
that strings all 7 sub-features together for a Sprint 17 wrap post.

Each one is self-contained HTML/CSS/JS — paste into [claude.ai](https://claude.ai),
get back an Artifact, screen-record it, convert to MP4, attach to your
LinkedIn post.

---

## 🛠️ The Workflow (do this once, then repeat per animation)

### 1. Generate the animation
1. Go to **claude.ai** → start a new chat
2. Paste one of the five prompts below
3. Claude produces an Artifact you can preview right in the browser
4. If you want tweaks ("make the chips slower", "change the engine
   chip text") — ask in plain English. Claude updates the Artifact.

### 2. Capture as video (Windows)
- **ScreenToGif** — https://www.screentogif.com — best free tool for
  this. Records the Artifact area, exports MP4 or GIF.
- **OBS Studio** — free, more powerful, window-capture the browser.
- **Microsoft Clipchamp** — built into Windows 11, has a Screen
  Recorder.

### 3. Format for LinkedIn
- **Aspect ratio:** square 1:1, 1080×1080 (best mobile reach)
  · 9:16 vertical for Reels / Shorts cross-post
- **Duration:** 8–12 seconds, looping seamlessly
- **Format:** MP4 preferred (plays inline). GIF as fallback.
- **File size:** under 5 MB
- **Convert:** https://cloudconvert.com (MP4 → GIF or trim/resize)

### 4. Upload native to LinkedIn (DO NOT link to YouTube)
- Click the video icon in the LinkedIn composer
- Upload the MP4 directly
- Native video reach is **3–5× higher** than external embeds

---

## 🎨 Universal Design Language (already in every prompt below)

These tokens are baked into every prompt — they match the EVOLV brand
**and** the React platform's actual UI. Don't change them.

```
Brand colors (DARK theme — use this for animations):
  --bg-base:       #0a0e1a   (very dark navy, primary background)
  --bg-surface:    #131826   (one shade up — cards/panels)
  --text:          #ffffff   (primary text)
  --text-muted:    #7a8fa3   (secondary text, WCAG AA on bg-base)
  --evolv-blue:    #007FFF   (primary accent, brand wordmark)
  --evolv-lime:    #32CD32   (success / passed / applied)
  --warn-amber:    #f59e0b   (warning / blocked / advisory chips)
  --error-red:     #ef4444   (failure / hard block / vague chip)
  --adhoc-purple:  #a855f7   (refinement panel / manual mode / AI accent)

Typography: Inter or system-ui, font-feature-settings: "ss01"
Animation: cubic-bezier(0.16, 1, 0.3, 1) easing, 300–600ms
Border radius: 8px on cards, 4px on chips
Safe area: 80px margin from canvas edges (LinkedIn crops aggressively)
```

---

# Prompt 1 — Bad-Pattern Sidekick (Sprint 17.5)

**Use this for:** the **Week 1** LinkedIn post — highest emotional pull

**Animation concept:** A practitioner types a bad requirement
(letter-by-letter typewriter). As key phrases land, advisory chips
fire one-by-one beside the row — Vague, Reg-copy, Untestable, Too
long. A muted "advisory" footer reminds the viewer this is **not** a
hard block. Loop.

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode. Background #0a0e1a. Square canvas, 1080x1080,
centered in viewport.

EVOLV brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --warn-amber: #f59e0b
  --text-muted: #7a8fa3    --error-red: #ef4444
                           --adhoc-purple: #a855f7

Font: 'Inter', system-ui. Border radius 8px on cards / 4px on chips.

Scene (12-second loop):
1. (0.0–0.6s) Title fades in at top: "Bad-Pattern Sidekick" white
   24px semibold. Subtitle muted 14px: "Advisory chips. The
   practitioner stays in charge."
2. (0.6–1.4s) A requirement editor row materialises in the centre
   (760x110px, #131826 bg, 1px #2a3142 border, radius 8px). Header
   "UR-1 · Capability" in mono 10px muted. Inside, a single-line
   text field shows a blinking caret.
3. (1.4–5.5s) A typewriter effect (40ms/char) types the sentence:
   "system shall be 21 CFR Part 11 compliant and user-friendly"
   As specific phrases get typed, advisory chips fire from the
   RIGHT edge of the row and dock in a horizontal cluster BELOW
   the row:
     a. After "21 CFR Part 11" types (~3.0s) — chip appears:
          "⚠ Reg-copy" in #f59e0b text on rgba(245,158,11,0.12) bg,
          1px amber border at 30%, 11px medium, padding 4px 10px,
          radius 4px. Slides up + fades in (300ms).
     b. After "user-friendly" types (~5.0s) — chip appears:
          "⚠ Vague: user-friendly" in same amber style.
     c. At 5.5s — chip appears:
          "⚠ No testable trigger" in same amber style.
4. (5.5–6.5s) A fourth chip slides in:
       "⚠ 11 words — but no Condition" in amber.
   The chip cluster now reads (left-to-right):
       [⚠ Reg-copy] [⚠ Vague: user-friendly] [⚠ No testable trigger]
       [⚠ Missing condition]
5. (6.5–8.0s) Below the chip cluster, a small footer band fades
   in (full width of the row, 28px tall, transparent bg, 1px top
   border #2a3142). Footer text:
       "📌 Advisory only — Save with override-justification" in
       #7a8fa3 italic 10px.
   Beside it on the right: a tiny "Override & Save" pill in
   #007FFF text on transparent bg, 1px #007FFF border at 40%
   opacity, 10px, padding 3px 10px, radius 4px.
6. (8.0–10.5s) Hold the full state. The chips pulse gently
   (border-opacity 30% → 60% → 30%, 1.6s loop).
7. (10.5–12.0s) Cross-fade everything to 50% opacity, then back
   to start. Loop forever.

Use CSS keyframes for sequencing. Use a tiny bit of JS only for the
typewriter (setInterval adding chars). All other motion is CSS.
Stay inside an 80px safe-area margin from canvas edges. Add the
"EVOLV" wordmark in #007FFF 12px semibold tracking 0.1em at the
very bottom centre.
```

---

# Prompt 2 — Refine with SMART (Sprint 17.7)

**Use this for:** the **Week 2** LinkedIn post

**Animation concept:** Click the **✨ Refine with SMART** button. A
diff panel opens beneath the row with **original on the left**,
**refined on the right**. A risk badge auto-elevates to High. An
engine-mode chip shows "deterministic." Apply / Dismiss buttons
materialise. The practitioner clicks Apply — capability cell updates,
panel closes with a lime checkmark, sync banner toasts.

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode, EVOLV brand language. Background #0a0e1a.
Square canvas, 1080x1080.

Brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --error-red: #ef4444
  --text-muted: #7a8fa3    --warn-amber: #f59e0b
                           --adhoc-purple: #a855f7

Font: 'Inter', system-ui. Border radius 8px on cards / 4px on chips.

Scene (12-second loop):
1. (0.0–0.5s) Title at top: "Refine with SMART" white 24px
   semibold. Subtitle muted 14px:
       "AI suggests. Practitioner decides. Audit captures both."
2. (0.5–1.2s) A requirement row appears (760x76px, #131826 bg,
   1px #2a3142 border, radius 8px). Inside: ID "UR-1" mono 10px
   muted on the left, then capability text in 13px:
       "system shall be 21 CFR Part 11 compliant and user-friendly"
   On the right edge, a purple pill button:
       "✨ Refine with SMART" in white text on rgba(168,85,247,0.85)
       bg, 11px semibold, padding 6px 14px, radius 6px.
3. (1.2–1.8s) Animated cursor (white triangle, 14px) glides over
   to the Refine button. Button scales 1.0 → 0.96 → 1.0 (click
   ripple). Button text briefly changes to "⏳ Refining…" with
   a thin spinner spin (300ms).
4. (1.8–3.5s) Below the row, a refinement panel materialises
   (760px wide, 280px tall, rgba(168,85,247,0.06) bg, 1px purple
   border, radius 8px). Panel header bar (44px tall, transparent,
   1px bottom border #2a3142):
     LEFT — "✨ SMART REFINEMENT" in #a855f7 12px uppercase tracking
            0.1em
     CENTRE — risk badge "HIGH RISK" in #ef4444 on
              rgba(239,68,68,0.12) bg, 1px red border, 10px bold,
              padding 3px 8px, radius 4px
     CENTRE-NEXT — engine chip "engine: deterministic" in #7a8fa3
                   on transparent bg, 1px #2a3142 border, 10px
                   uppercase, padding 3px 8px, radius 4px
     RIGHT — "Dismiss" link in #7a8fa3 11px
   Below the header, a 2-column grid (each 360px wide) appears:
     LEFT col — label "ORIGINAL" in #7a8fa3 9px uppercase tracking
                0.1em. Below it, in 12px white:
                "system shall be 21 CFR Part 11 compliant and
                 user-friendly"
                The "user-friendly" word has a subtle red strikethrough
                appearing at 3.0s.
     RIGHT col — label "REFINED" in #32CD32 9px uppercase tracking
                 0.1em. Below it, typewriter effect (35ms/char,
                 starting at 2.5s) types:
                 "The system shall be 21 CFR Part 11 compliant and
                  conforming to WCAG 2.1 AA"
                 The "conforming to WCAG 2.1 AA" portion is wrapped
                 in a faint lime highlight box.
5. (3.5–5.0s) Below the diff, an "Acceptance criteria (template)"
   section appears in muted text 10px uppercase. Three single-line
   bullet rows fade in sequentially (every 350ms), each prefixed
   by a tiny bullet "•":
     • Given a valid session, when triggered, then logged
     • Given invalid input, then rejected with validated error
     • Given >= 200 concurrent users, then within thresholds
   Each line truncates at ~70 chars with ellipsis.
6. (5.0–6.0s) Footer bar at bottom of panel (40px tall, transparent,
   1px top border #2a3142). Two pill buttons on the right:
     "Dismiss" in #7a8fa3 on transparent, 1px #7a8fa3 border at 40%
     "Apply refined →" in white on #a855f7 bg, 11px semibold, lime
                       glow on the arrow
7. (6.0–7.5s) Cursor glides to "Apply refined →". Click ripple.
   The original capability text in the row ABOVE the panel
   smoothly cross-fades from the original sentence to the refined
   sentence (with the lime highlight box transferring up). The
   panel collapses (slide up + fade, 500ms).
8. (7.5–9.5s) A tiny toast slides in from the top-right corner
   (240px wide, #131826 bg, 1px lime border, radius 6px):
     line 1 (white 11px) + tiny lime check icon:
       "SMART refinement applied"
     line 2 (muted 10px):
       "Capability cell updated · audit trail recorded"
9. (9.5–10.5s) Hold the full state. Toast remains visible. Row
   has the refined sentence with a subtle lime left-border (2px,
   3 second pulse).
10. (10.5–12.0s) Cross-fade to start state. Loop.

Use CSS transforms (translate, opacity, scale) for performance.
Use a tiny bit of JS for the typewriter and the toast timer.
Stay inside 80px safe-area margins. Add "EVOLV" wordmark in
#007FFF 12px semibold tracking 0.1em at the very bottom centre.
```

---

# Prompt 3 — Workshop-Driven Intake (Sprint 17.4)

**Use this for:** the **Week 3** LinkedIn post

**Animation concept:** A workshop intake form fills itself out — system
description, workshop notes (multi-line), Lucidchart URL, workflow
process. A submit button pulses, a "Generating first-draft URs/FRs…"
banner runs across, then 3 requirement rows materialise in the editor
below — each populated with Capability, Condition, Constraint
prefilled from the workshop notes. Each row gets a tiny "📋 from
workshop" chip.

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode, EVOLV brand language. Background #0a0e1a.
Square canvas, 1080x1080.

Brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --error-red: #ef4444
  --text-muted: #7a8fa3    --warn-amber: #f59e0b
                           --adhoc-purple: #a855f7

Font: 'Inter', system-ui. Border radius 8px on cards / 4px on chips.

Scene (12-second loop):
1. (0.0–0.5s) Title at top: "Workshop-Driven Intake" white 24px
   semibold. Subtitle muted 14px:
       "The workshop IS the authoring step."
2. (0.5–1.0s) An intake form card materialises (760x340px,
   #131826 bg, 1px #2a3142 border, radius 8px). Header bar
   (40px tall): "📋 NEW REQUIREMENTS BATCH" in #007FFF 11px
   uppercase tracking 0.1em.
3. (1.0–4.5s) Inside the form, four field rows appear, with
   typewriter fills (30ms/char, sequential):
     a. (1.0–1.8s) Field label "System Description" in muted 10px.
        Field bg #0a0e1a, 1px #2a3142 border, 36px tall. Types:
          "LIMS replacement — Veeva → LabCore v4.2"
     b. (1.8–3.2s) Field label "Workshop Notes" in muted 10px.
        Multi-line field, 80px tall. Types over 1.4s:
          "Lab lead: chain-of-custody is safety-critical.
           QA: e-sign on disposal step required.
           IT: integrate with SAP via REST."
     c. (3.2–3.8s) Field label "Lucidchart / Diagram URL" in muted
        10px. Single-line field, 36px tall. Types:
          "https://lucid.app/share/labcore-flow"
        Beside it on the right, a small chip:
          "📎 1 file attached" in #7a8fa3 9px uppercase
4. (4.5–5.0s) A wide "Generate first-draft URs and FRs" button
   appears at the bottom of the form (full row width, 44px tall,
   #007FFF bg, white text 13px semibold, radius 6px). Cursor
   glides to it. Click ripple.
5. (5.0–6.0s) Form card collapses (slide up + fade, 500ms). A
   thin progress band appears across the canvas centre (4px tall,
   gradient from #007FFF to #32CD32, sweeps left-to-right) with
   text above it in muted 10px:
       "Generating first-draft URs/FRs from workshop context…"
6. (6.0–9.5s) Three requirement rows materialise sequentially
   (every 700ms), each 760x68px, #131826 bg, 1px #2a3142 border,
   radius 8px. Each row has a 3-column inline layout:
     COL 1 (180px) — ID + chip: "UR-1" mono 11px white, then
                     small "📋 from workshop" chip in
                     rgba(0,127,255,0.12) bg, #007FFF text 9px
                     uppercase, radius 4px.
     COL 2 (380px) — three stacked mini-fields each 18px tall:
       Capability:  "Track sample chain-of-custody"
       Condition:   "When sample changes hands"
       Constraint:  "Per 21 CFR §211.184"
       Each label is muted 8px uppercase; each value is white 11px.
     COL 3 (140px) — owner pill "Lab" on rgba(50,205,50,0.12) bg,
                     #32CD32 text 10px, radius 4px. Below it:
                     functional/non-functional toggle showing
                     "Functional" in #007FFF 9px.
   The 3 rows show:
     UR-1: chain-of-custody / sample handoff / 21 CFR §211.184
     UR-2: e-signature on disposal / batch close / Part 11 §11.50
     UR-3: SAP integration / nightly sync / GAMP 5 §M3
   Owner pills: Lab, QA, IT respectively.
7. (9.5–11.0s) Hold the full state. A muted footer caption fades
   in below the rows (italic 12px #7a8fa3):
       "Workshop notes stamped into every requirement.
        Audit trail starts in the meeting."
8. (11.0–12.0s) Cross-fade to start state. Loop.

Use CSS keyframes for the row materialisation and progress band.
Use a tiny bit of JS for the typewriter fills (one shared helper).
Stay inside 80px safe-area margins. Add "EVOLV" wordmark in
#007FFF 12px semibold tracking 0.1em at the very bottom centre.
```

---

# Prompt 4 — 3 Cs + Stakeholders (Sprint 17.2 + 17.3)

**Use this for:** the **Week 4** LinkedIn post

**Animation concept:** A wall of prose (a "1990s URS template") shimmers
on the left side of the canvas. A diagonal lime sweep wipes across,
"morphing" the prose into 3 structured rows on the right side, each
with **Capability / Condition / Constraint** columns and a
**stakeholder dropdown** that opens to show 7 roles. Functional vs.
Non-Functional toggle pulses on the right edge.

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode, EVOLV brand language. Background #0a0e1a.
Square canvas, 1080x1080.

Brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --error-red: #ef4444
  --text-muted: #7a8fa3    --warn-amber: #f59e0b
                           --adhoc-purple: #a855f7

Font: 'Inter', system-ui. Mono fallback to ui-monospace.
Border radius 8px on cards / 4px on chips.

Scene (12-second loop):
1. (0.0–0.5s) Title at top: "3 Cs Schema + 7 Stakeholders" white
   24px semibold. Subtitle muted 14px:
       "Structure beats prose. Always."
2. (0.5–2.0s) LEFT half of the canvas (440px wide column):
   A "Word doc" mock fades in — #131826 bg, 1px #2a3142 border,
   radius 8px. Header strip "URS_v1.docx" in muted 9px uppercase.
   Inside: a wall of grey prose lines (use placeholder text — short
   wavy paragraph blocks of 9px lighter grey, suggesting prose
   without being readable). Apply a subtle red corner stamp:
       "⚠ UNREVIEWABLE" in red 10px tracking 0.05em at 30° rotate.
3. (2.0–3.0s) A diagonal lime sweep (gradient from
   rgba(50,205,50,0) to rgba(50,205,50,0.4) and back to 0,
   80px wide, 60° angle) sweeps from the bottom-left to the
   top-right of the prose card over 1.0s. As it passes, the prose
   lines fade out behind it.
4. (3.0–6.0s) RIGHT half of the canvas (440px wide column):
   Three structured rows fade in sequentially (every 800ms), each
   460x96px, #131826 bg, 1px #2a3142 border, radius 8px. Per row:
     - Header: ID "UR-1" mono 10px + functional toggle pill
       (small, 90x20px, "Functional" in #007FFF on
       rgba(0,127,255,0.12) bg, radius 12px).
     - 3 horizontal mini-cells, each 130px wide:
         CELL 1: label "CAPABILITY" muted 8px uppercase. Value:
                 "Track temperature" white 11px.
         CELL 2: label "CONDITION" muted 8px uppercase. Value:
                 "When stored < 8°C" white 11px.
         CELL 3: label "CONSTRAINT" muted 8px uppercase. Value:
                 "Per USP <1079>" white 11px.
     Three rows show different content:
       UR-1: Track temperature / When stored < 8°C / USP <1079>
       UR-2: Notify lab / On excursion >2°C / 5 minutes max
       UR-3: Audit log entries / On every change / 21 CFR §11.10
5. (6.0–7.5s) Below the third row, a stakeholder dropdown opens
   (animated). The dropdown trigger says "Owner: Lab ▾" on the
   row. Click ripple. The dropdown menu opens DOWN with 7 options
   each 24px tall, slide-down stagger 60ms each:
       Senior Mgmt
       Lab            ← current selection, lime check left
       IT
       QA / ITQA
       Procurement
       Supplier
       Data Owner
   Menu bg #131826, 1px #2a3142 border, radius 6px, hover state
   shown on "Lab".
6. (7.5–9.0s) Dropdown closes. A small label below the rows fades
   in muted italic 10px:
       "Functional vs. Non-Functional · 7 GxP roles · 1 Data Owner"
7. (9.0–10.5s) A connector arrow (lime, 2px, with arrowhead) appears
   between the LEFT prose card and the RIGHT structured rows,
   running diagonally. Above it, in 9px lime uppercase tracking
   0.1em: "REDESIGNED, NOT DIGITISED".
8. (10.5–12.0s) Cross-fade to start state. Loop.

Use CSS animations for the sweep, dropdown stagger, and row reveals.
Stay inside 80px safe-area margins. Add "EVOLV" wordmark in
#007FFF 12px semibold tracking 0.1em at the very bottom centre.
```

---

# Prompt 5 — Mode Toggle (Sprint 17.6 + 17.1) — Series Wrap

**Use this for:** the **Week 5** LinkedIn post (Sprint 17 wrap)

**Animation concept:** A segmented toggle "📋 Workshop ⇄ ✍ Manual"
flips back and forth. On Workshop side: the intake form is visible.
On Manual side: the form collapses and the 3 Cs editor takes the full
surface. Both sides keep the chip cluster + Refine button visible —
**emphasising "AI optional, schema mandatory."** Tagline: *Same audit
trail, regardless of mode.*

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode, EVOLV brand language. Background #0a0e1a.
Square canvas, 1080x1080.

Brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --error-red: #ef4444
  --text-muted: #7a8fa3    --warn-amber: #f59e0b
                           --adhoc-purple: #a855f7

Font: 'Inter', system-ui. Border radius 8px on cards / 4px on chips.

Scene (12-second loop):
1. (0.0–0.5s) Title at top: "Workshop ⇄ Manual" white 24px
   semibold. Subtitle muted 14px:
       "AI optional. Schema mandatory."
2. (0.5–1.5s) A segmented toggle appears centred under the title.
   Two segments, each 180x36px, joined into one pill:
     LEFT: "📋 Workshop" in white on rgba(0,127,255,0.12) bg,
           1px blue border, currently selected (slight glow).
     RIGHT: "✍ Author Manually" on transparent bg, muted text.
   Toggle pill total width 360px, 1px #2a3142 outer border, radius
   18px.
3. (1.5–4.0s) BELOW the toggle (Workshop mode active):
   A workshop intake form card materialises (760x180px, #131826,
   1px #2a3142, radius 8px). Inside: 3 stacked field placeholders
   with light filler:
       "System Description: LIMS replacement — LabCore v4.2"
       "Workshop Notes: chain-of-custody safety-critical… (3 lines)"
       "Lucidchart URL: https://lucid.app/share/labcore-flow"
   Below the form, a single editor row appears (760x68px, #131826,
   1px #2a3142, radius 8px) with placeholder text "(generated row
   appears here)" muted italic 11px.
4. (4.0–4.5s) A cursor glides to the "✍ Author Manually" segment.
   Click ripple. The toggle pill's blue selection slides RIGHT
   (smooth 400ms ease) and turns purple — RIGHT segment now has
   purple bg rgba(168,85,247,0.15), purple text, 1px purple border.
5. (4.5–5.5s) The workshop form card collapses (slide up + fade,
   600ms). The editor row expands to fill the vertical space the
   form vacated, becoming a 3-row 3 Cs editor table (760x220px,
   3 rows of 60px each + a 36px header strip).
6. (5.5–8.0s) Three editor rows fill in (typewriter 30ms/char,
   sequential):
     UR-1: Capability "Track temperature" / Condition "When stored
           < 8°C" / Constraint "Per USP <1079>" / Owner "Lab"
     UR-2: Capability "Notify lab" / Condition "On excursion >2°C"
           / Constraint "5 minutes" / Owner "QA"
     UR-3: Capability "Audit log entries" / Condition "On every
           change" / Constraint "21 CFR §11.10" / Owner "IT"
   Each row's right edge has a small "✨ Refine" purple icon
   button (24x24px, no text, just sparkle icon).
7. (8.0–9.5s) On the FIRST row, two advisory chips fade in below
   the row text:
       [⚠ Reg-copy candidate] [⚠ Tighten condition]
   in amber on rgba(245,158,11,0.12), as in Prompt 1's style.
   This emphasises that the **chips and refine work in BOTH modes**.
8. (9.5–10.5s) A tagline fades in below the editor table, muted
   italic 12px:
       "Same chips. Same refine. Same audit trail. Mode is yours."
9. (10.5–12.0s) Cross-fade — toggle pill swings back to Workshop
   selected. Form card re-materialises. Editor row collapses to
   placeholder. Loop.

Use CSS transforms (translateX, opacity, scale) plus a small JS
helper for the typewriter. Stay inside 80px safe-area margins. Add
"EVOLV" wordmark in #007FFF 12px semibold tracking 0.1em at the
very bottom centre.
```

---

## 🎬 Pro Tips (so the animations actually convert)

### Visual hierarchy
1. **First 2 seconds = the hook.** LinkedIn auto-plays muted —
   if your animation isn't visually compelling in 2s, the viewer
   keeps scrolling. Front-load the title and the first beat.
2. **Use motion to direct the eye.** Each animation has ONE focal
   moment (the chip cluster / the diff panel / the workshop fill /
   the prose-to-schema sweep / the toggle flip). Don't dilute it.
3. **End on the brand mark.** Every prompt includes "EVOLV" at
   the bottom. Don't remove it — that's the whole point.

### Loop hygiene
- The cross-fade at the end (every prompt has one) hides the
  reset frame. Don't shorten it below 1.5s or the loop will
  feel jerky.
- LinkedIn loops natively after the first play — make sure the
  last frame matches the first frame (the cross-fade does this).

### Captions / accessibility
- Add **subtitles overlaid on the video** in your editor (Clipchamp,
  CapCut). 80% of LinkedIn views are muted. The animation alone
  should tell the story, but a 1-line caption per beat helps.
- Suggested caption text per animation:
  - **Sidekick (17.5):** "Advisory chips. Override = audit-trailed."
  - **Refine SMART (17.7):** "AI suggests. You decide. Audit captures."
  - **Workshop (17.4):** "The workshop IS the authoring step."
  - **3 Cs (17.2/17.3):** "Structure beats prose."
  - **Mode Toggle (17.6/17.1):** "AI optional. Schema mandatory."

### File preparation
1. Record at 1080×1080 @ 30fps in your screen recorder
2. Trim to exactly the loop length (12s)
3. Export as MP4 (H.264, ~3 Mbps bitrate — keeps file under 5 MB)
4. Test the loop on your phone before posting

### Iteration trick
After Claude generates the first Artifact, ask follow-ups in
plain English:
- "Slow the typewriter to 50ms per character."
- "Make the engine chip text say 'engine: gpt-4o-mini'."
- "Replace the workshop notes filler with [your real text]."
- "Add a subtle drop-shadow under the diff panel."

Each tweak takes ~10 seconds and you keep the same Artifact open.

---

## 🚀 Bonus — Sprint 17 Hero Animation (one to rule them all)

If you want a SINGLE 30-second hero video that strings all 5 features
together, use this as your **Sprint 17 wrap pinned post**, your
**YouTube channel trailer**, or your **homepage hero loop**.

### Paste this into claude.ai

```
Build a self-contained HTML/CSS/JS Artifact: a 30-second looping
animation that walks through 5 EVOLV Sprint 17 features in sequence.
Dark mode (#0a0e1a), 1080x1080 square, EVOLV brand language.

Brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --error-red: #ef4444
  --text-muted: #7a8fa3    --warn-amber: #f59e0b
                           --adhoc-purple: #a855f7

Font: 'Inter', system-ui. Border radius 8px on cards / 4px on chips.

Beats:
  0.0–6.0s   "Bad-Pattern Sidekick" — typewriter fills a vague
             requirement; 4 advisory chips fire in sequence
             (Reg-copy / Vague / Untestable / Missing condition).
             Footer "Advisory only — Save with override-justification".
  6.0–13.0s  "Refine with SMART" — a purple Refine button on the
             same row pulses; diff panel opens (Original |
             Refined); risk badge "HIGH"; engine chip
             "deterministic"; Apply button click; capability cell
             cross-fades to refined text; lime toast "SMART
             refinement applied".
 13.0–19.0s  "Workshop Intake" — workshop form fills itself
             (3 typewriter fields + 1 attachment chip); Submit
             click triggers a thin gradient progress band; 3
             rows materialise below with "📋 from workshop"
             chips + 3 Cs columns + Lab/QA/IT owner pills.
 19.0–25.0s  "3 Cs + Stakeholders" — a "URS_v1.docx" prose card on
             left "morphs" via a lime diagonal sweep into the 3
             structured rows on right; stakeholder dropdown opens
             showing all 7 roles; small label "REDESIGNED, NOT
             DIGITISED" appears between the two halves.
 25.0–28.0s  "Workshop ⇄ Manual" — segmented toggle pill swings
             between Workshop and Manual; below it, a unified row
             with chips + Refine button persists across both
             modes; tagline appears: "Same chips. Same refine.
             Same audit trail."
 28.0–30.0s  Final hold — all 5 feature names tile into a 2×3
             grid (one slot empty or used for the EVOLV wordmark
             enlarged). Title above the grid:
             "Sprint 17 — Requirements Module Overhaul"
             Subtitle below the grid:
             "AI inside a governed workflow — not in a corner."
             EVOLV wordmark in #007FFF 14px semibold tracking
             0.1em at the very bottom centre.

Use the EVOLV brand tokens defined above. Each beat should have a
smooth cross-fade transition (500ms) into the next. Keep all
content inside an 80px safe-area margin from canvas edges. Loop
seamlessly — last frame must visually match first frame.
```

---

## 📐 Layout reference (in case you want to tweak by hand)

The 5 individual prompts and the hero animation share a consistent
layout grid you can rely on if you decide to remix:

| Element | Width | Height | Notes |
|---------|-------|--------|-------|
| Title row | 920px | 48px | Top of canvas, 80px safe-area below the top edge |
| Subtitle | 920px | 24px | 8px below title, muted 14px |
| Main content card | 760px | 200–340px (varies) | Centred, 60px gap below subtitle |
| Chip cluster (advisory) | 720px | 32px | 16px below content card row, horizontal flex |
| Footer caption / brand | 720px | 28px | 24px above bottom safe-area |
| EVOLV wordmark | auto | 16px | Last 60px of canvas, centred |

This grid keeps everything inside the 80px LinkedIn safe area while
giving each animation enough breathing room to feel premium.

---

## 🎯 The "why these animations" tying back to the UiPath CTO insight

Each animation visualises a **different facet of governed AI**:

| Animation | The visible motion | The hidden message |
|-----------|---------------------|--------------------|
| Sidekick | Chips fire one-by-one | AI as **reviewer**, not decider |
| Refine SMART | Diff panel + Apply | **Workflow reliability** — practitioner sees engine mode, decides |
| Workshop Intake | Form fills, rows generate | **Coordination beats isolation** — context is first-class |
| 3 Cs + Stakeholders | Prose sweeps into structure | **Redesign, not lift-and-shift** |
| Mode Toggle | Toggle flips, chips persist | **AI optional, schema mandatory** — gradient adoption |

The hero animation is the **proof that all five connect into one
governed workflow** — the UiPath CTO's "connective tissue" frame, made
visible in 30 seconds.
