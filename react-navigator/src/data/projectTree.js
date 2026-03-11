/**
 * EVOLV Project Tree — Initial State
 *
 * 7-level GAMP 5 hierarchy:
 *   L1 Project → L2 Governance → L3 Release →
 *   L4 Folder → L5 Document → L6 Requirement → L7 Step
 *
 * Folders auto-created on New Release:
 *   URS | Risk Matrix | Functional Specs |
 *   Test Scripts | Traceability | VSR | Supplier Assessment
 */

import { requirements, testScripts, risks } from './traceabilityMap.js'

const GAMP5_TEMPLATE = [
  'URS',
  'Risk Matrix',
  'Functional Specs',
  'Test Scripts',
  'Traceability',
  'VSR',
  'Supplier Assessment',
]

export { GAMP5_TEMPLATE }

// ── Folder heat scores (aggregate of children) ───────────────
const folderHeat = (folderName, releaseId) => {
  if (folderName === 'URS') {
    const items = requirements.filter(r =>
      r.releases.includes(releaseId)
    )
    if (!items.length) return 0
    return Math.round(
      items.reduce((s, r) => s + r.heatScore, 0) / items.length
    )
  }
  if (folderName === 'Test Scripts') {
    const items = testScripts.filter(t =>
      t.releases.includes(releaseId)
    )
    if (!items.length) return 0
    return Math.round(
      items.reduce((s, t) => s + t.heatScore, 0) / items.length
    )
  }
  if (folderName === 'Risk Matrix') return 80
  return 15
}

// ── Build folder node ─────────────────────────────────────────
const buildFolder = (name, releaseId) => ({
  id: `${releaseId}-${name.replace(/\s+/g, '-').toLowerCase()}`,
  name,
  type: 'folder',
  heatScore: folderHeat(name, releaseId),
  children: buildFolderChildren(name, releaseId),
})

const buildFolderChildren = (folderName, releaseId) => {
  if (folderName === 'URS') {
    return requirements
      .filter(r => r.releases.includes(releaseId))
      .map(r => ({
        id: r.id,
        name: r.title,
        type: 'requirement',
        status: r.status,
        aiGenerated: r.aiGenerated,
        humanApproved: r.humanApproved,
        heatScore: r.heatScore,
        regulation: r.regulation,
        children: [],
      }))
  }
  if (folderName === 'Test Scripts') {
    return testScripts
      .filter(t => t.releases.includes(releaseId))
      .map(t => ({
        id: t.id,
        name: t.title,
        type: 'testScript',
        status: t.status,
        aiGenerated: t.aiGenerated,
        humanApproved: t.humanApproved,
        heatScore: t.heatScore,
        children: [],
      }))
  }
  if (folderName === 'Risk Matrix') {
    return risks.map(rk => ({
      id: rk.id,
      name: rk.title,
      type: 'risk',
      riskLevel: rk.riskLevel,
      heatScore: rk.heatScore,
      children: [],
    }))
  }
  if (folderName === 'Traceability') {
    // Shadow links — auto-created from requirements
    return requirements
      .filter(r => r.releases.includes(releaseId))
      .map(r => ({
        id: `SL-${r.id}`,
        name: `↔ Shadow Link — ${r.id}`,
        type: 'shadowLink',
        linkedTo: r.id,
        status: r.status,
        humanApproved: r.humanApproved,
        heatScore: r.heatScore,
        children: [],
      }))
  }
  return []
}

// ── Project tree ──────────────────────────────────────────────
export const initialTree = {
  id: 'proj-labcore',
  name: 'LabCore LIMS v4.2',
  type: 'project',
  system: 'LabCore LIMS',
  complianceMode: 'GMP',
  heatScore: 72,
  children: [
    // L2 — Governance
    {
      id: 'gov-labcore',
      name: 'Governance',
      type: 'governance',
      heatScore: 20,
      children: [
        { id: 'vp-001', name: 'Validation Plan v1.2', type: 'govDoc', status: 'approved', aiGenerated: false, humanApproved: true, heatScore: 5, children: [] },
        { id: 'vp-002', name: 'SOP-VAL-001 — Validation Lifecycle', type: 'govDoc', status: 'approved', aiGenerated: false, humanApproved: true, heatScore: 5, children: [] },
        { id: 'vp-003', name: 'Supplier Qualification Master', type: 'govDoc', status: 'in_review', aiGenerated: true, humanApproved: false, heatScore: 30, children: [] },
        { id: 'vp-004', name: 'Risk Management Framework', type: 'govDoc', status: 'approved', aiGenerated: false, humanApproved: true, heatScore: 10, children: [] },
      ],
    },

    // L3 — Release v1.0
    {
      id: 'v1.0',
      name: 'v1.0 — Initial Validation',
      type: 'release',
      status: 'Released',
      heatScore: 35,
      children: GAMP5_TEMPLATE.map(f => buildFolder(f, 'v1.0')),
    },

    // L3 — Release v1.1
    {
      id: 'v1.1',
      name: 'v1.1 — Patch Validation',
      type: 'release',
      status: 'In Progress',
      heatScore: 82,
      children: GAMP5_TEMPLATE.map(f => buildFolder(f, 'v1.1')),
    },

    // L3 — Release v2.0
    {
      id: 'v2.0',
      name: 'v2.0 — ERP Integration Validation',
      type: 'release',
      status: 'Planned',
      heatScore: 55,
      children: GAMP5_TEMPLATE.map(f => buildFolder(f, 'v2.0')),
    },
  ],
}
