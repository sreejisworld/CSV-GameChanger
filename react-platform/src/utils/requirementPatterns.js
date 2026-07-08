/**
 * requirementPatterns.js — Sprint 17.5 AI Sidekick detector.
 *
 * Pure JavaScript — no React, no network, no LLM. Six deterministic
 * pattern detectors that flag bad-smell URs/FRs in real time so the
 * author can rewrite before the requirement gets locked into the
 * Risk / Design / Verify pipeline downstream.
 *
 * Detectors:
 *   1. vague               — weasel words / unmeasurable adjectives
 *   2. untestable          — vague verbs OR Functional w/o trigger
 *   3. reg-copy            — regulation citation w/o a system action
 *   4. too-long            — > 25 words → likely 2+ FRs in one row
 *   5. and-or              — "and/or" or 2+ " and " conjunctions
 *   6. missing-constraint  — Non-Functional w/o measurable threshold
 *
 * Severity:
 *   high   — red    — likely audit finding (reg-copy, untestable verb)
 *   warn   — amber  — refactor recommended (too-long, and-or)
 *   info   — blue   — nice-to-have polish (vague, NF-no-threshold)
 *
 * Each detector returns at most one finding per requirement (the most
 * severe match wins inside the detector). The aggregate
 * `analyzeRequirement(req, meta)` returns an array of zero-to-six
 * findings with stable shape:
 *
 *   { id, severity, label, hint, matches? }
 *
 * Advisory only — never gates phase completion or save (per sprint
 * plan: "advisory chips, never a hard gate").
 */

// ── Word lists ────────────────────────────────────────────────────────
const VAGUE_WORDS = [
  'appropriate', 'as needed', 'user-friendly', 'user friendly',
  'fast', 'quick', 'easy', 'simple', 'robust', 'efficient',
  'flexible', 'intuitive', 'modern', 'state-of-the-art',
  'best-in-class', 'world-class', 'best effort', 'best-effort',
  'as soon as possible', 'asap', 'good enough', 'if applicable',
  'when feasible', 'to be defined', 'tbd', 'high quality',
  'high performance', 'minimum impact', 'reasonable', 'sufficient',
  'optimal', 'seamless', 'scalable', 'reliable', 'secure',
  'standard',
]

const VAGUE_VERBS = [
  'support', 'handle', 'manage', 'deal with', 'facilitate',
  'enable user to', 'provide capability', 'leverage', 'utilize',
  'address', 'cover', 'incorporate', 'consider',
]

const REG_CITATION_RE = new RegExp(
    '\\b('
  + '21\\s*c\\.?\\s*f\\.?\\s*r\\.?\\s*(?:part\\s*\\d+|§\\s*\\d+)?'
  + '|annex\\s*11'
  + '|gamp\\s*\\d?'
  + '|ich\\s*q\\d+'
  + '|iso\\s*\\d+'
  + '|hipaa'
  + '|gdpr'
  + '|fda\\s*(?:cfr|guidance|guide)?'
  + '|ema'
  + '|csa'
  + ')\\b',
  'i',
)

const REG_TOKEN_SET = new Set([
  'cfr', 'annex', 'gamp', 'ich', 'iso', 'fda', 'gdpr', 'hipaa', 'ema',
  '11', '21', 'part', 'csa',
])


// ── Helpers ───────────────────────────────────────────────────────────
function _wordCount(text) {
  return (text || '').trim().split(/\s+/).filter(Boolean).length
}

function _padded(text) {
  return ' ' + (text || '').toLowerCase().replace(/\s+/g, ' ').trim() + ' '
}

function _containsPhrase(padded, phrase) {
  const p = ' ' + phrase.toLowerCase() + ' '
  if (padded.includes(p)) return true
  // Allow trailing punctuation: "fast." / "fast,"
  return padded.includes(' ' + phrase.toLowerCase() + '.')
      || padded.includes(' ' + phrase.toLowerCase() + ',')
}


// ── Detector: vague / weasel words ────────────────────────────────────
function detectVague(text) {
  if (!text) return null
  const padded = _padded(text)
  const hits = VAGUE_WORDS.filter(w => _containsPhrase(padded, w))
  if (!hits.length) return null
  const preview = hits.slice(0, 2).join(', ')
      + (hits.length > 2 ? `, +${hits.length - 2}` : '')
  return {
    id: 'vague',
    severity: 'info',
    label: `Vague: ${preview}`,
    hint:
      'Replace weasel words with measurable outcomes — e.g. "within 30 s", '
      + '"≤ 5 % rejection rate", "uptime ≥ 99.5 %".',
    matches: hits,
  }
}


