# Sprint 17 — Requirements Module Overhaul

**Status:** Active (started 2026-04-29)
**Theme:** Make the Requirements tab the strongest tab in the platform — what closes pilot conversations.

## Schema contract (vendor-agnostic — no person, company, or publication
named anywhere in product code or UI)

The two authoring flows in demo feedback map onto an industry-standard
practitioner playbook for GxP requirements. We adopt these structural ideas
as the schema contract — without crediting any specific author, firm, or
journal so the platform stays neutral for any pharma customer:

1. **The 3 Cs** — every requirement = **Capability** + **Condition** + **Constraint** (Constraint optional)
2. **Functional vs Non-Functional** as a first-class enum
3. **7 stakeholders** — Senior Mgmt, Lab, IT, QA/ITQA, Procurement, Supplier, **Data Owner** (added by us)
4. **Bad-pattern detection** — weasel words, >25 words, "and/or", "system shall be 21 CFR Part 11 compliant" (regulation-copying)
5. **AI's defined lane** — generic draft for review and update by humans; never replace lab-process minutiae

## Sub-tickets (priority order)

### 17.1 — Visual harmonization (in progress)
Replace the iframe-tab pattern in `Requirements.jsx` with a React-native shell
that matches `Risk.jsx`'s **wide-table layout** (not Plan.jsx's narrow form
layout). The "feels separate" pain is that Streamlit's centered narrow
content was bleeding through the iframe.

Acceptance: layout, typography, padding, and chrome match Risk.jsx. Iframe
preserved as a "↗ Open legacy Streamlit" link for now.

### 17.2 — 3 Cs as the requirement schema
Restructure the per-requirement editor row from one textarea to three fields
(Capability / Condition / Constraint). Backward compatible — concat into the
existing `Requirement_Statement` for downstream consumers (PDF, Word, agents).

Store change: `requirements[i].user_requirement` gains `capability`, `condition`,
`constraint` fields. Existing `statement` becomes a derived field.

### 17.3 — Functional / Non-Functional toggle + Stakeholder tag
Two enum dropdowns per requirement row.
- `requirement_type`: Functional | Non-Functional
- `stakeholder`: Senior Mgmt | Lab | IT | QA/ITQA | Procurement | Supplier | Data Owner

Drives section-grouping in the export.

### 17.4 — Workshop-driven flow (Flow A)
Top-of-page form with the existing `transform_urs_to_ur_fr(additional_context=…)` plumbing:
- System Description (textarea)
- Workshop Notes (textarea)
- Lucid Diagram URL (input) + file upload
- Workflow Process Description (textarea)

Submit → backend generates first-draft URs/FRs populated into the 3 Cs editor below.
User reviews, edits, accepts.

### 17.5 — Manual flow + AI sidekick (Flow B)
Right-rail "AI Assistant" panel that critiques the row in focus. Calls SMART
engine + a new ruleset. Inline chips:
- ⚠ Vague (weasel words: "fast", "easy", "user-friendly", "robust", "modest")
- ⚠ Untestable (no condition / no measurable parameter)
- ⚠ Reg-copy ("system shall be 21 CFR Part 11 compliant")
- ⚠ Too long (>25 words)
- ⚠ "and/or" detected
- ⚠ Missing constraint (regulation cited but no constraint field)

**Decision (user 2026-04-29):** Sidekick is **advisory** (chips + counts),
never a hard gate. Save remains available with a one-line override
justification.

### 17.6 — Mode toggle
Single tab, two modes: "Generate from workshop" / "Write manually". Flow A's form
collapses when in manual mode; Flow B's side panel shows in both.

## Decisions locked

| Question | Answer |
|---|---|
| 17.1 first or 17.2 first? | 17.1 first (cheap visual win) |
| Sidekick advisory or hard gate? | **Advisory** — chips + counts, override allowed |
| 3 Cs backward-compatible? | **Yes** — concat to old `Requirement_Statement` for exports |
| Stakeholder count | **7** (six common GxP roles + Data Owner) |

## What we deliberately NOT build in Sprint 17

- Two-version requirements lifecycle (v1 generic / v2 system-specific / v3 corrections) — separate sprint
- 8-section templated export with reusable IT section — belongs in PDF generator sprint
- User-stories format — explicitly out of scope; the 3 Cs is the chosen schema
- Replacing the SMART engine — wire to the existing one
- Replacing `requirement_architect.py` — its `additional_context` plumbing is exactly what Flow A needs

## Implementation map

| New code | Modifies / Wires To |
|---|---|
| `react-platform/src/apps/Requirements.jsx` (rewrite) | Risk.jsx layout pattern, `requirements` store slice |
| `react-platform/src/apps/requirements/WorkshopIntake.jsx` (17.4) | calls `/requirements/generate` (existing) with `additional_context` |
| `react-platform/src/apps/requirements/RequirementRow.jsx` (17.2/17.3) | 3-field editor + 2 dropdowns |
| `react-platform/src/apps/requirements/AISidekick.jsx` (17.5) | calls SMART engine + new bad-pattern detector |
| `Agents/smart_requirements_engine.py` (17.5) | extend `_apply_vague_substitutions` with weasel-word + reg-copy + length detectors |
| `react-platform/src/store/useAppStore.js` | add `capability`, `condition`, `constraint`, `requirement_type`, `stakeholder` fields per requirement |
