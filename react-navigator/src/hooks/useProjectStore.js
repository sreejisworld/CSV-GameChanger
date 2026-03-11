/**
 * useProjectStore — State management for the project tree.
 *
 * Handles:
 *  - Tree expansion state
 *  - Active selection (breadcrumb path)
 *  - New Release creation with GAMP 5 folder template
 *  - Item approval (removes HITL badge)
 *  - Auto shadow-link injection in Traceability folder
 *  - Heatmap mode toggle
 */
import { useState, useCallback } from 'react'
import { initialTree, GAMP5_TEMPLATE } from '../data/projectTree.js'

// Deep clone utility
const clone = obj => JSON.parse(JSON.stringify(obj))

// Build a new release node with all GAMP 5 folders
function buildNewRelease(name, version, folderTemplate) {
  const id = version.replace(/\s+/g, '-').toLowerCase()
  return {
    id,
    name: `${version} — ${name}`,
    type: 'release',
    status: 'Planned',
    heatScore: 0,
    children: (folderTemplate || GAMP5_TEMPLATE).map(fname => ({
      id: `${id}-${fname.replace(/\s+/g, '-').toLowerCase()}`,
      name: fname,
      type: 'folder',
      heatScore: 0,
      children: [],
    })),
  }
}

// Find and update a node by id (returns true if found)
function updateNode(nodes, targetId, updater) {
  for (let i = 0; i < nodes.length; i++) {
    if (nodes[i].id === targetId) {
      updater(nodes, i)
      return true
    }
    if (nodes[i].children?.length) {
      if (updateNode(nodes[i].children, targetId, updater)) return true
    }
  }
  return false
}

export function useProjectStore() {
  const [tree, setTree]             = useState(() => clone(initialTree))
  const [expanded, setExpanded]     = useState(new Set(['proj-labcore', 'gov-labcore', 'v1.0', 'v1.1']))
  const [activePath, setActivePath] = useState([])   // breadcrumb
  const [heatmapOn, setHeatmapOn]   = useState(false)

  // ── Expand / collapse ──────────────────────────────────────
  const toggleExpand = useCallback(nodeId => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(nodeId)) next.delete(nodeId)
      else next.add(nodeId)
      return next
    })
  }, [])

  const isExpanded = useCallback(
    nodeId => expanded.has(nodeId),
    [expanded]
  )

  // ── Breadcrumb selection ───────────────────────────────────
  const select = useCallback((path) => {
    setActivePath(path) // [{id, name, type}, ...]
  }, [])

  const activeBreadcrumb = activePath

  // ── New Release ────────────────────────────────────────────
  const addRelease = useCallback((name, version, folderTemplate) => {
    if (!name.trim() || !version.trim()) return
    const newRel = buildNewRelease(name, version, folderTemplate)
    setTree(prev => {
      const next = clone(prev)
      next.children.push(newRel)
      return next
    })
    setExpanded(prev => new Set([...prev, newRel.id]))
  }, [])

  // ── Approve item (clear HITL badge) ───────────────────────
  const approveItem = useCallback(itemId => {
    setTree(prev => {
      const next = clone(prev)
      updateNode([next], itemId, (nodes, idx) => {
        nodes[idx].humanApproved = true
        nodes[idx].status = nodes[idx].status === 'in_review'
          ? 'approved'
          : nodes[idx].status
      })
      // Also approve shadow link
      updateNode([next], `SL-${itemId}`, (nodes, idx) => {
        nodes[idx].humanApproved = true
      })
      return next
    })
  }, [])

  // ── Add requirement (with auto shadow link) ────────────────
  const addRequirement = useCallback((releaseId, reqData) => {
    const reqNode = {
      id: reqData.id,
      name: reqData.title,
      type: 'requirement',
      status: 'draft',
      aiGenerated: true,
      humanApproved: false,
      heatScore: 40,
      children: [],
    }
    const shadowNode = {
      id: `SL-${reqData.id}`,
      name: `↔ Shadow Link — ${reqData.id}`,
      type: 'shadowLink',
      linkedTo: reqData.id,
      status: 'draft',
      humanApproved: false,
      heatScore: 40,
      children: [],
    }
    setTree(prev => {
      const next = clone(prev)
      // Add to URS folder
      updateNode([next], `${releaseId}-urs`, (nodes, idx) => {
        nodes[idx].children.push(reqNode)
      })
      // Auto-inject shadow link in Traceability folder
      updateNode([next], `${releaseId}-traceability`, (nodes, idx) => {
        nodes[idx].children.push(shadowNode)
      })
      return next
    })
  }, [])

  return {
    tree,
    expanded, toggleExpand, isExpanded,
    activeBreadcrumb, select,
    addRelease,
    approveItem,
    addRequirement,
    heatmapOn, setHeatmapOn,
  }
}
