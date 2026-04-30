# EVOLV Brand Kit — Social & Marketing

**Single source of truth for every LinkedIn post, YouTube video, animation, demo screenshot, and pitch deck.**

If you're about to make a marketing asset and you didn't open this file first, stop and open it.

---

## 1. The Positioning Sentence

> **EVOLV is the AI-era validation factory for pharma — built by a 2-decade CSV practitioner who got tired of waiting for legacy vendors to catch up.**

Use this (or a trimmed version) as the bio line on LinkedIn, the first line of every YouTube description, and the close of every cold DM.

**Tone rules:**
- Speak like a practitioner, not a vendor. ("We built this because…" not "Our platform empowers…")
- Specific over generic. ("21 CFR Part 11 §11.10(b)" beats "compliance-ready".)
- Show the receipt. (Sprint number, regulation citation, screenshot — never just claims.)
- No emojis in body copy. Reserved for status badges in the product (⚡ Adhoc, 🛡 QA Review).

---

## 2. Typography (locked)

| Role | Font | Where | Why |
|------|------|-------|-----|
| **Headers / hero** | **Space Grotesk** (700, 600) | LinkedIn post titles, video lower-thirds, slide headers | Distinctive without being weird — the slight quirk in the 'a' and 'g' makes it memorable in a feed dominated by Inter |
| **Body / captions** | **Inter** (400, 500, 600) | Post body, descriptions, slide bullets, caption tracks | Universally readable, no regulator will squint |
| **Data / IDs / timestamps** | **JetBrains Mono** (500) | URS IDs, RPN scores, citations, code blocks, audit timestamps | Signals "this is real evidence" — leans into the data-confident voice |

All three are free on Google Fonts. Embed link:
```
https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap
```

**Type scale (use only these sizes):**
- Hero: 56px / Space Grotesk 700 / -0.02em letter-spacing
- Title: 32px / Space Grotesk 600 / -0.01em
- Subtitle: 20px / Inter 500
- Body: 16px / Inter 400 / 1.6 line-height
- Caption: 13px / Inter 500 / uppercase / 0.08em letter-spacing
- Mono / data: 14px / JetBrains Mono 500

---

## 3. Color Palette (locked — same as product)

The product ships **two themes**. As of Sprint 16 (April 2026) **light is the new default** — pharma QA pros said the dark UI was hard on their eyes during long audit sessions, and most validation legacy tools they grew up with are light. Both palettes are first-class. Use the one that matches the asset's context:

- **Light palette** — product screenshots, demo videos, walkthroughs, customer-facing decks
- **Dark palette** — hero animations, "tech-forward" feel posts, founder reels, stylized assets
- **Accent palette** — same hex in both themes; never recolor these per theme

### 3a. Light palette (product default, Sprint 16+)

| Token | Hex | Use |
|-------|-----|-----|
| `--bg-base` | `#ffffff` | Main background |
| `--bg-surface` | `#f9fafb` | Cards, panels |
| `--bg-card` | `#f1f5f9` | Sticky headers, raised cards |
| `--bg-hover` | `#e5e7eb` | Hover states |
| `--text-primary` | `#0f172a` | Body copy on light (16:1 on white) |
| `--text-secondary` | `#334155` | Secondary headers (12.6:1) |
| `--text-muted` | `#64748b` | Captions, hint text (4.6:1 — passes AA) |
| `--border-base` | `#e2e8f0` | Hairlines, dividers |
| `--border-bright` | `#cbd5e1` | Active card border, focus ring |

### 3b. Dark palette (legacy default, kept for stylized assets)

| Token | Hex | Use |
|-------|-----|-----|
| `--bg-base` | `#07070f` | Main background, video backdrops |
| `--bg-surface` | `#0d0d1c` | Cards, panels, hero zones |
| `--bg-card` | `#111124` | Hover states, sticky headers |
| `--bg-hover` | `#17172e` | Active row hover |
| `--text-primary` | `#e2e8f0` | Body copy on dark |
| `--text-secondary` | `#b0bec8` | Secondary headers |
| `--text-muted` | `#7a8fa3` | Captions (WCAG AA against `--bg-base`) |
| `--border-base` | `#1c1c38` | Hairlines |
| `--border-bright` | `#28284a` | Active card border |

