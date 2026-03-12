/** Config — Tenant configuration placeholder. */
export default function Config() {
  const sections = [
    {
      title: 'Tenant Nomenclature Engine',
      icon: '🏷️',
      desc: 'Map EVOLV terminology to your organisation\'s vocabulary. "User Requirements Specification" can become "System Anforderungsdokument" for German sites.',
      badge: 'Enterprise',
    },
    {
      title: 'Site-Specific Compliance Modes',
      icon: '🛡️',
      desc: 'Configure per-site regulatory context: GMP (manufacturing), GCP (clinical), GLP (labs), ISO 13485 (medical devices).',
      badge: 'Enterprise',
    },
    {
      title: 'ABAC Policy Engine',
      icon: '🔐',
      desc: 'Define attribute-based access control rules. The "Wow Rule": no user — regardless of role — can approve a GxP document with an expired training record.',
      badge: 'Admin',
    },
    {
      title: 'AI Model Configuration',
      icon: '🤖',
      desc: 'Configure EVOLV AI engine parameters, minimum confidence thresholds, and HITL approval requirements per document type.',
      badge: 'Admin',
      accentColor: '#32CD32',
    },
  ]

  return (
    <div className="h-full overflow-y-auto bg-bg-base">
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-white font-bold text-xl mb-1">Configuration</h1>
          <p className="text-text-secondary text-sm">
            Tenant, compliance, and access control settings.
          </p>
          <div className="neon-sep mt-3" />
        </div>

        <div className="space-y-4">
          {sections.map(s => (
            <div key={s.title}
              className="glass rounded-xl p-5 flex items-start gap-4
                         cursor-not-allowed opacity-70
                         hover:opacity-90 transition-opacity">
              <span className="text-3xl shrink-0">{s.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-white font-semibold text-sm">{s.title}</h3>
                  <span className="text-[9px] px-1.5 py-0.5 rounded border
                                   bg-bg-hover border-border-base text-text-muted">
                    {s.badge}
                  </span>
                </div>
                <p className="text-text-secondary text-xs leading-relaxed">{s.desc}</p>
              </div>
              <span className="text-text-muted text-xs shrink-0 mt-0.5">
                Coming Soon
              </span>
            </div>
          ))}
        </div>

        <p className="text-center text-text-muted text-xs mt-8">
          Full configuration panel available in EVOLV Enterprise edition.
        </p>
      </div>
    </div>
  )
}
