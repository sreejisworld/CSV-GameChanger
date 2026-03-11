/**
 * EVOLV Traceability Map — Mock Data
 *
 * Full bi-directional traceability graph for a LIMS
 * validation programme.  Each node carries:
 *   - upstream:    Business risks this item mitigates
 *   - downstream:  Test scripts that verify this item
 *   - crossRelease: Releases where this item appears
 *   - status:      draft | in_review | approved |
 *                  failed | open_issue
 *   - aiGenerated: true/false (HITL tag shown until approved)
 *   - heatScore:   0–100 (used by Impact Heatmap)
 */

// ── Risks ────────────────────────────────────────────────────
export const risks = [
  {
    id: 'RISK-001',
    title: 'Unauthorised access to patient sample data',
    riskLevel: 'high',
    regulation: '21 CFR Part 11 §11.10(d)',
    mitigatedBy: ['URS-001', 'URS-002'],
    heatScore: 90,
  },
  {
    id: 'RISK-002',
    title: 'Temperature excursion not detected in time',
    riskLevel: 'high',
    regulation: '21 CFR Part 211.68',
    mitigatedBy: ['URS-007', 'URS-008'],
    heatScore: 85,
  },
  {
    id: 'RISK-003',
    title: 'Chain-of-custody break for controlled substances',
    riskLevel: 'high',
    regulation: '21 CFR Part 211.122',
    mitigatedBy: ['URS-010', 'URS-011'],
    heatScore: 80,
  },
  {
    id: 'RISK-004',
    title: 'Audit trail tampering or deletion',
    riskLevel: 'high',
    regulation: '21 CFR Part 11 §11.10(e)',
    mitigatedBy: ['URS-003'],
    heatScore: 75,
  },
  {
    id: 'RISK-005',
    title: 'Instrument calibration data loss',
    riskLevel: 'medium',
    regulation: 'GAMP 5 §10.3',
    mitigatedBy: ['URS-015', 'URS-016'],
    heatScore: 55,
  },
  {
    id: 'RISK-006',
    title: 'Batch release without QA sign-off',
    riskLevel: 'high',
    regulation: '21 CFR Part 211.192',
    mitigatedBy: ['URS-020'],
    heatScore: 88,
  },
  {
    id: 'RISK-007',
    title: 'LIMS-ERP interface data corruption',
    riskLevel: 'medium',
    regulation: 'GAMP 5 §9.2',
    mitigatedBy: ['URS-025'],
    heatScore: 60,
  },
]

