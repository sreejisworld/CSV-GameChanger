/**
 * ProjectNavigator — main sidebar component.
 *
 * Layout (top → bottom):
 *  1. EVOLV logo + compliance mode badge
 *  2. Impact Search Bar (Cmd+K)
 *  3. Heatmap toggle
 *  4. Breadcrumbs
 *  5. + New Release button
 *  6. Hierarchical tree (7-level GAMP structure)
 */
import { useState } from 'react'
import { useProjectStore } from '../hooks/useProjectStore.js'
import TreeNode              from './TreeNode.jsx'
import Breadcrumbs           from './Breadcrumbs.jsx'
import GlobalSearchBar       from './GlobalSearchBar.jsx'
import HeatmapToggle         from './HeatmapToggle.jsx'
import NewReleaseModal       from './NewReleaseModal.jsx'

// Build breadcrumb path by walking the tree to find a node
function findPath(node, targetId, path = []) {
  const current = [...path, { id: node.id, name: node.name, type: node.type }]
  if (node.id === targetId) return current
  if (!node.children) return null
  for (const child of node.children) {
    const found = findPath(child, targetId, current)
    if (found) return found
  }
  return null
}

export default function ProjectNavigator() {
  const {
    tree,
    loading,
    apiMode,
    expanded, toggleExpand, isExpanded,
    activeBreadcrumb, select,
    addRelease,
    approveItem,
    heatmapOn, setHeatmapOn,
  } = useProjectStore()

  const [showNewRelease, setShowNewRelease] = useState(false)

  const handleSelect = node => {
    const path = findPath(tree, node.id)
    select(path || [{ id: node.id, name: node.name, type: node.type }])
  }

  const handleNewRelease = (name, version, folders) => {
    addRelease(name, version, folders)
    setShowNewRelease(false)
  }

  return (
    <>
      {/* ── Sidebar shell ── */}
      <aside className="flex flex-col h-screen w-72 bg-navy-800 border-r border-navy-600
                        select-none overflow-hidden">

        {/* Logo */}
        <div className="px-4 pt-4 pb-3 border-b border-navy-600 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center
                          text-white font-bold text-sm shrink-0">
            E
          </div>
          <div>
            <h1 className="text-white font-bold text-sm leading-none">EVOLV</h1>
            <p className="text-[10px] text-muted mt-0.5 uppercase tracking-wider">
              The Validation Factory
            </p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <span className="text-[10px] bg-green-900/50 text-green-400
                             border border-green-700 rounded-full px-2 py-0.5">
              GMP
            </span>
            {/* Live / Demo mode indicator */}
            <span className={`text-[9px] rounded-full px-1.5 py-0.5 border
              ${apiMode
                ? 'bg-blue-900/50 text-blue-400 border-blue-700'
                : 'bg-slate-800 text-slate-500 border-slate-600'}`}>
              {loading ? '…' : apiMode ? 'Live' : 'Demo'}
            </span>
          </div>
        </div>

        {/* Search */}
        <div className="px-3 py-2.5 border-b border-navy-600">
          <GlobalSearchBar />
        </div>

        {/* Heatmap toggle + New Release row */}
        <div className="px-3 py-2 border-b border-navy-600 flex items-center gap-2">
          <HeatmapToggle
            on={heatmapOn}
            onToggle={() => setHeatmapOn(v => !v)}
          />
          <button
            onClick={() => setShowNewRelease(true)}
            className="ml-auto flex items-center gap-1 px-2.5 py-1 rounded
                       bg-accent hover:bg-accent-dark text-white text-xs
                       font-semibold transition-colors"
          >
            + New Release
          </button>
        </div>

        {/* Breadcrumbs */}
        <Breadcrumbs path={activeBreadcrumb} />

        {/* Legend when heatmap is on */}
        {heatmapOn && (
          <div className="px-3 py-1.5 border-b border-navy-600 flex items-center
                          gap-3 text-[10px] text-muted">
            <span>Heatmap:</span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block"/>Low
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-orange-500 inline-block"/>Med
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500 inline-block"/>Hot
            </span>
          </div>
        )}

        {/* HITL legend */}
        <div className="px-3 py-1.5 border-b border-navy-600 flex items-center
                        gap-3 text-[10px] text-muted">
          <span className="text-yellow-400 hitl-pulse">🤖</span>
          <span>= AI-generated, awaiting human review (FDA AI §3.2)</span>
        </div>

        {/* Tree */}
        <div className="flex-1 overflow-y-auto px-2 py-2">
          <TreeNode
            node={tree}
            depth={0}
            isExpanded={isExpanded}
            toggleExpand={toggleExpand}
            onSelect={handleSelect}
            activePath={activeBreadcrumb}
            heatmapOn={heatmapOn}
            onApprove={approveItem}
          />
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-navy-600 flex items-center justify-between">
          <span className="text-[10px] text-navy-400">
            Powered by EVOLV | WingstarTech Inc.
          </span>
          <span className="text-[10px] text-navy-500">v2.0</span>
        </div>
      </aside>

      {/* New Release modal */}
      {showNewRelease && (
        <NewReleaseModal
          onConfirm={handleNewRelease}
          onClose={() => setShowNewRelease(false)}
        />
      )}
    </>
  )
}
