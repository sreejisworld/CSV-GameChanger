/**
 * useProjectStore — State management for the project tree.
 *
 * Data flow:
 *   1. On mount: GET /api/navigator/projects → pick first project →
 *      GET /api/navigator/projects/{id} → transform → setTree
 *   2. If API is unreachable or returns no projects → fall back to
 *      static initialTree (demo mode, no writes to API).
 *   3. All mutations (addRelease, approveItem, addRequirement) call
 *      the API first then apply an optimistic local update.
 *
 * UI state (expansion, breadcrumb, heatmap) is always local.
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import { initialTree, GAMP5_TEMPLATE } from '../data/projectTree.js'
import * as api from '../api/navigatorApi.js'
import {
  projectToTree,
  releaseOutToNode,
  itemOutToNode,
} from '../api/treeTransform.js'

// ── Utilities ──────────────────────────────────────────────────

const clone = obj => JSON.parse(JSON.stringify(obj))

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

// Find a node and return it (read-only)
function findNode(nodes, targetId) {
  for (const node of nodes) {
    if (node.id === targetId) return node
    if (node.children?.length) {
      const found = findNode(node.children, targetId)
      if (found) return found
    }
  }
  return null
}

// Build a folder-slug id consistent with treeTransform
function folderNodeId(releaseId, folderName) {
  return `${releaseId}-${folderName.toLowerCase().replace(/\s+/g, '-')}`
}


// ── Hook ───────────────────────────────────────────────────────

export function useProjectStore() {
  const [tree, setTree]             = useState(() => clone(initialTree))
  const [expanded, setExpanded]     = useState(new Set(['proj-labcore', 'gov-labcore', 'v1.0', 'v1.1']))
  const [activePath, setActivePath] = useState([])
  const [heatmapOn, setHeatmapOn]   = useState(false)
  const [apiMode, setApiMode]       = useState(false)   // true = live API
  const [loading, setLoading]       = useState(true)

  // Track the active project id for API calls
  const projectIdRef = useRef(null)


  // ── Initial load ──────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const projects = await api.listProjects()
        if (cancelled) return

        if (!projects || projects.length === 0) {
          // No projects yet — seed a default one
          const created = await api.createProject({
            name: 'LabCore LIMS v4.2 Validation',
            system_name: 'LabCore LIMS',
            compliance_mode: 'GMP',
            description: 'GMP validation programme',
          })
          if (cancelled) return
          projectIdRef.current = created.project_id
          // New project has no releases — keep demo tree but mark live
          setApiMode(true)
        } else {
          // Load full tree for first project
          const full = await api.getProject(projects[0].project_id)
          if (cancelled) return
          projectIdRef.current = full.project_id
          const liveTree = projectToTree(full)
          // If the live project has no releases, fall back to demo tree
          // structure so the UI isn't empty on first run
          if (liveTree.children.length === 0) {
            liveTree.children = clone(initialTree).children
          }
          setTree(liveTree)
          setApiMode(true)
          // Auto-expand top-level nodes
          const topIds = liveTree.children.map(c => c.id)
          setExpanded(new Set([liveTree.id, ...topIds.slice(0, 2)]))
        }
      } catch (err) {
        // API unreachable — stay in demo mode silently
        console.warn('[EVOLV Navigator] API unavailable, using demo data.', err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [])


  // ── Expand / collapse ─────────────────────────────────────────
  const toggleExpand = useCallback(nodeId => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(nodeId) ? next.delete(nodeId) : next.add(nodeId)
      return next
    })
  }, [])

  const isExpanded = useCallback(
    nodeId => expanded.has(nodeId),
    [expanded],
  )


  // ── Breadcrumb selection ──────────────────────────────────────
  const select = useCallback(path => setActivePath(path), [])
  const activeBreadcrumb = activePath


  // ── New Release ───────────────────────────────────────────────
  const addRelease = useCallback(async (name, version, folderTemplate) => {
    if (!name.trim() || !version.trim()) return

    if (apiMode && projectIdRef.current) {
      try {
        const rel = await api.createRelease(projectIdRef.current, {
          name,
          version,
          description: '',
          status: 'Planned',
          folder_template: folderTemplate || null,
        })
        const relNode = releaseOutToNode(rel)
        setTree(prev => {
          const next = clone(prev)
          next.children.push(relNode)
          return next
        })
        setExpanded(prev => new Set([...prev, rel.release_id]))
        return
      } catch (err) {
        console.error('[EVOLV] createRelease failed:', err.message)
        // Fall through to local-only update
      }
    }

    // Demo / fallback — local only
    const id = version.replace(/\s+/g, '-').toLowerCase()
    const newRel = {
      id,
      name: `${version} — ${name}`,
      type: 'release',
      status: 'draft',
      heatScore: 0,
      children: (folderTemplate || GAMP5_TEMPLATE).map(fname => ({
        id: folderNodeId(id, fname),
        name: fname,
        type: 'folder',
        heatScore: 0,
        children: [],
      })),
    }
    setTree(prev => {
      const next = clone(prev)
      next.children.push(newRel)
      return next
    })
    setExpanded(prev => new Set([...prev, id]))
  }, [apiMode])


  // ── Approve item (HITL — FDA AI §3.2) ────────────────────────
  const approveItem = useCallback(async (itemId, releaseId, folder) => {
    // Optimistic local update first (instant UI feedback)
    setTree(prev => {
      const next = clone(prev)
      updateNode([next], itemId, (nodes, idx) => {
        nodes[idx].humanApproved = true
        if (nodes[idx].status === 'in_review') {
          nodes[idx].status = 'approved'
        }
      })
      // Approve shadow link too
      updateNode([next], `SL-${itemId}`, (nodes, idx) => {
        nodes[idx].humanApproved = true
      })
      return next
    })

    // Persist to API if live
    if (apiMode && projectIdRef.current && releaseId && folder) {
      try {
        await api.approveItem(
          projectIdRef.current,
          releaseId,
          itemId,
          folder,
        )
      } catch (err) {
        console.error('[EVOLV] approveItem failed:', err.message)
        // Local state already updated — user sees the change,
        // it just won't persist if the API call failed.
      }
    }
  }, [apiMode])


  // ── Add requirement (with auto shadow link) ───────────────────
  const addRequirement = useCallback(async (releaseId, reqData) => {
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

    if (apiMode && projectIdRef.current) {
      try {
        const item = await api.addItem(projectIdRef.current, releaseId, {
          folder: 'URS',
          name: reqData.title,
          item_type: 'urs',
          artifact_id: reqData.id,
          notes: '',
          status: 'Draft',
        })
        // Use the API-assigned item_id
        reqNode.id = item.item_id
        reqNode._apiItemId = item.item_id

        // Also add a traceability shadow link via API
        await api.addItem(projectIdRef.current, releaseId, {
          folder: 'Traceability Matrix',
          name: `Shadow Link — ${reqData.id}`,
          item_type: 'traceability',
          artifact_id: item.item_id,
          notes: '',
          status: 'Draft',
        })
      } catch (err) {
        console.error('[EVOLV] addRequirement API call failed:', err.message)
      }
    }

    setTree(prev => {
      const next = clone(prev)
      // URS folder
      const ursId = folderNodeId(releaseId, 'URS')
      updateNode([next], ursId, (nodes, idx) => {
        nodes[idx].children.push(reqNode)
      })
      // Traceability folder
      const traceId = folderNodeId(releaseId, 'Traceability Matrix')
        || folderNodeId(releaseId, 'Traceability')
      updateNode([next], traceId, (nodes, idx) => {
        nodes[idx].children.push(shadowNode)
      })
      return next
    })
  }, [apiMode])


  return {
    tree,
    loading,
    apiMode,
    expanded, toggleExpand, isExpanded,
    activeBreadcrumb, select,
    addRelease,
    approveItem,
    addRequirement,
    heatmapOn, setHeatmapOn,
    projectId: projectIdRef.current,
  }
}