// ── Requirements (URS) ────────────────────────────────────────
export const requirements = [
  {
    id: 'URS-001',
    title: 'System shall authenticate all users via company SSO (SAML 2.0)',
    status: 'approved',
    aiGenerated: true,
    humanApproved: true,
    releases: ['v1.0', 'v1.1'],
    criticality: 'high',
    upstream: ['RISK-001'],
    downstream: ['TS-001', 'TS-002'],
    heatScore: 20,
    folder: 'URS',
    regulation: '21 CFR Part 11 §11.300',
  },
  {
    id: 'URS-002',
    title: 'System shall enforce role-based access control with audit logging',
    status: 'approved',
    aiGenerated: true,
    humanApproved: true,
    releases: ['v1.0', 'v1.1', 'v2.0'],
    criticality: 'high',
    upstream: ['RISK-001'],
    downstream: ['TS-003', 'TS-004'],
    heatScore: 30,
    folder: 'URS',
    regulation: '21 CFR Part 11 §11.10(d)',
  },
  {
    id: 'URS-003',
    title: 'System shall maintain an append-only audit trail with SHA-256 integrity hashes',
    status: 'in_review',
    aiGenerated: true,
    humanApproved: false,
    releases: ['v1.0'],
    criticality: 'high',
    upstream: ['RISK-004'],
    downstream: ['TS-005'],
    heatScore: 70,
    folder: 'URS',
    regulation: '21 CFR Part 11 §11.10(e)',
  },
  {
    id: 'URS-004',
    title: 'System shall support electronic signature with meaning per 21 CFR Part 11',
    status: 'draft',
    aiGenerated: true,
    humanApproved: false,
    releases: ['v1.1'],
    criticality: 'high',
    upstream: ['RISK-001'],
    downstream: ['TS-006'],
    heatScore: 65,
    folder: 'URS',
    regulation: '21 CFR Part 11 §11.50',
  },
  {
    id: 'URS-007',
    title: 'System shall monitor sample storage temperature every 5 minutes',
    status: 'approved',
    aiGenerated: false,
    humanApproved: true,
    releases: ['v1.0', 'v1.1'],
    criticality: 'high',
    upstream: ['RISK-002'],
    downstream: ['TS-010', 'TS-011'],
    heatScore: 40,
    folder: 'URS',
    regulation: '21 CFR Part 211.68',
  },
  {
    id: 'URS-008',
    title: 'System shall generate an alert within 60 seconds of temperature excursion',
    status: 'open_issue',
    aiGenerated: true,
    humanApproved: false,
    releases: ['v1.0', 'v1.1'],
    criticality: 'high',
    upstream: ['RISK-002'],
    downstream: ['TS-012'],
    heatScore: 95,
    folder: 'URS',
    regulation: '21 CFR Part 211.68',
    openIssue: 'Alert latency exceeds SLA in load test (INC-2034)',
  },
  {
    id: 'URS-010',
    title: 'System shall record chain-of-custody for all sample transfers',
    status: 'approved',
    aiGenerated: true,
    humanApproved: true,
    releases: ['v1.0'],
    criticality: 'high',
    upstream: ['RISK-003'],
    downstream: ['TS-015', 'TS-016'],
    heatScore: 25,
    folder: 'URS',
    regulation: '21 CFR Part 211.122',
  },
  {
    id: 'URS-011',
    title: 'System shall prevent chain-of-custody modification after analyst sign-off',
    status: 'failed',
    aiGenerated: true,
    humanApproved: false,
    releases: ['v1.1'],
    criticality: 'high',
    upstream: ['RISK-003'],
    downstream: ['TS-017'],
    heatScore: 98,
    folder: 'URS',
    regulation: '21 CFR Part 211.122',
    failedTest: 'TS-017 Negative Test — sign-off bypass found (DEF-441)',
  },
  {
    id: 'URS-015',
    title: 'System shall store instrument calibration records with GxP metadata',
    status: 'approved',
    aiGenerated: true,
    humanApproved: true,
    releases: ['v1.0'],
    criticality: 'medium',
    upstream: ['RISK-005'],
    downstream: ['TS-020'],
    heatScore: 15,
    folder: 'URS',
    regulation: 'GAMP 5 §10.3',
  },
  {
    id: 'URS-020',
    title: 'System shall block batch release without QA Lead electronic signature',
    status: 'in_review',
    aiGenerated: true,
    humanApproved: false,
    releases: ['v1.1', 'v2.0'],
    criticality: 'high',
    upstream: ['RISK-006'],
    downstream: ['TS-025', 'TS-026'],
    heatScore: 78,
    folder: 'URS',
    regulation: '21 CFR Part 211.192',
  },
  {
    id: 'URS-025',
    title: 'System shall validate all data received from ERP interface against schema',
    status: 'draft',
    aiGenerated: true,
    humanApproved: false,
    releases: ['v2.0'],
    criticality: 'medium',
    upstream: ['RISK-007'],
    downstream: ['TS-030'],
    heatScore: 50,
    folder: 'URS',
    regulation: 'GAMP 5 §9.2',
  },
]