### 3c. Brand-locked accents (same in both themes)

| Token | Hex | Use |
|-------|-----|-----|
| `--evolv-blue` | `#007FFF` | Primary CTA, brand accent, link color |
| `--evolv-lime` | `#32CD32` | Success, "covered", positive metrics |
| `--evolv-blue-soft` | `rgba(0,127,255,0.12)` | Backgrounds for blue chips |
| `--evolv-lime-soft` | `rgba(50,205,50,0.12)` | Backgrounds for green chips |
| `--error-red` | `#ef4444` | Failures, blockers, gap alerts |
| `--warn-amber` | `#f59e0b` | Warnings, partial coverage |
| `--adhoc-purple` | `#a855f7` | Tester adhoc badge, exploratory accents |

**Contrast caveats on light backgrounds:**
- `#007FFF` on `#ffffff` is 3.85:1 — passes AA for **graphical UI / large text** (3:1) but **fails body-text AA** (4.5:1). Use it for badges, chip borders, button backgrounds — never for inline link text in body copy. For inline emphasis on a light surface, use `--text-primary` bold.
- `#32CD32` on `#ffffff` is 1.9:1. Use only as a chip-fill or icon stroke alongside text in `--text-primary` — never as text color on light.
- `#a855f7` on `#ffffff` is 4.65:1 — passes AA. Safe for inline emphasis and link text.

**Gradient (use sparingly — hero zones only):**
```
linear-gradient(135deg, #007FFF 0%, #32CD32 100%)
```
Maximum 1 gradient per asset. Never use it on text smaller than 32px (illegible at small sizes). Works on both light and dark backdrops.

---

## 4. Logo & Wordmark

**Wordmark:** `EVOLV` set in Space Grotesk 700, all caps, letter-spacing `0.04em`. Color: `--text-primary` on dark, `--bg-base` on light.

**Lockup (when space allows):**
```
EVOLV
THE VALIDATION FACTORY
```
- Line 1: Space Grotesk 700, 24px, `--text-primary`
- Line 2: Inter 500, 11px, `--text-muted`, uppercase, letter-spacing `0.12em`

**Minimum clear space:** 1× the cap-height of "E" on all four sides. Never put another logo or text inside that zone.

**Don't:**
- Don't use a graphical logo mark (we don't have one — type-only is the brand). If you need an icon, use a single solid square in `--evolv-blue` next to the wordmark.
- Don't apply gradient or shadow to the wordmark.
- Don't italicize, condense, or recolor letter-by-letter.

---

## 5. Social Templates

### 5a. LinkedIn Feed Post (1080×1080 square)

```
┌────────────────────────────────────────┐
│ EVOLV ◾ Sprint 15.3                    │  ← Header strip (64px tall)
│                                        │     bg: --bg-elevated
├────────────────────────────────────────┤
│                                        │
│                                        │
│         [ ANIMATION / CONTENT ]        │  ← Demo zone (880px tall)
│                                        │     bg: --bg-surface
│                                        │     16px corner radius
│                                        │
├────────────────────────────────────────┤
│ The Validation Factory ◾ evolv.app     │  ← Footer strip (64px tall)
└────────────────────────────────────────┘
```

- Header: wordmark + tag chip (sprint or feature name) in `--evolv-blue` chip
- Footer: tagline left, domain right (when domain exists; for now use "evolv.app — coming May 2026")
- All padding: 24px from edges
- Use this template for every static post AND as the wrapper around every animation

### 5b. LinkedIn Native Video (1920×1080 landscape)

Same header/footer strips (now 80px tall). Demo zone is 1920×920. Add a **lower-third caption strip** between demo and footer for muted viewers (85% of LinkedIn watches with sound off):

```
┌──────────────────────────────────────────────┐
│  CAPTION TEXT — 32px Inter 600              │  bg: --bg-base 70% opacity
│  Speaker name or feature name — 16px        │  positioned 120px from bottom
└──────────────────────────────────────────────┘
```

### 5c. YouTube Thumbnail (1280×720)

