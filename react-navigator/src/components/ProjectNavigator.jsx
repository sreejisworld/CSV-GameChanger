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

const PHASES = [
  'plan', 'requirements', 'risk', 'design',
  'verify', 'release', 'monitor', 'retire',
]

export default function ProjectNavigator({ store, onFolderSelect, currentView, evolvContext }) {
  const { projectName = '', phaseCompletion = {} } = evolvContext ?? {}
  const {
    tree,
    loading,
    apiMode,
    expanded, toggleExpand, isExpanded,
    activeBreadcrumb, select,
    addRelease,
    approveItem,
    heatmapOn, setHeatmapOn,
  } = store

  const [showNewRelease, setShowNewRelease] = useState(false)

  const handleSelect = node => {
    const path = findPath(tree, node.id)
    const resolvedPath = path || [{ id: node.id, name: node.name, type: node.type }]
    select(resolvedPath)

    // Notify App for view-switching when a folder or document is clicked
    if (onFolderSelect && (node.type === 'folder' || node.type === 'govDoc')) {
      onFolderSelect(node, resolvedPath)
    }
  }

  const handleNewRelease = (name, version, folders) => {
    addRelease(name, version, folders)
    setShowNewRelease(false)
  }

  return (
    <>
      {/* ── Sidebar shell ── */}
      <aside className="flex flex-col h-screen w-72 bg-navy-800/95 border-r border-white/5
                        select-none overflow-hidden backdrop-blur-sm">

        {/* Logo */}
        <div className="px-4 pt-4 pb-3 border-b border-white/5
                        bg-gradient-to-b from-navy-800 to-navy-800/80">
          <div className="flex items-center gap-3">
            {/* EVOLV mark */}
            <div className="relative w-8 h-8 shrink-0">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-accent to-accent/60
                              flex items-center justify-center shadow-blue">
                <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
                  <path d="M4 14L10 4l6 10H4z" stroke="white" strokeWidth="1.6"
                    fill="white" fillOpacity=".15" strokeLinejoin="round"/>
                </svg>
              </div>
              {/* Cyber Lime pulse dot */}
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full
                               bg-lime shadow-lime animate-pulse-dot" />
            </div>

            <div className="flex-1 min-w-0">
              <h1 className="text-white font-bold text-sm leading-none tracking-tight">
                EVOLV
              </h1>
              {projectName ? (
                <p className="text-[9px] text-lime/70 mt-0.5 truncate font-medium"
                   title={projectName}>
                  {projectName}
                </p>
              ) : (
                <p className="text-[9px] text-lime/70 mt-0.5 uppercase tracking-widest
                               font-medium">
                  Validation Factory
                </p>
              )}
            </div>

            {/* Mode badges */}
            <div className="flex flex-col items-end gap-1">
              <span className="text-[9px] bg-success/10 text-success
                               border border-success/25 rounded-full px-1.5 py-0.5
                               font-semibold">
                GMP
              </span>
              <span className={`text-[8px] rounded-full px-1.5 py-0.5 border font-mono
                ${apiMode
                  ? 'bg-accent/10 text-accent border-accent/25'
                  : 'bg-white/5 text-white/30 border-white/10'}`}>
                {loading ? '·' : apiMode ? 'Live' : 'Demo'}
              </span>
            </div>
          </div>
        </div>

        {/* Phase completion strip */}
        {Object.keys(phaseCompletion).length > 0 && (
          <div className="px-3 py-2 border-b border-white/5 flex items-center gap-1">
            {PHASES.map(phase => {
              const done = phaseCompletion[phase]
              return (
                <div
                  key={phase}
                  title={`${phase.charAt(0).toUpperCase() + phase.slice(1)}${done ? ' ✓' : ''}`}
                  className="flex-1 h-1 rounded-full transition-colors"
                  style={{
                    background: done
                      ? '#32CD32'
                      : 'rgba(255,255,255,0.08)',
                    boxShadow: done ? '0 0 4px rgba(50,205,50,0.5)' : 'none',
                  }}
                />
              )
            })}
          </div>
        )}

        {/* Search */}
        <div className="px-3 py-2.5 border-b border-white/5">
          <GlobalSearchBar />
        </div>

        {/* Heatmap toggle + New Release row */}
        <div className="px-3 py-2 border-b border-white/5 flex items-center gap-2">
          <HeatmapToggle
            on={heatmapOn}
            onToggle={() => setHeatmapOn(v => !v)}
          />
          <button
            onClick={() => setShowNewRelease(true)}
            className="ml-auto flex items-center gap-1 px-2.5 py-1 rounded-lg
                       bg-lime/15 hover:bg-lime/25 text-lime text-xs
                       font-semibold transition-colors border border-lime/25"
          >
            + New Release
          </button>
        </div>

        {/* Breadcrumbs */}
        <Breadcrumbs path={activeBreadcrumb} />

        {/* Legend when heatmap is on */}
        {heatmapOn && (
          <div className="px-3 py-1.5 border-b border-white/5 flex items-center
                          gap-3 text-[10px] text-white/30">
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
        <div className="px-3 py-1.5 border-b border-white/5 flex items-center
                        gap-2 text-[10px] text-white/30">
          <span className="text-[9px] bg-yellow-900/40 text-yellow-400/80
                           border border-yellow-700/40 rounded px-1 py-0.5
                           font-mono hitl-pulse">AI</span>
          <span>= awaiting human review (FDA AI §3.2)</span>
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
        <div className="px-4 py-3 border-t border-white/5
                        flex items-center justify-between">
          <span className="text-[9px] text-white/20 leading-tight">
            Powered by EVOLV<br/>
            <span className="text-white/15">WingstarTech Inc.</span>
          </span>
          <span className="text-[9px] text-white/20 font-mono">v2.0</span>
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
