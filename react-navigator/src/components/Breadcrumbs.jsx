/**
 * Breadcrumbs — shows the active navigation path.
 * e.g.  LabCore LIMS › v1.1 › URS › URS-008
 */
export default function Breadcrumbs({ path }) {
  if (!path?.length) {
    return (
      <div className="flex items-center gap-1 text-xs text-navy-500 px-4 py-2 border-b border-navy-600">
        <span className="text-muted">EVOLV</span>
        <span className="text-navy-400">›</span>
        <span className="text-navy-500">Select an item to navigate</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1 text-xs px-4 py-2 border-b border-navy-600 overflow-x-auto whitespace-nowrap">
      <span className="text-muted font-medium">EVOLV</span>
      {path.map((crumb, i) => (
        <span key={crumb.id} className="flex items-center gap-1">
          <span className="text-navy-400">›</span>
          <span className={
            i === path.length - 1
              ? 'text-accent font-semibold'
              : 'text-muted hover:text-white cursor-pointer transition-colors'
          }>
            {crumb.name.length > 22
              ? crumb.name.slice(0, 22) + '…'
              : crumb.name}
          </span>
        </span>
      ))}
    </div>
  )
}
