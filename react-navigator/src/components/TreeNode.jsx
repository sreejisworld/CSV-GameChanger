/**
 * TreeNode — recursive component for one node in the
 * 7-level GAMP 5 project tree.
 *
 * Node types and their visual treatment:
 *  project     → top-level accent bar
 *  governance  → purple tint
 *  release     → status-colored expander
 *  folder      → GAMP folder icon
 *  requirement → colored by status + HITL badge
 *  testScript  → teal icon
 *  risk        → red/amber/green risk pill
 *  shadowLink  → dashed border, linked icon
 *  govDoc      → document icon
 */
import { heatStyle } from './HeatmapToggle.jsx'

const TYPE_ICONS = {
  project:     '🏢',
  governance:  '🛡',
  release:     null,   // uses status icon
  folder:      null,   // uses folder map
  requirement: '📋',
  testScript:  '🧪',
  risk:        '⚠️',
  shadowLink:  '🔗',
  govDoc:      '📄',
}

const FOLDER_ICONS = {
  'URS':                   '📋',
  'Risk Matrix':           '⚠️',
  'Functional Specs':      '📐',
  'Test Scripts':          '🧪',
  'Traceability':          '🔗',
  'VSR':                   '📄',
  'Supplier Assessment':   '🏭',
}

const RELEASE_STATUS = {
  Released:    { icon: '🟢', cls: 'text-green-400' },
  'In Progress':{ icon: '🟡', cls: 'text-yellow-400' },
  Planned:     { icon: '🔵', cls: 'text-blue-400'  },
  Archived:    { icon: '⚫', cls: 'text-slate-500'  },
}

const ITEM_STATUS_CLS = {
  approved:   'text-green-400',
  in_review:  'text-yellow-400',
  draft:      'text-slate-500',
  failed:     'text-red-400',
  open_issue: 'text-orange-400',
}

const RISK_LEVEL_CLS = {
  high:   'bg-red-900/50 text-red-300 border-red-700',
  medium: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  low:    'bg-green-900/50 text-green-300 border-green-700',
}

const DEPTH_INDENT = 12 // px per level

export default function TreeNode({
  node,
  depth = 0,
  isExpanded,
  toggleExpand,
  onSelect,
  activePath,
  heatmapOn,
  onApprove,
  // Threading context for API calls
  _releaseId   = undefined,
  _folderName  = undefined,
}) {
  // Propagate release / folder context to children
  const childReleaseId  = node.type === 'release'
    ? (node._apiReleaseId || node.id)
    : _releaseId
  const childFolderName = node.type === 'folder'
    ? node.name
    : _folderName
  const isActive  = activePath?.some(p => p.id === node.id)
  const hasKids   = node.children?.length > 0
  const expanded  = isExpanded(node.id)

  // ── visual config per type ──────────────────────────────────
  const icon = getIcon(node)

  const isLeaf = ['requirement', 'testScript', 'risk', 'shadowLink', 'govDoc']
    .includes(node.type)

  const hasIssue  = node.status === 'open_issue' || node.status === 'failed'
  const isValid   = node.status === 'approved' && node.humanApproved
  const needsHITL = node.aiGenerated && !node.humanApproved

  const indent = depth * DEPTH_INDENT

  const handleClick = e => {
    e.stopPropagation()
    if (!isLeaf && hasKids) toggleExpand(node.id)
    onSelect(node)
  }

  return (
    <div>
      {/* ── Node row ── */}
      <div
        onClick={handleClick}
        className={`
          heat-node group relative flex items-center gap-1.5 cursor-pointer
          rounded-md py-1 pr-2 transition-colors duration-150
          ${isActive ? 'bg-accent/15 text-white' : 'hover:bg-navy-600/50 text-slate-300'}
          ${hasIssue ? 'glow-red' : ''}
          ${isValid  ? 'glow-green' : ''}
          ${node.type === 'shadowLink' ? 'border-l-2 border-dashed border-navy-400' : ''}
        `}
        style={{ paddingLeft: indent + 6, ...heatStyle(node.heatScore, heatmapOn) }}
      >
        {/* Expand chevron */}
        {!isLeaf && (
          <span className={`
            shrink-0 text-[10px] text-muted w-3
            transition-transform duration-150
            ${expanded ? 'rotate-90' : ''}
          `}>
            {hasKids ? '▶' : ''}
          </span>
        )}
        {isLeaf && <span className="w-3 shrink-0" />}

        {/* Icon */}
        <span className="shrink-0 text-sm leading-none">{icon}</span>

        {/* Label */}
        <span className={`
          flex-1 text-xs leading-snug truncate
          ${node.type === 'project' ? 'font-semibold text-white' : ''}
          ${node.type === 'governance' ? 'text-purple-300' : ''}
          ${node.type === 'release' ? `font-medium ${RELEASE_STATUS[node.status]?.cls || 'text-blue-300'}` : ''}
          ${node.type === 'folder' ? 'text-slate-300 font-medium' : ''}
          ${node.type === 'shadowLink' ? 'text-cyan-400 italic' : ''}
        `}>
          {node.type === 'risk'
            ? node.id
            : node.name?.length > 38
              ? node.name.slice(0, 38) + '…'
              : node.name}
        </span>

        {/* HITL badge */}
        {needsHITL && (
          <span className="shrink-0 text-[9px] bg-yellow-900/50 text-yellow-400
                           border border-yellow-700 rounded px-1 py-0.5 hitl-pulse">
            🤖
          </span>
        )}

        {/* Risk level pill */}
        {node.type === 'risk' && (
          <span className={`
            shrink-0 text-[9px] border rounded px-1 py-0.5
            ${RISK_LEVEL_CLS[node.riskLevel] || ''}
          `}>
            {node.riskLevel?.toUpperCase()}
          </span>
        )}

        {/* Status dot */}
        {node.status && node.type !== 'release' && (
          <span className={`shrink-0 text-[10px] ${ITEM_STATUS_CLS[node.status] || 'text-slate-500'}`}>
            ●
          </span>
        )}

        {/* Approve button (shown on hover for HITL items) */}
        {needsHITL && onApprove && (
          <button
            onClick={e => {
              e.stopPropagation()
              onApprove(node.id, _releaseId, _folderName)
            }}
            title="Mark as Human-Approved (FDA AI Guidance §3.2)"
            className="hidden group-hover:flex shrink-0 items-center gap-0.5
                       text-[9px] bg-green-900/60 text-green-400
                       border border-green-700 rounded px-1.5 py-0.5
                       hover:bg-green-800/60 transition-colors"
          >
            ✓ Approve
          </button>
        )}

        {/* Item count badge for folders */}
        {!isLeaf && hasKids && (
          <span className="hidden group-hover:flex shrink-0 text-[9px]
                           bg-navy-600 text-navy-400 rounded-full px-1.5 py-0.5">
            {node.children.length}
          </span>
        )}
      </div>

      {/* ── Children ── */}
      {expanded && hasKids && (
        <div className={`
          relative border-l border-navy-600 ml-[${indent + 14}px]
        `}
          style={{ marginLeft: indent + 14 }}
        >
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

function getIcon(node) {
  if (node.type === 'folder') return FOLDER_ICONS[node.name] || '📂'
  if (node.type === 'release') return RELEASE_STATUS[node.status]?.icon || '🔵'
  if (node.type === 'govDoc') return node.status === 'approved' ? '✅' : '📄'
  return TYPE_ICONS[node.type] || '📄'
}
