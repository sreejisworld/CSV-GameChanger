/**
 * DevPortal — Developer Portal.
 *
 * Two sections:
 *  1. API Key Manager — generate scoped keys, copy-once reveal,
 *     stored in localStorage (raw key never persisted).
 *  2. Swagger UI — embedded FastAPI /docs iframe.
 */
import { useState, useCallback } from 'react'

const API_BASE = '/api'

// ── API Key Manager ────────────────────────────────────────────

function ApiKeyManager() {
  const [keys,       setKeys]       = useState(() => {
    try { return JSON.parse(localStorage.getItem('evolv_api_keys') || '[]') }
    catch { return [] }
  })
  const [rawKey,     setRawKey]     = useState(null)   // shown once
  const [generating, setGenerating] = useState(false)
  const [copied,     setCopied]     = useState(false)
  const [tenantId,   setTenantId]   = useState('demo-tenant')
  const [scope,      setScope]      = useState('full_access')

  const generateKey = useCallback(async () => {
    setGenerating(true)
    try {
      const res = await fetch(`${API_BASE}/admin/api-keys`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          tenant_id:  tenantId,
          scopes:     [scope],
          dac_policy: {},
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      // Show raw key once
      setRawKey(data.raw_key)
      // Store metadata (never raw key)
      const meta = {
        key_id:     data.key_id,
        tenant_id:  data.tenant_id,
        scopes:     data.scopes,
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
  }, [tenantId, scope, keys])

  const copyKey = useCallback(() => {
    if (!rawKey) return
    navigator.clipboard.writeText(rawKey).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [rawKey])

  const dismissKey = () => setRawKey(null)

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

      {/* Raw key reveal (shown once after generation) */}
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
            onClick={dismissKey}
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
                    {k.key_id.slice(0, 8)}…
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

// ── Main DevPortal component ───────────────────────────────────

export default function DevPortal() {
  const [activeTab, setActiveTab] = useState('keys')

  const tabs = [
    { id: 'keys',    label: '🔑 API Keys' },
    { id: 'swagger', label: '📖 API Docs (Swagger)' },
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
          API key management, interactive docs, and webhook configuration.
        </p>
      </div>

      {/* Internal tab strip */}
      <div className="flex items-center gap-1 px-6 pt-4 shrink-0">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 rounded-t-lg text-xs font-medium transition-colors
              border-b-2 ${activeTab === t.id
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
        {activeTab === 'keys' && <ApiKeyManager />}

        {activeTab === 'swagger' && (
          <div className="h-full flex flex-col">
            <p className="text-text-muted text-xs mb-3">
              Interactive API documentation — powered by FastAPI / OpenAPI 3.0.
              Ensure the API server is running on{' '}
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
                 className="text-blue-DEFAULT underline underline-offset-2">
                port 8000
              </a>.
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
              ReDoc — alternative API reference documentation.
            </p>
            <iframe
              src="http://localhost:8000/redoc"
              className="app-iframe flex-1 rounded-xl border border-border-base"
              title="ReDoc"
              style={{ minHeight: '600px' }}
            />
          </div>
        )}

        {activeTab === 'webhooks' && (
          <WebhooksPanel />
        )}
      </div>
    </div>
  )
}

// ── Webhooks placeholder ───────────────────────────────────────

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
            <label className="text-[10px] text-text-muted block mb-1">
              HMAC Secret
            </label>
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
        Payloads are HMAC-SHA256 signed. Retry logic: 1 min → 5 min → 15 min.
      </p>
    </div>
  )
}
