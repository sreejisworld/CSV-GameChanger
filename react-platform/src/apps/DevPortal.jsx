/**
 * DevPortal — Developer Portal.
 *
 * Internal tabs:
 *  1. API Keys  — Production & Sandbox key types, copy-once reveal,
 *                 stored in localStorage (raw key never persisted).
 *  2. EVOLV Connect — Pre-built integration cards for SAP, Salesforce, Veeva.
 *  3. API Docs (Swagger) — embedded FastAPI /docs iframe.
 *  4. ReDoc    — alternative reference docs.
 *  5. Webhooks — register event endpoints with HMAC secret.
 */
import { useState, useCallback } from 'react'

const API_BASE = '/api'

// ── EVOLV Connect integration cards ───────────────────────────

const INTEGRATIONS = [
  {
    id:      'sap',
    name:    'SAP S/4HANA',
    icon:    '🏢',
    color:   '#007FFF',
    status:  'available',
    desc:    'Bi-directional sync of change requests, validation documents, '
             + 'and audit records with SAP GRC and SAP QM modules.',
    events:  ['CHANGE_REQUEST_ASSESSED', 'URS_GENERATED', 'VALIDATION_APPROVED'],
    docs:    'SAP Integration Guide v2.1',
    badge:   'REST + OData',
  },
  {
    id:      'salesforce',
    name:    'Salesforce Health Cloud',
    icon:    '☁️',
    color:   '#00a1e0',
    status:  'available',
    desc:    'Push validation milestones and compliance status into Salesforce '
             + 'Health Cloud cases and custom validation objects.',
    events:  ['VALIDATION_APPROVED', 'COMPLIANCE_EXCEPTION', 'AUDIT_EXPORTED'],
    docs:    'Salesforce Integration Guide v1.3',
    badge:   'REST + Apex',
  },
  {
    id:      'veeva',
    name:    'Veeva Vault',
    icon:    '🔬',
    color:   '#f59e0b',
    status:  'available',
    desc:    'Auto-file EVOLV-generated URS, test scripts, and validation '
             + 'reports directly into Veeva Vault QMS document workflows.',
    events:  ['URS_GENERATED', 'TEST_SCRIPT_EXPORTED', 'VALIDATION_APPROVED'],
    docs:    'Veeva Vault Integration Guide v1.0',
    badge:   'Vault REST API',
  },
  {
    id:      'servicenow',
    name:    'ServiceNow GRC',
    icon:    '🛠️',
    color:   '#32CD32',
    status:  'native',
    desc:    'Native webhook receiver for ServiceNow Change Requests. '
             + 'Automated risk assessment and GAMP 5 classification on CR arrival.',
    events:  ['CHANGE_REQUEST_RECEIVED', 'RISK_ASSESSMENT_COMPLETED'],
    docs:    'ServiceNow Webhook Spec',
    badge:   'Native',
  },
  {
    id:      'jira',
    name:    'Jira Software',
    icon:    '🔵',
    color:   '#0052CC',
    status:  'coming-soon',
    desc:    'Sync EVOLV validation items as Jira epics and stories with '
             + 'automatic GAMP 5 risk labels and acceptance-criteria fields.',
    events:  [],
    docs:    '',
    badge:   'Q3 2026',
  },
  {
    id:      'azure',
    name:    'Azure DevOps',
    icon:    '🔷',
    color:   '#0078d4',
    status:  'coming-soon',
    desc:    'Pipeline integration for automated validation evidence collection '
             + 'and traceability matrix population on each CI/CD build.',
    events:  [],
    docs:    '',
    badge:   'Q3 2026',
  },
]

