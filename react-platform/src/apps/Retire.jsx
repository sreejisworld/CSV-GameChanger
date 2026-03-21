/**
 * Retire — Lifecycle Phase 8: Decommissioning
 * Locked until the project reaches active validated state.
 */
export default function Retire() {
  return (
    <div className="flex flex-col h-full items-center justify-center
                    gap-5 text-center px-8">
      <div className="flex flex-col items-center gap-3">
        <div className="w-14 h-14 rounded-2xl bg-bg-card border border-border-base
                        flex items-center justify-center text-3xl">
          🔒
        </div>
        <h2 className="text-text-primary font-semibold text-base">
          Decommissioning
        </h2>
      </div>

      <div className="max-w-sm space-y-2">
        <p className="text-text-muted text-sm">
          Controlled system retirement including data migration,
          archival according to regulatory retention periods, and a
          final validation assessment confirming data integrity.
        </p>
        <p className="text-text-muted text-xs">
          Available once the project has a completed
          <span className="text-lime-DEFAULT"> Validation Summary Report</span>{' '}
          and is in active validated state.
        </p>
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full
                      bg-bg-card border border-border-base">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
        <span className="text-[10px] text-text-muted uppercase tracking-widest">
          Locked — requires validated state
        </span>
      </div>
    </div>
  )
}
