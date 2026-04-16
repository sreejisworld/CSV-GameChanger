/**
 * DevPortal — Developer Portal.
 *
 * Internal tabs:
 *  1. ServiceNow Demo — live CR submission, real-time risk assessment display.
 *  2. API Keys  — Production & Sandbox key types, copy-once reveal,
 *                 stored in localStorage (raw key never persisted).
 *  3. EVOLV Connect — Pre-built integration cards for SAP, Salesforce, Veeva.
 *  4. API Docs (Swagger) — embedded FastAPI /docs iframe.
 *  5. ReDoc    — alternative reference docs.
 *  6. Webhooks — register event endpoints with HMAC secret.
 */
import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { API_BASE as _EVOLV_API_BASE } from '../config.js'

const API_BASE = '/api'
const EVOLV_API = _EVOLV_API_BASE

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

// ── ServiceNow Demo Panel ──────────────────────────────────────

const SN_SCENARIOS = [
  {
    id:          'emergency',
    label:       '🚨 Emergency Patch',
    color:       '#ef4444',
    cr_id:       'CR-2024-0891',
    description: 'Critical security patch — production LIMS system '
                 + 'requires immediate hotfix to address data integrity flaw.',
    system_criticality: 'critical',
    change_type: 'emergency',
    expected:    'HIGH Risk · Rigorous Scripted',
  },
  {
    id:          'normal',
    label:       '🔄 Normal Upgrade',
    color:       '#f59e0b',
    cr_id:       'CR-2024-0892',
    description: 'ServiceNow v8.2 platform upgrade — scheduled quarterly '
                 + 'version update affecting change management workflows.',
    system_criticality: 'high',
    change_type: 'normal',
    expected:    'HIGH Risk · Rigorous Scripted',
  },
  {
    id:          'config',
    label:       '⚙️ Config Change',
    color:       '#007FFF',
    cr_id:       'CR-2024-0893',
    description: 'Update change approval workflow routing rules — '
                 + 'approval threshold raised from 1 to 2 sign-offs.',
    system_criticality: 'medium',
    change_type: 'standard',
    expected:    'LOW Risk · Unscripted',
  },
  {
    id:          'routine',
    label:       '🔁 Routine Maintenance',
    color:       '#32CD32',
    cr_id:       'CR-2024-0894',
    description: 'Quarterly password rotation for shared service accounts '
                 + 'per IT security policy SOP-IT-004.',
    system_criticality: 'low',
    change_type: 'routine',
    expected:    'LOW Risk · Unscripted',
  },
]

const RISK_COLOR = { High: '#ef4444', Medium: '#f59e0b', Low: '#32CD32' }

function RiskBadge({ level }) {
  const color = RISK_COLOR[level] ?? '#007FFF'
  return (
    <div
      className="flex flex-col items-center justify-center rounded-2xl p-6"
      style={{
        background:  color + '18',
        border:      `2px solid ${color}40`,
        boxShadow:   `0 0 32px ${color}30`,
      }}
    >
      <span className="text-5xl font-black tracking-tight"
            style={{ color }}>
        {level?.toUpperCase()}
      </span>
      <span className="text-[11px] mt-1" style={{ color: color + 'cc' }}>
        RISK LEVEL
      </span>
    </div>
  )
}

function AuditEvent({ idx, action, timestamp }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: idx * 0.18 }}
      className="flex items-start gap-3 py-2.5 border-b border-border-base/40
                 last:border-0"
    >
      <span className="mt-0.5 shrink-0 w-5 h-5 rounded-full bg-lime-dim
                       border border-lime-DEFAULT/30 flex items-center
                       justify-center text-lime-DEFAULT text-[9px]">
        ✓
      </span>
      <div className="min-w-0">
        <p className="text-white text-[11px] font-mono">{action}</p>
        <p className="text-text-muted text-[10px] mt-0.5">
          {timestamp}
        </p>
      </div>
      <span className="ml-auto shrink-0 text-[9px] text-lime-DEFAULT border
                       border-lime-DEFAULT/30 bg-lime-dim rounded px-1.5 py-0.5">
        21 CFR §11
      </span>
    </motion.div>
  )
}

