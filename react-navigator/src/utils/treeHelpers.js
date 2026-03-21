/**
 * treeHelpers — utilities for extracting items from the live project tree.
 *
 * The tree is the single source of truth whether in Demo or Live mode.
 * These helpers let views read items without importing mock data directly.
 */

/**
 * Walk the tree and collect all children of folders matching `folderName`.
 * Returns items from ALL releases (union).
 */
export function getItemsByFolder(tree, folderName) {
  const items = []
  if (!tree) return items

  function walk(node) {
    if (node.type === 'folder' && node.name === folderName) {
      items.push(...(node.children || []))
      return
    }
    for (const child of node.children || []) {
      walk(child)
    }
  }

  walk(tree)

  // Deduplicate by id (same item can appear in multiple releases)
  const seen = new Set()
  return items.filter(item => {
    if (seen.has(item.id)) return false
    seen.add(item.id)
    return true
  })
}

/**
 * Walk the tree and count all leaf items grouped by status.
 * Returns { total, approved, in_review, draft, failed, open_issue }
 */
export function countByStatus(items) {
  return {
    total:      items.length,
    approved:   items.filter(i => i.status === 'approved').length,
    in_review:  items.filter(i => i.status === 'in_review').length,
    draft:      items.filter(i => i.status === 'draft').length,
    failed:     items.filter(i => i.status === 'failed').length,
    open_issue: items.filter(i => i.status === 'open_issue').length,
  }
}

/**
 * Return all releases in the tree.
 */
export function getReleases(tree) {
  if (!tree) return []
  return (tree.children || []).filter(c => c.type === 'release')
}

/**
 * Build the traceability graph edges from all folder items in the tree.
 * Returns { nodes: [], edges: [] } for the canvas graph.
 */
export function buildTraceGraph(tree) {
  const reqItems   = getItemsByFolder(tree, 'URS')
  const testItems  = getItemsByFolder(tree, 'Test Scripts')
  const riskItems  = getItemsByFolder(tree, 'Risk Matrix')
  const traceItems = getItemsByFolder(tree, 'Traceability')
    .concat(getItemsByFolder(tree, 'Traceability Matrix'))

  const nodes = [
    ...reqItems.map(r => ({
      id: r.id, label: r.id, type: 'req',
      full: r.name, status: r.status,
    })),
    ...testItems.map(t => ({
      id: t.id, label: t.id, type: 'test',
      full: t.name, status: t.status,
    })),
    ...riskItems.map(rk => ({
      id: rk.id, label: rk.id, type: 'risk',
      full: rk.name,
    })),
  ]

  // Edges from shadow links: SL-{reqId} → link req to test
  const edges = []
  traceItems.forEach(sl => {
    if (sl.linkedTo) {
      // shadow link points at the req; connect req → tests that share
      // same prefix heuristic (TS-001 ↔ URS-001)
      const reqId = sl.linkedTo
      if (reqItems.find(r => r.id === reqId)) {
        testItems.forEach(t => {
          // simple heuristic: connect if test verifies matching req by number
          const reqNum = reqId.replace(/\D/g, '')
          const tsNum  = t.id.replace(/[^\d]/g, '').slice(0, reqNum.length)
          if (tsNum === reqNum) {
            edges.push({ source: reqId, target: t.id })
          }
        })
      }
    }
  })

  // Also connect risk items → reqs they mitigate (by riskLevel heat)
  riskItems.forEach(rk => {
    const riskNum = rk.id.replace(/\D/g, '')
    reqItems.forEach(r => {
      const reqNum = r.id.replace(/\D/g, '')
      if (riskNum === reqNum.slice(0, riskNum.length)) {
        edges.push({ source: rk.id, target: r.id })
      }
    })
  })

  return { nodes, edges }
}