function ConnectCard({ integration }) {
  const [connected, setConnected] = useState(false)
  const [expanded,  setExpanded]  = useState(false)
  const isNative    = integration.status === 'native'
  const isAvailable = integration.status === 'available' || isNative
  const isSoon      = integration.status === 'coming-soon'

  return (
    <div
      className={`glass rounded-xl p-5 flex flex-col gap-3 transition-all
                  ${isSoon ? 'opacity-50' : 'hover:border-blue-DEFAULT/30'}`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{integration.icon}</span>
          <div>
            <p className="text-white text-sm font-semibold">{integration.name}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className="text-[9px] px-1.5 py-0.5 rounded border font-medium"
                style={{
                  color:            integration.color,
                  borderColor:      integration.color + '40',
                  backgroundColor:  integration.color + '15',
                }}
              >
                {integration.badge}
              </span>
              {connected && (
                <span className="text-[9px] text-lime-DEFAULT border
                                 border-lime-DEFAULT/30 bg-lime-dim rounded
                                 px-1.5 py-0.5">
                  ● Connected
                </span>
              )}
              {isNative && !connected && (
                <span className="text-[9px] text-lime-DEFAULT border
                                 border-lime-DEFAULT/30 bg-lime-dim rounded
                                 px-1.5 py-0.5 animate-pulse-lime">
                  ● Live
                </span>
              )}
            </div>
          </div>
        </div>
        {isAvailable && (
          <button
            onClick={() => setConnected(p => !p)}
            className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-all
              ${connected
                ? 'border border-border-base text-text-muted hover:text-red-400 hover:border-red-400/40'
                : 'bg-blue-DEFAULT text-white shadow-[0_0_12px_rgba(0,127,255,0.3)] hover:brightness-110'
              }`}
          >
            {connected ? 'Disconnect' : 'Connect'}
          </button>
        )}
      </div>

      {/* Description */}
      <p className="text-text-secondary text-xs leading-relaxed">{integration.desc}</p>

      {/* Event tags */}
      {integration.events.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {integration.events.map(ev => (
            <span key={ev}
              className="text-[9px] px-2 py-0.5 rounded bg-bg-hover
                         border border-border-base text-text-muted font-mono">
              {ev}
            </span>
          ))}
        </div>
      )}

      {/* Expandable config */}
      {connected && isAvailable && (
        <div className="border-t border-border-base pt-3 space-y-2 animate-fade-in">
          <button
            onClick={() => setExpanded(p => !p)}
            className="text-[11px] text-blue-DEFAULT hover:underline"
          >
            {expanded ? '▼ Hide config' : '▶ Show config'}
          </button>
          {expanded && (
            <div className="glass rounded-xl p-3 space-y-2">
              <div>
                <label className="text-[9px] text-text-muted block mb-1">
                  Webhook URL (send events to)
                </label>
                <input
                  readOnly
                  value={`https://your-${integration.id}.example.com/evolv/webhook`}
                  className="w-full bg-bg-base border border-border-base rounded-lg
                             px-3 py-1.5 text-[11px] font-mono text-text-secondary
                             outline-none"
                />
              </div>
              <div>
                <label className="text-[9px] text-text-muted block mb-1">
                  EVOLV API Endpoint
                </label>
                <input
                  readOnly
                  value={`${window.location.origin}/api/${integration.id}/push`}
                  className="w-full bg-bg-base border border-border-base rounded-lg
                             px-3 py-1.5 text-[11px] font-mono text-text-secondary
                             outline-none"
                />
              </div>
              {integration.docs && (
                <p className="text-[10px] text-text-muted">
                  📄 Reference: {integration.docs}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── API Key Manager ────────────────────────────────────────────

function ApiKeyManager() {
  const [keys,       setKeys]       = useState(() => {
    try { return JSON.parse(localStorage.getItem('evolv_api_keys') || '[]') }
    catch { return [] }
  })
  const [rawKey,     setRawKey]     = useState(null)
  const [generating, setGenerating] = useState(false)
  const [copied,     setCopied]     = useState(false)
  const [tenantId,   setTenantId]   = useState('demo-tenant')
  const [scope,      setScope]      = useState('full_access')
  const [keyType,    setKeyType]    = useState('sandbox')

  const generateKey = useCallback(async () => {
    setGenerating(true)
    try {
      const res = await fetch(`${API_BASE}/admin/api-keys`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          tenant_id:  tenantId,
          scopes:     [scope],
          key_type:   keyType,
          dac_policy: {},
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setRawKey(data.raw_key)
      const meta = {
        key_id:     data.key_id,
        tenant_id:  data.tenant_id,
        scopes:     data.scopes,
        key_type:   keyType,
        created_at: data.created_at,
        active:     data.active,
      }
      const updated = [meta, ...keys]
      setKeys(updated)
      localStorage.setItem('evolv_api_keys', JSON.stringify(updated))
    } catch (err) {
      alert(`Failed to generate key: ${err.message}`)
    } finally {
      setGenerating(false)
    }
  }, [tenantId, scope, keyType, keys])

  const copyKey = useCallback(() => {
    if (!rawKey) return
    navigator.clipboard.writeText(rawKey).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [rawKey])

  const revokeKey = useCallback(keyId => {
    const updated = keys.filter(k => k.key_id !== keyId)
    setKeys(updated)
    localStorage.setItem('evolv_api_keys', JSON.stringify(updated))
  }, [keys])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-semibold text-sm flex items-center gap-2">
          🔑 API Key Manager
          <span className="text-[9px] text-text-muted border border-border-base
                           rounded px-1.5 py-0.5">21 CFR Part 11</span>
        </h2>
      </div>

      {/* Raw key reveal (shown once) */}
      {rawKey && (
        <div className="key-reveal p-4 space-y-3 animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="text-lime-DEFAULT text-sm">✓</span>
            <p className="text-lime-DEFAULT text-xs font-semibold">
              API Key generated — copy it now. It will not be shown again.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <code className="flex-1 font-mono text-xs text-lime-DEFAULT
                             bg-bg-base rounded-lg px-3 py-2 truncate border
                             border-lime-DEFAULT/20">
              {rawKey}
            </code>
            <button
              onClick={copyKey}
              className="shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg
                         bg-lime-DEFAULT text-bg-base text-xs font-semibold
                         hover:brightness-110 transition-all"
            >
              {copied ? '✓ Copied!' : '📋 Copy'}
            </button>
          </div>
          <button
            onClick={() => setRawKey(null)}
            className="text-[10px] text-text-muted hover:text-text-secondary
                       underline underline-offset-2"
          >
            I have copied my key — dismiss
          </button>
        </div>
      )}

      {/* Generator form */}
      <div className="glass rounded-xl p-4 space-y-3">
        <p className="text-text-muted text-xs">Generate a new scoped API key</p>

        {/* Key type toggle */}
        <div>
          <label className="text-[10px] text-text-muted block mb-1.5">
            Key Environment
          </label>
          <div className="flex rounded-lg border border-border-base overflow-hidden
                          text-xs font-medium">
            {[
              { value: 'sandbox',    label: '🧪 Sandbox',    color: '#32CD32' },
              { value: 'production', label: '🔴 Production', color: '#ef4444' },
            ].map(opt => (
              <button
                key={opt.value}
                onClick={() => setKeyType(opt.value)}
                className={`flex-1 py-2 transition-colors
                  ${keyType === opt.value
                    ? 'bg-bg-hover text-white'
                    : 'text-text-muted hover:text-text-secondary'
                  }`}
                style={keyType === opt.value
                  ? { borderBottom: `2px solid ${opt.color}` }
                  : {}}
              >
                {opt.label}
              </button>
            ))}
          </div>
          {keyType === 'production' && (
            <p className="text-[10px] text-amber-400 mt-1.5">
              ⚠ Production keys access live regulatory data. Handle with care.
            </p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-text-muted block mb-1">Tenant ID</label>
            <input
              value={tenantId}
              onChange={e => setTenantId(e.target.value)}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors"
            />
          </div>
          <div>
            <label className="text-[10px] text-text-muted block mb-1">Scope</label>
            <select
              value={scope}
              onChange={e => setScope(e.target.value)}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors"
            >
              <option value="full_access">full_access</option>
              <option value="audit_only">audit_only (read-only)</option>
              <option value="bulk_only">bulk_only</option>
            </select>
          </div>
        </div>
        <button
          onClick={generateKey}
          disabled={generating}
          className="flex items-center gap-2 px-4 py-2 rounded-lg
                     bg-blue-DEFAULT text-white text-xs font-semibold
                     hover:brightness-110 disabled:opacity-50
                     transition-all shadow-[0_0_16px_rgba(0,127,255,0.3)]"
        >
          {generating ? '⏳ Generating…' : '⚡ Generate Key'}
        </button>
      </div>

      {/* Key table */}
      {keys.length > 0 && (
        <div className="glass rounded-xl overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border-base text-text-muted">
                <th className="text-left px-4 py-2.5">Key ID</th>
                <th className="text-left px-4 py-2.5">Env</th>
                <th className="text-left px-4 py-2.5">Tenant</th>
                <th className="text-left px-4 py-2.5">Scopes</th>
                <th className="text-left px-4 py-2.5">Created</th>
                <th className="text-left px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {keys.map(k => (
                <tr key={k.key_id}
                  className="border-b border-border-base/50 hover:bg-bg-hover
                             transition-colors">
                  <td className="px-4 py-2.5 font-mono text-blue-DEFAULT">
                    {k.key_id?.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-2.5">
                    {k.key_type === 'production'
                      ? <span className="text-red-400 text-[10px]">🔴 Prod</span>
                      : <span className="text-lime-DEFAULT text-[10px]">🧪 Sandbox</span>}
                  </td>
                  <td className="px-4 py-2.5 text-text-secondary">{k.tenant_id}</td>
                  <td className="px-4 py-2.5">
                    {(k.scopes || []).map(s => (
                      <span key={s}
                        className="bg-blue-dim border border-blue-DEFAULT/20
                                   text-blue-DEFAULT rounded px-1.5 py-0.5 mr-1">
                        {s}
                      </span>
                    ))}
                  </td>
                  <td className="px-4 py-2.5 text-text-muted">
                    {k.created_at?.slice(0, 10)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-lime-DEFAULT">● Active</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() => revokeKey(k.key_id)}
                      className="text-red-400 hover:text-red-300 text-[10px]
                                 hover:underline transition-colors"
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Webhooks ───────────────────────────────────────────────────

function WebhooksPanel() {
  const EVENTS = [
    'SENTINEL_SCAN_COMPLETED',
    'BULK_VALIDATE_COMPLETE',
    'CHANGE_REQUEST_ASSESSED',
  ]
  const [url,    setUrl]    = useState('')
  const [event,  setEvent]  = useState(EVENTS[0])
  const [secret, setSecret] = useState('')
  const [status, setStatus] = useState(null)

  const register = async () => {
    if (!url) return
    setStatus('registering')
    try {
      const res = await fetch('/api/webhooks/register', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          tenant_id: 'demo-tenant',
          url,
          events: [event],
          secret: secret || 'demo-secret',
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      setStatus('success')
      setTimeout(() => setStatus(null), 3000)
    } catch {
      setStatus('error')
      setTimeout(() => setStatus(null), 3000)
    }
  }

  return (
    <div className="space-y-4 max-w-xl">
      <h2 className="text-white font-semibold text-sm">🪝 Webhook Registry</h2>
      <div className="glass rounded-xl p-4 space-y-3">
        <div>
          <label className="text-[10px] text-text-muted block mb-1">Endpoint URL</label>
          <input
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="https://your-system.example.com/webhook"
            className="w-full bg-bg-base border border-border-base rounded-lg
                       px-3 py-2 text-xs text-text-primary outline-none
                       focus:border-border-blue transition-colors"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-text-muted block mb-1">Event</label>
            <select
              value={event}
              onChange={e => setEvent(e.target.value)}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors"
            >
              {EVENTS.map(ev => <option key={ev}>{ev}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-text-muted block mb-1">HMAC Secret</label>
            <input
              type="password"
              value={secret}
              onChange={e => setSecret(e.target.value)}
              placeholder="webhook-secret"
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors"
            />
          </div>
        </div>
        <button
          onClick={register}
          disabled={status === 'registering'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg
                     bg-blue-DEFAULT text-white text-xs font-semibold
                     hover:brightness-110 disabled:opacity-50 transition-all"
        >
          {status === 'registering' ? '⏳ Registering…'
           : status === 'success'   ? '✓ Registered!'
           : status === 'error'     ? '✗ Failed'
           :                         '⚡ Register Webhook'}
        </button>
      </div>
      <p className="text-text-muted text-[10px]">
        Payloads are HMAC-SHA256 signed. Retry: 1 min → 5 min → 15 min.
      </p>
    </div>
  )
}

// ── Main DevPortal component ───────────────────────────────────

export default function DevPortal() {
  const [activeTab, setActiveTab] = useState('keys')

  const tabs = [
    { id: 'keys',    label: '🔑 API Keys' },
    { id: 'connect', label: '🔗 EVOLV Connect' },
    { id: 'swagger', label: '📖 API Docs' },
    { id: 'redoc',   label: '📘 ReDoc' },
    { id: 'webhooks',label: '🪝 Webhooks' },
  ]

  return (
    <div className="h-full flex flex-col bg-bg-base">

      {/* Header */}
      <div className="px-6 py-5 border-b border-border-base shrink-0">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-white font-bold text-lg">Developer Portal</h1>
          <span className="ai-badge">EVOLV API v1.0</span>
        </div>
        <p className="text-text-secondary text-xs">
          API key management, EVOLV Connect integrations, docs, and webhooks.
        </p>
      </div>

      {/* Internal tab strip */}
      <div className="flex items-center gap-1 px-6 pt-4 shrink-0 overflow-x-auto">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 rounded-t-lg text-xs font-medium transition-colors
              border-b-2 whitespace-nowrap
              ${activeTab === t.id
                ? 'text-blue-DEFAULT border-blue-DEFAULT bg-blue-dim'
                : 'text-text-muted border-transparent hover:text-text-secondary'
              }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="neon-sep mx-6" />

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 min-h-0">
        {activeTab === 'keys'    && <ApiKeyManager />}
        {activeTab === 'webhooks' && <WebhooksPanel />}

        {activeTab === 'connect' && (
          <div className="space-y-5">
            <div>
              <h2 className="text-white font-semibold text-sm mb-1">
                🔗 EVOLV Connect
              </h2>
              <p className="text-text-secondary text-xs">
                Pre-built integrations for the pharma and life-sciences tech stack.
                Connect once — validation data flows automatically.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {INTEGRATIONS.map(integration => (
                <ConnectCard key={integration.id} integration={integration} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'swagger' && (
          <div className="h-full flex flex-col">
            <p className="text-text-muted text-xs mb-3">
              Interactive API documentation — powered by FastAPI / OpenAPI 3.0.
            </p>
            <iframe
              src="http://localhost:8000/docs"
              className="app-iframe flex-1 rounded-xl border border-border-base"
              title="Swagger UI"
              style={{ minHeight: '600px' }}
            />
          </div>
        )}

        {activeTab === 'redoc' && (
          <div className="h-full flex flex-col">
            <p className="text-text-muted text-xs mb-3">
              ReDoc — clean alternative API reference documentation.
            </p>
            <iframe
              src="http://localhost:8000/redoc"
              className="app-iframe flex-1 rounded-xl border border-border-base"
              title="ReDoc"
              style={{ minHeight: '600px' }}
            />
          </div>
        )}
      </div>
    </div>
  )
}
