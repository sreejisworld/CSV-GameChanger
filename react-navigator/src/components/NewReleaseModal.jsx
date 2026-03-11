/**
 * NewReleaseModal — dialog for creating a release with
 * auto-populated GAMP 5 folder template.
 */
import { useState } from 'react'
import { GAMP5_TEMPLATE } from '../data/projectTree.js'

export default function NewReleaseModal({ onConfirm, onClose }) {
  const [name,     setName]     = useState('')
  const [version,  setVersion]  = useState('')
  const [folders,  setFolders]  = useState(new Set(GAMP5_TEMPLATE))

  const toggleFolder = f =>
    setFolders(prev => {
      const next = new Set(prev)
      next.has(f) ? next.delete(f) : next.add(f)
      return next
    })

  const handleSubmit = e => {
    e.preventDefault()
    if (!name.trim() || !version.trim()) return
    onConfirm(name.trim(), version.trim(), [...folders])
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center search-overlay">
      <div className="bg-navy-700 border border-navy-500 rounded-xl w-full max-w-md shadow-2xl animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-navy-500">
          <div>
            <h2 className="text-white font-semibold">New Release</h2>
            <p className="text-xs text-muted mt-0.5">
              Auto-populates GAMP 5 folder structure
            </p>
          </div>
          <button onClick={onClose} className="text-muted hover:text-white text-lg leading-none">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 py-4 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs text-muted mb-1 font-medium">Release Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. ERP Integration Validation"
              className="w-full bg-navy-800 border border-navy-500 rounded-lg px-3 py-2
                         text-white text-sm placeholder-navy-400
                         focus:outline-none focus:border-accent"
            />
          </div>

          {/* Version */}
          <div>
            <label className="block text-xs text-muted mb-1 font-medium">Version</label>
            <input
              type="text"
              value={version}
              onChange={e => setVersion(e.target.value)}
              placeholder="e.g. v2.1"
              className="w-full bg-navy-800 border border-navy-500 rounded-lg px-3 py-2
                         text-white text-sm placeholder-navy-400
                         focus:outline-none focus:border-accent"
            />
          </div>

          {/* Folder template */}
          <div>
            <label className="block text-xs text-muted mb-2 font-medium">
              GAMP 5 Folder Template
              <span className="ml-1 text-navy-400">(deselect to exclude)</span>
            </label>
            <div className="grid grid-cols-2 gap-1.5">
              {GAMP5_TEMPLATE.map(f => (
                <label
                  key={f}
                  className={`
                    flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
                    border text-xs transition-colors
                    ${folders.has(f)
                      ? 'bg-accent/10 border-accent/60 text-white'
                      : 'bg-navy-800 border-navy-600 text-muted'}
                  `}
                >
                  <input
                    type="checkbox"
                    checked={folders.has(f)}
                    onChange={() => toggleFolder(f)}
                    className="accent-blue-500"
                  />
                  {f}
                </label>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="submit"
              disabled={!name.trim() || !version.trim()}
              className="flex-1 bg-accent hover:bg-accent-dark disabled:opacity-40
                         text-white text-sm font-semibold py-2 rounded-lg
                         transition-colors"
            >
              Create Release
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-navy-600 hover:bg-navy-500 text-muted
                         text-sm py-2 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