// ── Detector: untestable ──────────────────────────────────────────────
function detectUntestable({ text, meta, type, reqType }) {
  // Non-Functional has its own no-threshold check below.
  if (reqType === 'Non-Functional') return null

  const padded = _padded(text)
  for (const v of VAGUE_VERBS) {
    if (_containsPhrase(padded, v)
        || padded.startsWith(' ' + v + ' ')
        || padded.startsWith(' shall ' + v + ' ')) {
      return {
        id: 'untestable',
        severity: 'high',
        label: `Untestable verb "${v}"`,
        hint:
          'Replace with concrete observable verbs: log, record, block, '
          + 'alert, approve, validate, generate, encrypt, lock, expire, '
          + 'notify, capture.',
        matches: [v],
      }
    }
  }

  // Functional UR with capability filled but no condition AND no
  // constraint — no testable trigger means the FR has nothing to assert.
  const cap  = (meta?.capability ?? '').trim()
  const cond = (meta?.condition  ?? '').trim()
  const cons = (meta?.constraint ?? '').trim()
  if (type === 'UR' && cap && !cond && !cons) {
    return {
      id: 'untestable',
      severity: 'info',
      label: 'No testable trigger',
      hint:
        'Add a Condition cell (when / under what trigger) so the child '
        + 'FRs have an observable event to assert against.',
    }
  }
  return null
}


// ── Detector: reg-copy ────────────────────────────────────────────────
function detectRegCopy(text) {
  if (!text || !REG_CITATION_RE.test(text)) return null

  // Strongest signal: "shall be compliant" / "shall comply with"
  if (/\bshall\s+(be|become|remain)\s+(compliant|in compliance)\b/i.test(text)
      || /\bshall\s+comply\s+with\b/i.test(text)) {
    return {
      id: 'reg-copy',
      severity: 'high',
      label: 'Reg-copy',
      hint:
        'A regulation citation is not a requirement. State the system '
        + 'action that satisfies it — e.g. "log every access event with '
        + 'user ID, timestamp, and reason" — and put the regulation in '
        + 'the Constraint cell.',
    }
  }

  // Short statements that are mostly regulation tokens (e.g.
  // "21 CFR Part 11 audit trail").
  const words = (text.match(/\b[\w-]+\b/g) || []).filter(Boolean)
  if (words.length > 0 && words.length < 12) {
    const regHits = words.filter(
      w => REG_TOKEN_SET.has(w.toLowerCase()),
    ).length
    if (regHits / words.length > 0.22) {
      return {
        id: 'reg-copy',
        severity: 'high',
        label: 'Reg-copy (no action)',
        hint:
          'Statement is mostly regulation tokens. Move the citation to '
          + 'the Constraint cell and write the system action in the '
          + 'Capability cell.',
      }
    }
  }
  return null
}


// ── Detector: too-long ────────────────────────────────────────────────
function detectTooLong(text) {
  const wc = _wordCount(text)
  if (wc <= 25) return null
  return {
    id: 'too-long',
    severity: 'warn',
    label: `${wc} words`,
    hint:
      'Long requirements bundle multiple test cases. Split into one '
      + 'capability per row — each FR should be unambiguously testable.',
    matches: [String(wc)],
  }
}


// ── Detector: and / or compound ───────────────────────────────────────
function detectAndOr(text) {
  if (!text) return null
  if (/\band\s*\/\s*or\b/i.test(text)) {
    return {
      id: 'and-or',
      severity: 'warn',
      label: '"and/or"',
      hint:
        'Ambiguous logic. Replace "and/or" with explicit branches — '
        + 'one FR per branch.',
    }
  }
  const andCount = (text.match(/\band\b/gi) || []).length
  if (andCount >= 2) {
    return {
      id: 'and-or',
      severity: 'warn',
      label: 'compound',
      hint:
        `${andCount} "and" conjunctions detected — likely 2+ `
        + 'requirements in one row. Split into separate FRs.',
    }
  }
  return null
}