function ServiceNowDemoPanel() {
  const [form, setForm] = useState({
    cr_id:               'CR-2024-0891',
    description:         'Critical security patch — production LIMS system '
                         + 'requires immediate hotfix to address data integrity flaw.',
    system_criticality:  'critical',
    change_type:         'emergency',
  })
  const [loading,    setLoading]    = useState(false)
  const [result,     setResult]     = useState(null)
  const [apiError,   setApiError]   = useState(null)
  const [auditEvents, setAuditEvents] = useState([])

  const loadScenario = useCallback(scenario => {
    setForm({
      cr_id:              scenario.cr_id,
      description:        scenario.description,
      system_criticality: scenario.system_criticality,
      change_type:        scenario.change_type,
    })
    setResult(null)
    setApiError(null)
    setAuditEvents([])
  }, [])

  const submit = useCallback(async () => {
    setLoading(true)
    setResult(null)
    setApiError(null)
    setAuditEvents([])
    try {
      const res = await fetch(
        `${_EVOLV_API_BASE}/webhook/sn-change`,
        {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(form),
        }
      )
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(`API ${res.status}: ${txt}`)
      }
      const data = await res.json()
      setResult(data)
      // Simulate the two audit events that the API logs
      const ts = data.timestamp ?? new Date().toISOString()
      setAuditEvents([
        { action: 'CHANGE_REQUEST_RECEIVED',    timestamp: ts },
        { action: 'RISK_ASSESSMENT_COMPLETED',  timestamp: ts },
      ])
    } catch (err) {
      const msg = err.message ?? String(err)
      if (msg.includes('fetch') || msg.includes('Failed to fetch')
          || msg.includes('NetworkError') || msg.includes('ERR_CONNECTION')) {
        setApiError('api-offline')
      } else {
        setApiError(msg)
      }
    } finally {
      setLoading(false)
    }
  }, [form])

  const ra = result?.risk_assessment

  return (
    <div className="space-y-5">

      {/* Header */}
      <div>
        <h2 className="text-white font-semibold text-sm flex items-center gap-2">
          🛠️ ServiceNow Integration Demo
          <span className="text-[9px] text-lime-DEFAULT border border-lime-DEFAULT/30
                           bg-lime-dim rounded px-1.5 py-0.5 animate-pulse-lime">
            ● Native Webhook
          </span>
        </h2>
        <p className="text-text-secondary text-xs mt-1">
          Submit a mock Change Request → EVOLV assesses GAMP 5 risk in real time
          and logs a 21 CFR Part 11 audit trail.
        </p>
      </div>

      {/* Scenario quick-select */}
      <div>
        <p className="text-[10px] text-text-muted mb-2">Quick scenarios</p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {SN_SCENARIOS.map(s => (
            <button
              key={s.id}
              onClick={() => loadScenario(s)}
              className="text-left p-3 rounded-xl border border-border-base
                         hover:border-blue-DEFAULT/40 bg-bg-hover transition-all
                         group"
            >
              <p className="text-[11px] font-semibold text-white
                            group-hover:text-blue-DEFAULT transition-colors">
                {s.label}
              </p>
              <p className="text-[9px] text-text-muted mt-0.5 leading-relaxed">
                {s.cr_id}
              </p>
              <p className="text-[9px] mt-1" style={{ color: s.color }}>
                → {s.expected}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Form + Response side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">

        {/* Form */}
        <div className="glass rounded-xl p-4 space-y-3">
          <p className="text-[10px] text-text-muted font-semibold uppercase
                        tracking-wider">
            Change Request Payload
          </p>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              CR ID
            </label>
            <input
              value={form.cr_id}
              onChange={e => setForm(p => ({ ...p, cr_id: e.target.value }))}
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs font-mono text-text-primary outline-none
                         focus:border-border-blue transition-colors"
            />
          </div>

          <div>
            <label className="text-[10px] text-text-muted block mb-1">
              Description
            </label>
            <textarea
              rows={3}
              value={form.description}
              onChange={e =>
                setForm(p => ({ ...p, description: e.target.value }))
              }
              className="w-full bg-bg-base border border-border-base rounded-lg
                         px-3 py-2 text-xs text-text-primary outline-none
                         focus:border-border-blue transition-colors resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-text-muted block mb-1">
                System Criticality
              </label>
              <select
                value={form.system_criticality}
                onChange={e =>
                  setForm(p => ({ ...p, system_criticality: e.target.value }))
                }
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs text-text-primary outline-none
                           focus:border-border-blue transition-colors"
              >
                {['critical', 'high', 'medium', 'low', 'minor'].map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-text-muted block mb-1">
                Change Type
              </label>
              <select
                value={form.change_type}
                onChange={e =>
                  setForm(p => ({ ...p, change_type: e.target.value }))
                }
                className="w-full bg-bg-base border border-border-base rounded-lg
                           px-3 py-2 text-xs text-text-primary outline-none
                           focus:border-border-blue transition-colors"
              >
                {['emergency', 'normal', 'standard', 'routine'].map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={submit}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5
                       rounded-lg bg-blue-DEFAULT text-white text-xs font-bold
                       hover:brightness-110 disabled:opacity-50 transition-all
                       shadow-[0_0_20px_rgba(0,127,255,0.35)]"
          >
            {loading
              ? <><span className="animate-spin">⏳</span> Assessing…</>
              : '⚡ Submit to EVOLV'}
          </button>

          {/* JSON preview */}
          <details className="text-[10px]">
            <summary className="text-text-muted cursor-pointer hover:text-text-secondary
                                select-none">
              View raw payload
            </summary>
            <pre className="mt-2 bg-bg-base border border-border-base rounded-lg
                            p-3 text-text-secondary overflow-x-auto">
              {JSON.stringify(form, null, 2)}
            </pre>
          </details>
        </div>

        {/* Response */}
        <div className="space-y-4">
          <AnimatePresence mode="wait">

            {/* Idle state */}
            {!result && !apiError && !loading && (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="glass rounded-xl p-6 flex flex-col items-center
                           justify-center gap-3 min-h-[200px]"
              >
                <span className="text-4xl opacity-30">🛠️</span>
                <p className="text-text-muted text-xs text-center">
                  Select a scenario and click Submit to EVOLV.<br />
                  The risk assessment result appears here.
                </p>
              </motion.div>
            )}

            {/* Loading */}
            {loading && (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="glass rounded-xl p-6 flex flex-col items-center
                           justify-center gap-3 min-h-[200px]"
              >
                <div className="w-8 h-8 border-2 border-blue-DEFAULT/30
                                border-t-blue-DEFAULT rounded-full animate-spin" />
                <p className="text-text-muted text-xs">
                  EVOLV assessing GAMP 5 risk…
                </p>
              </motion.div>
            )}

            {/* API offline */}
            {apiError === 'api-offline' && (
              <motion.div
                key="offline"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="glass rounded-xl p-5 border border-amber-400/20
                           space-y-2"
              >
                <p className="text-amber-400 text-xs font-semibold">
                  ⚠ API server not reachable
                </p>
                <p className="text-text-muted text-[11px] leading-relaxed">
                  Start the FastAPI server to run a live demo:
                </p>
                <pre className="bg-bg-base border border-border-base rounded-lg
                                p-3 text-lime-DEFAULT text-[11px] font-mono">
                  uvicorn API.main:app --reload --port 8000
                </pre>
                <p className="text-text-muted text-[10px]">
                  The webhook endpoint is{' '}
                  <code className="text-blue-DEFAULT">
                    POST /webhook/sn-change
                  </code>
                </p>
              </motion.div>
            )}

            {/* Other error */}
            {apiError && apiError !== 'api-offline' && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="glass rounded-xl p-5 border border-red-400/20"
              >
                <p className="text-red-400 text-xs font-semibold mb-1">
                  ✗ Request failed
                </p>
                <p className="text-text-muted text-[11px] font-mono break-all">
                  {apiError}
                </p>
              </motion.div>
            )}

            {/* Result */}
            {result && ra && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                {/* Risk badge */}
                <RiskBadge level={ra.risk_level} />

                {/* Metrics grid */}
                <div className="glass rounded-xl p-4 grid grid-cols-3 gap-3
                                text-center">
                  {[
                    { label: 'RPN',          value: ra.rpn,           sub: '/ 27' },
                    { label: 'Severity',     value: ra.severity,      sub: '' },
                    { label: 'Occurrence',   value: ra.occurrence,    sub: '' },
                  ].map(({ label, value, sub }) => (
                    <div key={label}>
                      <p className="text-white text-lg font-bold">
                        {value}
                        {sub && (
                          <span className="text-text-muted text-[11px]">
                            {sub}
                          </span>
                        )}
                      </p>
                      <p className="text-text-muted text-[10px] mt-0.5">
                        {label}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Strategy + flags */}
                <div className="glass rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-text-muted">
                      CSA Strategy
                    </span>
                    <span className="text-xs text-white font-semibold">
                      {ra.testing_strategy}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-text-muted">
                      Detectability
                    </span>
                    <span className="text-xs text-white">{ra.detectability}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-text-muted">
                      Patient Safety Override
                    </span>
                    <span className={`text-xs font-semibold ${
                      ra.patient_safety_override
                        ? 'text-red-400' : 'text-lime-DEFAULT'
                    }`}>
                      {ra.patient_safety_override ? '⚠ YES' : '✓ No'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-1
                                  border-t border-border-base/50">
                    <span className="text-[10px] text-text-muted">
                      Reasoning hash
                    </span>
                    <code className="text-[9px] text-blue-DEFAULT font-mono">
                      {result.message?.slice(0, 32) ?? result.cr_id}…
                    </code>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Audit trail feed */}
          {auditEvents.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass rounded-xl p-4"
            >
              <p className="text-[10px] text-text-muted font-semibold uppercase
                            tracking-wider mb-3">
                21 CFR Part 11 Audit Events
              </p>
              {auditEvents.map((ev, i) => (
                <AuditEvent
                  key={ev.action}
                  idx={i}
                  action={ev.action}
                  timestamp={ev.timestamp}
                />
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main DevPortal component ───────────────────────────────────

export default function DevPortal() {
  const [activeTab, setActiveTab] = useState('sn-demo')

  const tabs = [
    { id: 'sn-demo', label: '🛠️ ServiceNow Demo' },
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
        {activeTab === 'sn-demo'  && <ServiceNowDemoPanel />}
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
