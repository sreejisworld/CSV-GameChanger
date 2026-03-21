/**
 * TreeNode — recursive component for one node in the
 * 7-level GAMP 5 project tree.
 *
 * Active folder → Cyber Lime left border + lime glow background.
 * Clean SVG-style icons instead of raw emoji.
 */
import { heatStyle } from './HeatmapToggle.jsx'

// ── SVG icon components (inline, no deps) ─────────────────────
const Icon = ({ d, className = '' }) => (
  <svg viewBox="0 0 16 16" fill="none"
    className={`w-3.5 h-3.5 shrink-0 ${className}`}>
    <path d={d} strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

const FolderIcon   = ({ open, className }) => (
  <svg viewBox="0 0 16 16" fill="none" className={`w-3.5 h-3.5 shrink-0 ${className}`}>
    {open
      ? <path d="M1 4.5A1 1 0 012 3.5h4l1.5 1.5H14A1 1 0 0115 6v7a1 1 0 01-1 1H2a1 1 0 01-1-1V4.5z"
          stroke="currentColor" strokeWidth="1.2" fill="currentColor" fillOpacity=".12"/>
      : <path d="M1 4.5A1 1 0 012 3.5h4l1.5 1.5H14A1 1 0 0115 6v6a1 1 0 01-1 1H2a1 1 0 01-1-1V4.5z"
          stroke="currentColor" strokeWidth="1.2" fill="none"/>
    }
  </svg>
)

const FOLDER_COLORS = {
  'URS':                 'text-blue-400',
  'Risk Matrix':         'text-red-400',
  'Functional Specs':    'text-violet-400',
  'Test Scripts':        'text-purple-400',
  'Traceability':        'text-cyan-400',
  'VSR':                 'text-emerald-400',
  'Supplier Assessment': 'text-amber-400',
}

const RELEASE_STYLE = {
  Released:     { dot: 'bg-success',  text: 'text-green-300'  },
  'In Progress':{ dot: 'bg-warning',  text: 'text-yellow-300' },
  Planned:      { dot: 'bg-accent',   text: 'text-blue-300'   },
  Archived:     { dot: 'bg-white/20', text: 'text-slate-500'  },
}

const ITEM_STATUS_CLS = {
  approved:   'bg-success',
  in_review:  'bg-warning',
  draft:      'bg-white/20',
  failed:     'bg-danger',
  open_issue: 'bg-orange-400',
}

const RISK_PILL = {
  high:   'bg-danger/20 text-danger border-danger/40',
  medium: 'bg-warning/20 text-warning border-warning/40',
  low:    'bg-success/20 text-success border-success/40',
}

const DEPTH_INDENT = 14

export default function TreeNode({
  node,
  depth = 0,
  isExpanded,
  toggleExpand,
  onSelect,
  activePath,
  heatmapOn,
  onApprove,
  _releaseId  = undefined,
  _folderName = undefined,
}) {
  const childReleaseId  = node.type === 'release' ? (node._apiReleaseId || node.id) : _releaseId
  const childFolderName = node.type === 'folder'  ? node.name : _folderName

  const isActive  = activePath?.some(p => p.id === node.id)
  const hasKids   = node.children?.length > 0
  const expanded  = isExpanded(node.id)

  const isLeaf    = ['requirement','testScript','risk','shadowLink','govDoc'].includes(node.type)
  const isFolder  = node.type === 'folder'
  const hasIssue  = node.status === 'open_issue' || node.status === 'failed'
  const needsHITL = node.aiGenerated && !node.humanApproved

  const indent = depth * DEPTH_INDENT

  const handleClick = e => {
    e.stopPropagation()
    if (!isLeaf && hasKids) toggleExpand(node.id)
    onSelect(node)
  }

  // ── Row styles ────────────────────────────────────────────────
  const isFolderActive = isFolder && isActive
  const rowCls = [
    'heat-node group relative flex items-center gap-1.5 cursor-pointer',
    'rounded-lg py-1.5 pr-2 transition-all duration-150',
    isFolderActive
      ? 'bg-lime/8 border-l-2 border-lime shadow-lime/10'
      : isActive
        ? 'bg-accent/10 border-l-2 border-accent'
        : 'border-l-2 border-transparent hover:bg-navy-600/40',
    hasIssue ? 'border-danger/40' : '',
  ].join(' ')

  return (
    <div>
      <div
        onClick={handleClick}
        className={rowCls}
        style={{ paddingLeft: indent + 6, ...heatStyle(node.heatScore, heatmapOn) }}
      >
        {/* Expand chevron */}
        {!isLeaf && (
          <span className={`shrink-0 text-[8px] text-white/25 w-3 transition-transform
                            duration-150 ${expanded ? 'rotate-90' : ''}`}>
            {hasKids ? '▶' : ''}
          </span>
        )}
        {isLeaf && <span className="w-3 shrink-0" />}

        {/* Icon */}
        <NodeIcon node={node} expanded={expanded} isActive={isFolderActive} />

        {/* Label */}
        <span className={[
          'flex-1 text-xs leading-snug truncate',
          node.type === 'project'    ? 'font-semibold text-white' : '',
          node.type === 'governance' ? 'text-purple-300/80 font-medium' : '',
          node.type === 'release'    ? `font-medium ${RELEASE_STYLE[node.status]?.text || 'text-blue-300'}` : '',
          node.type === 'folder'     ? isFolderActive
                                         ? 'text-lime font-semibold'
                                         : `font-medium ${FOLDER_COLORS[node.name] || 'text-slate-300'}`
                                       : '',
          node.type === 'shadowLink' ? 'text-cyan-400/80 italic text-[10px]' : '',
          node.type === 'govDoc'     ? 'text-slate-400' : '',
          !isLeaf && !['project','governance','release','folder'].includes(node.type)
            ? 'text-slate-400' : '',
        ].join(' ')}>
          {node.type === 'risk'
            ? node.id
            : (node.name?.length > 36 ? node.name.slice(0, 36) + '…' : node.name)}
        </span>

        {/* HITL badge */}
        {needsHITL && (
          <span className="shrink-0 text-[8px] bg-yellow-900/40 text-yellow-400
                           border border-yellow-700/50 rounded px-1 py-0.5 hitl-pulse
                           font-mono">
            AI
          </span>
        )}

        {/* Risk pill */}
        {node.type === 'risk' && (
          <span className={`shrink-0 text-[8px] border rounded px-1 py-0.5 font-semibold
                            ${RISK_PILL[node.riskLevel] || ''}`}>
            {node.riskLevel?.toUpperCase()}
          </span>
        )}

        {/* Status dot */}
        {node.status && node.type !== 'release' && node.type !== 'risk' && (
          <span className={`shrink-0 w-1.5 h-1.5 rounded-full
                            ${ITEM_STATUS_CLS[node.status] || 'bg-white/20'}`} />
        )}

        {/* Release status dot */}
        {node.type === 'release' && (
          <span className={`shrink-0 w-1.5 h-1.5 rounded-full
                            ${RELEASE_STYLE[node.status]?.dot || 'bg-white/20'}`} />
        )}

        {/* Approve button on hover */}
        {needsHITL && onApprove && (
          <button
            onClick={e => {
              e.stopPropagation()
              onApprove(node.id, _releaseId, _folderName)
            }}
            title="Mark as Human-Approved (FDA AI §3.2)"
            className="hidden group-hover:flex shrink-0 items-center
                       text-[8px] bg-success/20 text-success
                       border border-success/40 rounded px-1.5 py-0.5
                       hover:bg-success/30 transition-colors"
          >
            ✓
          </button>
        )}
      </div>

      {/* Children */}
      {expanded && hasKids && (
        <div className="relative border-l border-white/5"
          style={{ marginLeft: indent + 16 }}>
          {node.children.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              isExpanded={isExpanded}
              toggleExpand={toggleExpand}
              onSelect={onSelect}
              activePath={activePath}
              heatmapOn={heatmapOn}
              onApprove={onApprove}
              _releaseId={childReleaseId}
              _folderName={childFolderName}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function NodeIcon({ node, expanded, isActive }) {
  if (node.type === 'folder') {
    const color = isActive
      ? 'text-lime'
      : FOLDER_COLORS[node.name] || 'text-slate-400'
    return <FolderIcon open={expanded} className={color} />
  }

  const iconMap = {
    project: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-accent">
        <rect x="2" y="2" width="5.5" height="5.5" rx="1.2"
          stroke="currentColor" strokeWidth="1.2" fill="currentColor" fillOpacity=".15"/>
        <rect x="8.5" y="2" width="5.5" height="5.5" rx="1.2"
          stroke="currentColor" strokeWidth="1.2" fill="none"/>
        <rect x="2" y="8.5" width="5.5" height="5.5" rx="1.2"
          stroke="currentColor" strokeWidth="1.2" fill="none"/>
        <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1.2"
          stroke="currentColor" strokeWidth="1.2" fill="none"/>
      </svg>
    ),
    governance: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-purple-400">
        <path d="M8 1.5L14 5v3c0 3.5-2.5 5.8-6 7-3.5-1.2-6-3.5-6-7V5L8 1.5z"
          stroke="currentColor" strokeWidth="1.2" fill="currentColor" fillOpacity=".1"/>
      </svg>
    ),
    release: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-blue-400">
        <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
        <circle cx="8" cy="8" r="2" fill="currentColor" fillOpacity=".5"/>
      </svg>
    ),
    requirement: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-accent/70">
        <rect x="2" y="2" width="12" height="12" rx="1.5"
          stroke="currentColor" strokeWidth="1.2" fill="none"/>
        <path d="M5 6h6M5 8.5h4M5 11h5.5"
          stroke="currentColor" strokeWidth="1.1" strokeLinecap="round"/>
      </svg>
    ),
    testScript: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-purple-400">
        <path d="M5.5 2H3a1 1 0 00-1 1v10a1 1 0 001 1h10a1 1 0 001-1V3a1 1 0 00-1-1h-2.5"
          stroke="currentColor" strokeWidth="1.2"/>
        <rect x="5.5" y="1" width="5" height="2.5" rx="1"
          stroke="currentColor" strokeWidth="1.1" fill="currentColor" fillOpacity=".2"/>
        <path d="M5 7.5l2 2 3.5-3.5"
          stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      </svg>
    ),
    risk: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-danger/80">
        <path d="M8 2L14.5 13H1.5L8 2z"
          stroke="currentColor" strokeWidth="1.2" fill="currentColor" fillOpacity=".1"/>
        <path d="M8 6v3M8 11v.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
      </svg>
    ),
    shadowLink: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-cyan-400/70">
        <path d="M6 8a2 2 0 002 2h2a2 2 0 000-4H8"
          stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
        <path d="M10 8a2 2 0 00-2-2H6a2 2 0 000 4h2"
          stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      </svg>
    ),
    govDoc: (
      <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-slate-400">
        <path d="M4 2h6l3 3v9a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"
          stroke="currentColor" strokeWidth="1.2" fill="none"/>
        <path d="M10 2v3h3M6 8h4M6 10.5h3"
          stroke="currentColor" strokeWidth="1.1" strokeLinecap="round"/>
      </svg>
    ),
  }

  return iconMap[node.type] || (
    <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5 shrink-0 text-slate-500">
      <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.2"/>
    </svg>
  )
}