- Background: `--bg-surface`
- Top 60%: large hero text (48–72px Space Grotesk 700) — pose a question or state the pain
- Bottom 40%: screenshot of the actual feature (not a stock image, not a stretched LinkedIn post)
- Top-right corner: EVOLV wordmark (32px)
- Bottom-right corner: sprint tag chip in `--evolv-blue`
- Color rule: text and screenshot must hit 4.5:1 contrast. Test in grayscale.

### 5d. Slide / Pitch Deck (1920×1080)

- Always-visible top bar: EVOLV wordmark left, slide number + total right (e.g. `12 / 24`)
- Title zone: 1920×240 with `--evolv-blue` accent line under title (4px)
- Body zone: 1920×720
- Footer: hairline `--border-subtle` divider, slide topic name in 14px Inter 500 mono

---

## 6. Caption & Subtitle Style

For LinkedIn videos and YouTube uploads, burn captions into the video AND upload an .srt file. Style:

- Font: Inter 600
- Size: 32px (LinkedIn), 36px (YouTube)
- Color: `--text-primary` (#e7ebf3)
- Background: `--bg-base` at 70% opacity, 8px corner radius, 12px padding
- Position: bottom-center, 120px from frame bottom (clears the LinkedIn UI overlay)
- One line at a time, max 7 words per line
- Sentence case, never ALL CAPS

---

## 7. Hashtag System (consistency = algorithm love)

**Always include 3–5 from the core set, optionally 2–3 from rotating:**

**Core (every post):**
`#PharmaTech` `#CSV` `#GAMP5` `#FDACompliance` `#ValidationFactory`

**Rotating (pick 2–3 by topic):**
- Compliance angle: `#21CFRPart11` `#EUAnnex11` `#DataIntegrity` `#ALCOA`
- AI angle: `#AIinPharma` `#PharmaInnovation` `#GxP` `#CSA`
- Audience angle: `#QualityAssurance` `#BiotechStartups` `#PharmaQuality` `#RegulatoryAffairs`
- Founder angle: `#BuildInPublic` `#FounderJourney` `#PharmaFounder`

**Never use:** `#Validation` (too generic, hijacked by data-validation devs), `#Pharma` (saturated), generic `#AI` or `#Tech`.

---

## 8. Voice — Three Tone Levels

| Context | Voice | Example |
|---------|-------|---------|
| **LinkedIn post body** | Practitioner peer — confident, specific, slightly self-deprecating | "I've sat through this audit finding three times. Built the fix this sprint." |
| **YouTube video script** | Founder explainer — slower, walks through the why | "Most validation tools stop at script execution. The auditor doesn't. So we built…" |
| **Product UI / docs** | Calm, regulatory-precise, no humor | "Pre-lock QA review per 21 CFR Part 11 §11.10(b). Independent reviewer attestation required before signature." |

Never mix. A LinkedIn post should never sound like docs. Docs should never sound chatty.

---

## 9. Asset Naming Convention

Save every social asset to `marketing/assets/` using this pattern:

```
{date}_{channel}_{sprint}_{feature-slug}_{type}.{ext}

Examples:
20260429_li_s15.3_coverage-gap_animation.mp4
20260429_li_s15.3_coverage-gap_post.png
20260429_yt_s15.3_coverage-gap_thumbnail.png
20260429_yt_s15.3_coverage-gap_video.mp4
```

Date = the date you publish it. This way `ls marketing/assets/ | sort` gives you publication chronology.

---

## 10. Pre-Publish Checklist (paste into every post draft)

- [ ] Wordmark is Space Grotesk 700, all caps, correct color
- [ ] Brand colors match this kit (no off-by-one hex from a screenshot)
- [ ] Theme matches the asset's context (light for product screenshots, dark for stylized hero reels)
- [ ] Hero text is Space Grotesk; body is Inter; data is JetBrains Mono
- [ ] At least one specific receipt (sprint, regulation, screenshot, metric)
- [ ] Hashtags pulled from the locked sets (3–5 core + 2–3 rotating)
- [ ] Video has burned-in captions AND uploaded .srt
- [ ] Animation loops cleanly (last frame matches first frame)
- [ ] Asset filename follows the convention
- [ ] Founder narrative line included (or implied via context)
- [ ] No emojis in body copy

If any box is unchecked, don't publish.
