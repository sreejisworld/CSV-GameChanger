# Sprint 15 Animation Prompts — for claude.ai Artifacts

Four ready-to-paste prompts that generate **8–12 second looping
animations** for the four LinkedIn posts. Each one is self-contained
HTML/CSS/JS — you copy the prompt into [claude.ai](https://claude.ai),
get back an Artifact, screen-record it, convert to MP4, and attach
directly to your LinkedIn post.

---

## 🛠️ The Workflow (do this once, then repeat per animation)

### 1. Generate the animation
1. Go to **claude.ai** → start a new chat
2. Paste one of the four prompts below
3. Claude produces an Artifact you can preview right in the browser
4. If you want tweaks ("make the red banner slower", "use a darker
   background"), just ask in plain English — Claude updates the
   Artifact in place

### 2. Capture it as video (Windows)
- **ScreenToGif** (free, open source — best for this) →
  https://www.screentogif.com → records the Artifact area, exports
  MP4 or GIF
- **OBS Studio** (free, more powerful) → window-capture the browser,
  export MP4
- **Microsoft Clipchamp** (built into Windows 11) → use Screen
  Recorder, then trim

### 3. Format for LinkedIn
- **Aspect ratio:** square (1:1, 1080×1080) — best mobile reach.
  9:16 vertical works too if you're cross-posting to Reels.
- **Duration:** 8–12 seconds, looping seamlessly
- **Format:** MP4 (preferred — plays inline) or GIF (good fallback)
- **File size:** under 5 MB
- **Convert if needed:** https://cloudconvert.com (MP4 → GIF or
  trim/resize)

### 4. Upload native to LinkedIn (DO NOT link to YouTube)
- Click the video icon in the LinkedIn composer
- Upload the MP4 directly
- Add 1-line caption + your post text
- Native video reach is **3–5× higher** than external embeds

---

## 🎨 Universal Design Language (already in every prompt below)

These tokens are baked into every prompt — don't change them, they
match your EVOLV brand and the React platform's actual UI:

```
Brand colors:
  --bg-base:    #0a0e1a   (very dark navy, primary background)
  --bg-surface: #131826   (one shade up — cards/panels)
  --text:       #ffffff   (primary text)
  --text-muted: #7a8fa3   (secondary text, WCAG AA on bg-base)
  --evolv-blue: #007FFF   (primary accent)
  --evolv-lime: #32CD32   (success / passed)
  --warn-amber: #f59e0b   (warning / blocked)
  --error-red:  #ef4444   (failure / hard block)
  --adhoc-purple: #a855f7 (tester adhoc, manual authoring)

Typography: Inter or system-ui, font-feature-settings: "ss01"
Animation: cubic-bezier(0.16, 1, 0.3, 1) easing, 300–600ms
Border radius: 8px on cards, 4px on chips
```

---

# Prompt 1 — Coverage Gap Detector (Sprint 15.3)

**Use this for:** the Week 1 LinkedIn post (highest emotional pull)

**Animation concept:** A row of 8 UR cards. One by one they get
green ✓ test-bundle badges. Card #5 stays empty. A red banner
slides down from the top: "🛑 Design phase blocked — UR-5 has no
test coverage." Loop.

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode. Background #0a0e1a. Square canvas, 1080x1080,
centered in viewport.

Use the EVOLV brand language:
  --bg-base: #0a0e1a
  --bg-surface: #131826
  --text: #ffffff
  --text-muted: #7a8fa3
  --evolv-blue: #007FFF
  --evolv-lime: #32CD32
  --error-red: #ef4444

Font: 'Inter', system-ui. Border radius 8px on cards.

Scene (12-second loop):
1. (0.0–0.5s) Title fades in at top: "Coverage Gap Detector" in
   white, 24px semibold. Subtitle in #7a8fa3, 14px: "Hard-blocks
   Design phase if any GxP-Direct UR is uncovered."
2. (0.5–1.0s) A horizontal row of 8 cards fades in below the
   title. Each card is 110x90px, #131826 background, 1px border
   #2a3142, label "UR-1" through "UR-8" in mono font, 12px.
   Below each label, in 9px uppercase muted text: "GxP Direct".
3. (1.0–4.5s) Sequentially (every 400ms), each card flips to
   show a #32CD32 lime check-circle icon and the text "✓ Bundle
   ready" in lime, 10px. EXCEPT card #5 — it stays empty and
   the border pulses red (#ef4444) starting at 3.5s.
4. (4.5–5.0s) A red banner slides DOWN from the top of the
   canvas: full-width, height 56px, background rgba(239,68,68,
   0.12), border-bottom 1px #ef4444. Text in #ef4444, 14px
   semibold: "🛑 Design phase blocked — UR-5 has no test coverage"
5. (5.0–7.0s) A pill button appears next to the banner text:
   "⚡ Generate for UR-5" in white text on rgba(168,85,247,0.85)
   background, padding 6px 14px, radius 6px, 11px semibold.
   The button gently pulses (scale 1.0 → 1.03 → 1.0, 1.5s loop).
6. (7.0–10.0s) Hold the full state. Add a thin "EVOLV" wordmark
   at the bottom in #007FFF, 12px semibold tracking 0.1em.
7. (10.0–12.0s) Cross-fade everything to 50% opacity then back
   to start state. Loop forever.

Use CSS keyframes for sequencing. No JavaScript needed unless
useful for the loop reset. Make it crisp on retina displays.
Keep all text inside a 80px safe-area margin from the canvas
edges (LinkedIn crops aggressively).
```

---

# Prompt 2 — Pre-Lock QA Review (Sprint 15.4)

**Use this for:** the Week 2 LinkedIn post

**Animation concept:** A test script with mixed Pass/Fail/Blocked
verdicts. Failed + blocked + adhoc rows magnetically slide RIGHT
into a focused review panel. The 4-point checklist auto-ticks.
Two signature stamps appear side by side.

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
1. (0.0–0.5s) Title at top: "Pre-Lock QA Review" white, 24px
   semibold. Subtitle muted 14px: "21 CFR Part 11 §11.10(b) —
   independent record review."
2. (0.5–2.0s) Below title, a vertical list of 6 test step rows
   fades in (each 700px wide, 56px tall, #131826 background,
   1px #2a3142 border, radius 6px). Layout per row:
     [step number mono] [step title 14px] [verdict chip on right]
   Verdict chips:
     row 1 = PASS (lime)
     row 2 = PASS (lime)
     row 3 = FAIL (red, #ef4444 bg-tint, red text)
     row 4 = PASS (lime)
     row 5 = BLOCKED (amber)
     row 6 = ADHOC (purple chip with ⚡ icon, no verdict yet)
3. (2.0–4.0s) Rows 3, 5, and 6 magnetically slide RIGHT and
   stack into a "QA Review" panel that materialises on the
   right half of the canvas (panel is #131826, 420px wide,
   border 1px #2a3142, header text "Items requiring review (3)"
   in #7a8fa3 10px uppercase).
4. (4.0–6.5s) Below the panel, a 4-point checklist fades in.
   Each item: small empty checkbox + 11px text. Items:
     [ ] Failed steps have actual results recorded
     [ ] Defects logged for failures
     [ ] Evidence attached
     [ ] Adhoc steps justified
   Sequentially (every 350ms), each checkbox auto-ticks with a
   lime check and a tiny "(auto-OK)" tag in lime, 9px.
5. (6.5–8.5s) Two signature stamps appear side by side at the
   bottom, 200px wide each, #0a0e1a background, 1px lime border,
   radius 6px:
     LEFT stamp: "✓ Executor signed" / "Jane Smith" / timestamp
     RIGHT stamp: "✓ QA reviewed" / "Mark Patel" / timestamp
   Both have a subtle lime glow.
6. (8.5–10.5s) A muted caption fades in below: "Two signatures.
   One audit trail. Independent review per Part 11 §11.10(b)."
   Text in #7a8fa3, 12px italic.
7. (10.5–12.0s) Cross-fade to start. Loop.

Use CSS transforms (translateX, opacity, scale) for performance.
Stay inside an 80px safe-area margin from canvas edges.
Add the "EVOLV" wordmark in #007FFF 12px semibold at the very
bottom centre.
```

---

# Prompt 3 — Adhoc Step Insertion (Sprint 15.2)

**Use this for:** the Week 3 LinkedIn post

**Animation concept:** A live test execution table. Cursor hovers
between row 3 and row 4. A dashed "+ Insert adhoc step here"
button appears. New row 3.1 slides in with a purple ⚡ Adhoc badge.
Audit-log toast pops up: "Reason captured. Source: tester-adhoc."

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode, EVOLV brand language. Background #0a0e1a.
Square canvas, 1080x1080.

Brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --adhoc-purple: #a855f7
  --text-muted: #7a8fa3    --error-red: #ef4444
                           --warn-amber: #f59e0b

Font: 'Inter', system-ui. Mono font: 'JetBrains Mono' fallback
to ui-monospace. Border radius 6px on cards / 4px on chips.

Scene (12-second loop):
1. (0.0–0.5s) Title: "Adhoc Step Insertion" white 24px semibold.
   Subtitle muted 14px: "Tester-in-the-loop, fully auditable."
2. (0.5–1.5s) Below title, a test step table appears. Header
   row in 9px uppercase muted text: # | TITLE | EXPECTED |
   VERDICT. Then 4 rows of test steps, each 60px tall, alternating
   subtle row tints. Step numbers in mono: 1, 2, 3, 4. Each step
   has a "PASS" chip in lime on the right. Use placeholder titles
   like "Login as System Owner", "Navigate to Batch Records",
   "Verify temp range alarm at 8°C", "Confirm audit-trail entry".
3. (2.0–3.0s) An animated cursor (white triangle, 14px) slides
   in from the right and hovers in the gap BETWEEN row 3 and
   row 4. As it hovers, a thin dashed purple button appears
   spanning the full row width: "+ Insert adhoc step here" in
   #a855f7, 11px, dashed border 1px #a855f7 with 30% opacity.
4. (3.0–3.5s) Cursor clicks (small ripple effect). The dashed
   button expands into an inline form panel (height 140px,
   #131826 bg, 1px purple border) showing labelled fields:
     "Step Title *" with placeholder "Verify password lockout"
     "Reason for Adhoc Insert *" (mandatory hint in amber)
   Fields auto-fill via a typewriter effect (one char per 25ms).
5. (5.5–6.0s) An "Insert Step" button at the form's bottom-right
   pulses purple, then "clicks" (ripple). The form collapses.
6. (6.0–7.0s) A new row slides in BETWEEN row 3 and row 4 with
   step number "3.1" (mono, slightly indented). Title: "Verify
   password lockout after 5 failures". Right side has TWO chips:
     "EXECUTION" (blue tint)
     "⚡ ADHOC" (purple bg rgba(168,85,247,0.15), purple text)
   The new row has a faint left border in purple to mark it.
7. (7.0–9.0s) A toast notification slides in from top-right
   (260px wide, dark, with a small lime check icon). Text:
     line 1 (white 11px): "Audit entry captured"
     line 2 (muted 10px): "source: tester-adhoc · reason saved"
8. (9.0–11.0s) Hold the full state. Toast fades after 1s but
   the new row pulses gently (border-color 1.5s ease).
9. (11.0–12.0s) Cross-fade to start. Loop.

Use CSS transforms only (no layout-thrashing properties). Stay
inside 80px safe-area margins. Add "EVOLV" wordmark in #007FFF
12px semibold at very bottom centre.
```

---

# Prompt 4 — Manual Authoring (Sprint 15.1)

**Use this for:** the Week 4 LinkedIn post (series wrap)

**Animation concept:** A toggle flips between "AI Generate" and
"Author Manually." A blank canvas appears. Steps type themselves
out one by one. Citation chips fly in and dock to each step. A
quality-score gauge climbs from 0/5 to 5/5.

### Paste this into claude.ai

```
Build me a self-contained HTML/CSS/JS animation as an Artifact for a
LinkedIn marketing video. Single file, no external dependencies.

Theme: dark mode, EVOLV brand language. Background #0a0e1a.
Square canvas, 1080x1080.

Brand tokens:
  --bg-base: #0a0e1a       --evolv-blue: #007FFF
  --bg-surface: #131826    --evolv-lime: #32CD32
  --text: #ffffff          --adhoc-purple: #a855f7
  --text-muted: #7a8fa3    --warn-amber: #f59e0b

Font: 'Inter', system-ui. Border radius 8px on cards / 4px on chips.

Scene (12-second loop):
1. (0.0–0.5s) Title: "Manual Authoring" white 24px semibold.
   Subtitle muted 14px: "AI is optional. The audit trail is not."
2. (0.5–1.5s) A segmented toggle appears centred at the top.
   Two segments, each 140x36px:
     LEFT: "🤖 AI Generate" (blue tint, currently selected)
     RIGHT: "✍ Author Manually" (transparent)
   At 1.0s, the selection slides RIGHT to "Author Manually"
   (smooth 400ms ease). Right segment now has purple bg
   rgba(168,85,247,0.15), purple text, purple 1px border.
3. (1.5–2.0s) Below the toggle, an empty bundle card materialises
   (560px wide, 380px tall, #131826 bg, 1px #2a3142 border,
   radius 8px). Header "Bundle: TB-UR-7" in mono 11px muted.
4. (2.0–6.0s) Three step rows appear inside the card,
   sequentially, with a typewriter effect on the title field:
     Step 1 (Setup): "Establish test environment" — types at
       30ms/char, then 2 amber citation chips fly in from the
       right edge and dock under the row text:
         [21 CFR §11.10] [GAMP 5 §M3]
     Step 2 (Execution, Positive): "Verify temperature alarm at
       upper limit" — types in, then 2 chips dock:
         [EU Annex 11 §9] [21 CFR §11.10(e)]
     Step 3 (Execution, Negative): "Confirm rejection on out-of-
       range value" — types in, 2 chips dock:
         [ICH Q9] [GAMP 5 §M3]
   Each chip is small (auto-width, 9px text, padded 4px 8px,
   amber-tinted bg rgba(245,158,11,0.12), amber text #f59e0b,
   1px amber border at 30% opacity).
5. (6.0–8.5s) On the right side of the canvas (outside the
   bundle card, in a small panel 220px wide), a "Quality Score"
   gauge appears. Five circular pips arranged horizontally,
   each 18px diameter, initially empty (1px #2a3142 border).
   Below the pips, label "0 / 5" in 10px muted text. Sequentially
   (every 250ms), each pip fills with lime #32CD32 and the
   counter increments: 1/5, 2/5, 3/5, 4/5, 5/5. At 5/5, the
   counter switches to "✓ All checks pass" in lime 11px bold.
6. (8.5–10.5s) A footer caption fades in below the bundle card,
   muted italic 12px: "Same citations. Same quality checks.
   Same audit trail. Zero AI in the loop."
7. (10.5–12.0s) Cross-fade to start state. Loop.

Use CSS animations + a tiny bit of JS for the typewriter effect
(use a class that adds chars on a setInterval). All other motion
should be CSS keyframes. Stay inside 80px safe-area margins. Add
"EVOLV" wordmark in #007FFF 12px semibold at very bottom centre.
```

---

## 🎬 Pro Tips (so the animations actually convert)

### Visual hierarchy
1. **First 2 seconds = the hook.** LinkedIn auto-plays muted —
   if your animation isn't visually compelling in 2s, the viewer
   keeps scrolling. Front-load the title and the first beat.
2. **Use motion to direct the eye.** Each animation has ONE focal
   moment (the red banner / the ticking checklist / the new row /
   the climbing gauge). Don't dilute it.
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
  - **Coverage:** "Hard-block. No GxP-Direct UR ships untested."
  - **QA Review:** "Two signatures. One audit trail."
  - **Adhoc:** "Tester adds. Audit captures. Inspector trusts."
  - **Manual:** "AI optional. Compliance mandatory."

### File preparation
1. Record at 1080×1080 @ 30fps in your screen recorder
2. Trim to exactly the loop length (12s)
3. Export as MP4 (H.264, ~3 Mbps bitrate — keeps file under 5 MB)
4. Test the loop on your phone before posting (LinkedIn previews
   poorly on desktop)

### Iteration trick
After Claude generates the first Artifact, ask follow-ups in
plain English:
- "Slow the typewriter to 50ms per character."
- "Make the red banner shake once when it appears."
- "Replace the first row title with [your real text]."
- "Add a subtle drop-shadow under the bundle card."

Each tweak takes ~10 seconds and you keep the same Artifact open.

---

## 🚀 Bonus — One Animation to Rule Them All

If you want a SINGLE 30-second hero video that strings all four
sprint features together (use this as your pinned LinkedIn post,
YouTube channel trailer, or Sprint 15 wrap post), paste this
prompt:

```
Build a self-contained HTML/CSS/JS Artifact: a 30-second looping
animation that walks through 4 EVOLV features in sequence. Dark
mode (#0a0e1a), 1080x1080 square, EVOLV brand language.

Beats:
  0–7s:  "Coverage Gap Detector" — 8 UR cards, one stays empty,
         red hard-block banner slides down
  7–14s: "Pre-Lock QA Review" — failed/blocked/adhoc rows magnetise
         into a review panel, 4-checks auto-tick, dual signature
  14–21s: "Adhoc Step Insertion" — cursor hovers, dashed insert
          button appears, new row 3.1 slides in with ⚡ Adhoc badge
  21–28s: "Manual Authoring" — toggle flips to manual, 3 steps
          type themselves, citations dock, quality score climbs 0→5
  28–30s: Final hold — all 4 feature names tile into a 2×2 grid
          with the title "Sprint 15 — Tester-in-the-Loop +
          Coverage Confidence" and the EVOLV wordmark

Use the EVOLV brand tokens already defined. Each beat should have
a smooth cross-fade transition (400ms) into the next. Stay inside
80px safe-area margins. Loop seamlessly.
```

Use this as your Sprint 15 wrap post in Week 5 — it's the highest-
leverage piece of content from this whole series.