// ── Detector: missing constraint (Non-Functional only) ────────────────
function detectMissingConstraint({ meta, reqType }) {
  if (reqType !== 'Non-Functional') return null
  const cons = (meta?.constraint ?? '').trim()
  if (!cons) {
    return {
      id: 'missing-constraint',
      severity: 'info',
      label: 'NF: no threshold',
      hint:
        'Non-Functional requirements need a measurable threshold — '
        + 'e.g. "uptime ≥ 99.5 %", "RPO ≤ 24 h", "p95 latency ≤ 2 s".',
    }
  }
  // No numeric or regulation citation in the constraint cell.
  if (!/\d/.test(cons)
      && !/\b(per|in accordance with|cfr|annex|gamp|iso|≤|≥|<=|>=)\b/i
            .test(cons)) {
    return {
      id: 'missing-constraint',
      severity: 'info',
      label: 'NF: vague threshold',
      hint:
        'Constraint should carry a number with units (e.g. "≤ 24 h") '
        + 'or cite a specific regulation clause.',
    }
  }
  return null
}


// ── Public: analyze a single requirement row ──────────────────────────
/**
 * Run all six detectors against one requirement row.
 *
 * @param {Object} req      — { id, type:'UR'|'FR', statement, parentId? }
 * @param {Object} meta     — { capability, condition, constraint,
 *                              requirement_type, stakeholder }
 * @param {String} derived  — derived "The system shall …" sentence
 *                            (preferred analysis target when available)
 * @return {Array} findings — zero or more { id, severity, label, hint }
 */
export function analyzeRequirement(req, meta, derived) {
  if (!req) return []
  const text = (
    derived
    || meta?.capability
    || req.statement
    || ''
  ).trim()
  if (!text) return []

  const reqType = meta?.requirement_type ?? null
  const ctx = { text, meta, type: req.type, reqType }

  const findings = [
    detectVague(text),
    detectUntestable(ctx),
    detectRegCopy(text),
    detectTooLong(text),
    detectAndOr(text),
    detectMissingConstraint(ctx),
  ].filter(Boolean)

  return findings
}


// ── Public: aggregate counts across a batch ───────────────────────────
/**
 * Roll a per-row findings map into a summary keyed by detector id and
 * by severity. Used by the AI Sidekick aggregate rail.
 *
 * @param {Object} flagsByRow  — { [reqId]: Finding[] }
 * @return {Object} summary
 *   {
 *     totalFlags,            number — sum of findings across rows
 *     rowsWithFlags,         number — distinct rows with ≥ 1 finding
 *     bySeverity: { high, warn, info },
 *     byCategory: { [detectorId]: number },
 *     cleanRows,             number — rows with zero findings
 *   }
 */
export function summarizePatterns(flagsByRow, totalRows) {
  const bySeverity = { high: 0, warn: 0, info: 0 }
  const byCategory = {
    vague: 0, untestable: 0, 'reg-copy': 0,
    'too-long': 0, 'and-or': 0, 'missing-constraint': 0,
  }
  let totalFlags = 0
  let rowsWithFlags = 0
  for (const findings of Object.values(flagsByRow || {})) {
    if (!findings || findings.length === 0) continue
    rowsWithFlags += 1
    for (const f of findings) {
      totalFlags += 1
      if (bySeverity[f.severity] !== undefined) bySeverity[f.severity] += 1
      if (byCategory[f.id] !== undefined) byCategory[f.id] += 1
    }
  }
  return {
    totalFlags,
    rowsWithFlags,
    cleanRows: Math.max(0, (totalRows ?? 0) - rowsWithFlags),
    bySeverity,
    byCategory,
  }
}


// ── Public: severity → brand color map ────────────────────────────────
// Brand-locked accents per react-platform.md rules:
//   #ef4444 error · #f59e0b warning · #007FFF info
export const SEVERITY_COLORS = {
  high: '#ef4444',
  warn: '#f59e0b',
  info: '#007FFF',
}

// Display order used by the aggregate rail.
export const CATEGORY_ORDER = [
  { id: 'untestable',         label: 'Untestable',  severity: 'high' },
  { id: 'reg-copy',           label: 'Reg-copy',    severity: 'high' },
  { id: 'too-long',           label: 'Too long',    severity: 'warn' },
  { id: 'and-or',             label: 'and/or',      severity: 'warn' },
  { id: 'vague',              label: 'Vague',       severity: 'info' },
  { id: 'missing-constraint', label: 'No threshold', severity: 'info' },
]
