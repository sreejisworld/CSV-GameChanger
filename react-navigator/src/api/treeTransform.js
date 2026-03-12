/**
 * treeTransform.js — Converts the EVOLV FastAPI ProjectStore
 * response format into the nested tree node format expected
 * by the React ProjectNavigator components.
 *
 * API format  →  React tree node format
 * ─────────────────────────────────────
 * project     →  { type: 'project', id: project_id, ... }
 * release     →  { type: 'release', id: release_id, ... }
 * folder      →  { type: 'folder',  id: `${releaseId}-${slug}`, ... }
 * item        →  { type: <mapped>,  id: item_id, ... }
 */

// API status → React status
const STATUS = {
  Draft:       'draft',
  'In Review': 'in_review',
  Approved:    'approved',
  Rejected:    'failed',
  Retired:     'draft',
  Released:    'approved',
  Planned:     'draft',
  'In Progress': 'in_review',
  Archived:    'approved',
}

// API item_type → React node type
const ITEM_TYPE = {
  urs:          'requirement',
  test_script:  'testScript',
  risk:         'risk',
  traceability: 'shadowLink',
  report:       'govDoc',
  note:         'govDoc',
  supplier_doc: 'govDoc',
}

function slug(str) {
  return str.toLowerCase().replace(/\s+/g, '-')
}

function mapStatus(apiStatus) {
  return STATUS[apiStatus] ?? 'draft'
}

function mapItemType(apiType) {
  return ITEM_TYPE[apiType] ?? 'govDoc'
}

/**
 * Transform a single API item dict into a React tree leaf node.
 */
export function itemToNode(item, folderName) {
  const isTraceability = folderName === 'Traceability Matrix'
  const reactType = isTraceability ? 'shadowLink' : mapItemType(item.item_type)
  const id = isTraceability ? `SL-${item.item_id}` : item.item_id
  const name = isTraceability
    ? `↔ Shadow Link — ${item.artifact_id || item.item_id}`
    : item.name

  return {
    id,
    name,
    type: reactType,
    status: mapStatus(item.status),
    aiGenerated: false,          // API doesn't track this yet
    humanApproved: item.status === 'Approved',
    heatScore: 0,               // Derive later from risk data
    artifact_id: item.artifact_id,
    notes: item.notes,
    created_at: item.created_at,
    updated_at: item.updated_at,
    // Keep original API ids for further API calls
    _apiItemId: item.item_id,
    linkedTo: isTraceability ? item.artifact_id : undefined,
    children: [],
  }
}

/**
 * Transform a folder name + items array into a React folder node.
 */
function folderToNode(folderName, items, releaseId) {
  return {
    id: `${releaseId}-${slug(folderName)}`,
    name: folderName,
    type: 'folder',
    heatScore: 0,
    children: items.map(item => itemToNode(item, folderName)),
  }
}

/**
 * Transform an API release dict into a React release node.
 */
function releaseToNode(rel) {
  const folders = Object.entries(rel.folders || {}).map(
    ([name, items]) => folderToNode(name, items, rel.release_id)
  )
  return {
    id: rel.release_id,
    name: `${rel.version} — ${rel.name}`,
    type: 'release',
    status: mapStatus(rel.status),
    heatScore: 0,
    _apiReleaseId: rel.release_id,
    children: folders,
  }
}

/**
 * Transform a full API project dict (with releases) into a React
 * project tree root node.
 */
export function projectToTree(proj) {
  const releases = Object.values(proj.releases || {}).map(releaseToNode)
  return {
    id: proj.project_id,
    name: proj.name,
    type: 'project',
    system: proj.system_name,
    complianceMode: proj.compliance_mode,
    heatScore: 0,
    _apiProjectId: proj.project_id,
    children: releases,
  }
}

/**
 * Build a local-only release node immediately after a successful
 * POST /releases API call (optimistic UI update).
 *
 * @param {object} apiRelease  - ReleaseOut from FastAPI
 * @returns React tree release node
 */
export function releaseOutToNode(apiRelease) {
  return releaseToNode(apiRelease)
}

/**
 * Build a local-only item node immediately after a successful
 * POST /items API call (optimistic UI update).
 *
 * @param {object} apiItem   - ItemOut from FastAPI
 * @param {string} folder    - folder the item was added to
 * @returns React tree leaf node
 */
export function itemOutToNode(apiItem, folder) {
  return itemToNode(
    {
      item_id:    apiItem.item_id,
      name:       apiItem.name,
      item_type:  apiItem.item_type,
      status:     apiItem.status,
      artifact_id: apiItem.artifact_id,
      notes:      apiItem.notes,
      created_at: apiItem.created_at,
      updated_at: apiItem.updated_at,
    },
    folder,
  )
}