// ── Test Scripts ──────────────────────────────────────────────
export const testScripts = [
  { id: 'TS-001', title: 'OQ — SSO Authentication Positive', status: 'approved', aiGenerated: true, humanApproved: true, verifies: ['URS-001'], releases: ['v1.0'], heatScore: 10 },
  { id: 'TS-002', title: 'OQ — SSO Authentication Negative (invalid credentials)', status: 'approved', aiGenerated: true, humanApproved: true, verifies: ['URS-001'], releases: ['v1.0'], heatScore: 10 },
  { id: 'TS-003', title: 'OQ — RBAC Role Assignment Positive', status: 'approved', aiGenerated: true, humanApproved: true, verifies: ['URS-002'], releases: ['v1.0'], heatScore: 15 },
  { id: 'TS-004', title: 'OQ — RBAC Privilege Escalation Negative', status: 'in_review', aiGenerated: true, humanApproved: false, verifies: ['URS-002'], releases: ['v1.1'], heatScore: 55 },
  { id: 'TS-005', title: 'OQ — Audit Trail Integrity Verification', status: 'in_review', aiGenerated: true, humanApproved: false, verifies: ['URS-003'], releases: ['v1.0'], heatScore: 65 },
  { id: 'TS-006', title: 'OQ — Electronic Signature Meaning Validation', status: 'draft', aiGenerated: true, humanApproved: false, verifies: ['URS-004'], releases: ['v1.1'], heatScore: 60 },
  { id: 'TS-010', title: 'OQ — Temperature Monitoring Positive (within threshold)', status: 'approved', aiGenerated: false, humanApproved: true, verifies: ['URS-007'], releases: ['v1.0'], heatScore: 10 },
  { id: 'TS-011', title: 'OQ — Temperature Monitoring Edge (±0.1°C)', status: 'approved', aiGenerated: true, humanApproved: true, verifies: ['URS-007'], releases: ['v1.0'], heatScore: 20 },
  { id: 'TS-012', title: 'OQ — Temperature Alert Latency (60s SLA)', status: 'open_issue', aiGenerated: true, humanApproved: false, verifies: ['URS-008'], releases: ['v1.0', 'v1.1'], heatScore: 95, openIssue: 'Latency 78s in load test — SLA breach (INC-2034)' },
  { id: 'TS-015', title: 'OQ — Chain-of-Custody Transfer Positive', status: 'approved', aiGenerated: true, humanApproved: true, verifies: ['URS-010'], releases: ['v1.0'], heatScore: 10 },
  { id: 'TS-016', title: 'OQ — Chain-of-Custody Multi-Analyst Transfer', status: 'approved', aiGenerated: true, humanApproved: true, verifies: ['URS-010'], releases: ['v1.0'], heatScore: 15 },
  { id: 'TS-017', title: 'OQ — CoC Modification After Sign-Off (Negative)', status: 'failed', aiGenerated: true, humanApproved: false, verifies: ['URS-011'], releases: ['v1.1'], heatScore: 98, failedTest: 'System allowed modification in edge case — DEF-441' },
  { id: 'TS-020', title: 'OQ — Calibration Record Storage with Metadata', status: 'approved', aiGenerated: true, humanApproved: true, verifies: ['URS-015'], releases: ['v1.0'], heatScore: 10 },
  { id: 'TS-025', title: 'UAT — Batch Release QA Sign-Off Workflow', status: 'in_review', aiGenerated: true, humanApproved: false, verifies: ['URS-020'], releases: ['v1.1'], heatScore: 70 },
  { id: 'TS-026', title: 'OQ — Batch Release Blocked Without Signature (Negative)', status: 'draft', aiGenerated: true, humanApproved: false, verifies: ['URS-020'], releases: ['v2.0'], heatScore: 65 },
  { id: 'TS-030', title: 'OQ — ERP Interface Schema Validation', status: 'draft', aiGenerated: true, humanApproved: false, verifies: ['URS-025'], releases: ['v2.0'], heatScore: 45 },
]

// ── Flat searchable index ─────────────────────────────────────
export const searchIndex = [
  ...requirements.map(r => ({ ...r, _type: 'Requirement' })),
  ...testScripts.map(t  => ({ ...t, _type: 'Test Script'  })),
  ...risks.map(rk       => ({ ...rk, _type: 'Risk'         })),
]

// ── Lookup helpers ────────────────────────────────────────────
export const getRequirement = id =>
  requirements.find(r => r.id === id)

export const getTestScript = id =>
  testScripts.find(t => t.id === id)

export const getRisk = id =>
  risks.find(r => r.id === id)

export const getBlastRadius = itemId => {
  const req = getRequirement(itemId)
  if (req) {
    return {
      upstream:    req.upstream.map(getRisk).filter(Boolean),
      downstream:  req.downstream.map(getTestScript).filter(Boolean),
      crossRelease: req.releases,
    }
  }
  const ts = getTestScript(itemId)
  if (ts) {
    const parentReqs = requirements.filter(r =>
      r.downstream.includes(itemId)
    )
    return {
      upstream:    parentReqs,
      downstream:  [],
      crossRelease: ts.releases,
    }
  }
  return { upstream: [], downstream: [], crossRelease: [] }
}
