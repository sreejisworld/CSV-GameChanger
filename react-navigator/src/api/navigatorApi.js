/**
 * navigatorApi.js — Thin fetch wrapper for the EVOLV
 * Project Navigator FastAPI endpoints.
 *
 * All functions return parsed JSON or throw an Error with
 * a human-readable message on HTTP failure.
 *
 * Base URL is relative (/api/...) so the Vite dev proxy
 * forwards to http://localhost:8000 automatically.
 * In production the React build is served from the same
 * FastAPI origin, so no proxy is needed.
 */

const BASE = '/api/navigator'

// ── Helpers ───────────────────────────────────────────────────

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[${res.status}] ${text || res.statusText}`)
  }
  // 204 No Content — return null
  if (res.status === 204) return null
  return res.json()
}

const get  = path           => request(path)
const post = (path, body)   => request(path, { method: 'POST',   body: JSON.stringify(body) })
const patch = (path, body)  => request(path, { method: 'PATCH',  body: JSON.stringify(body) })
const del  = (path, body)   => request(path, { method: 'DELETE', body: JSON.stringify(body) })


// ── Projects ──────────────────────────────────────────────────

/** List all projects (summary). */
export const listProjects = () => get('/projects')

/** Get full project tree (with all releases + folder items). */
export const getProject = id => get(`/projects/${id}`)

/** Create a project. */
export const createProject = payload => post('/projects', payload)

/** Delete a project. */
export const deleteProject = id => del(`/projects/${id}`)


// ── Releases ──────────────────────────────────────────────────

/**
 * Create a release inside a project.
 * @param {string} projectId
 * @param {{ name, version, description?, status?, folder_template? }} payload
 */
export const createRelease = (projectId, payload) =>
  post(`/projects/${projectId}/releases`, payload)

/**
 * Update a release's lifecycle status.
 * @param {string} projectId
 * @param {string} releaseId
 * @param {string} status  e.g. "Released"
 */
export const updateReleaseStatus = (projectId, releaseId, status) =>
  patch(
    `/projects/${projectId}/releases/${releaseId}/status`,
    { status },
  )


// ── Items ─────────────────────────────────────────────────────

/**
 * Add an item to a release folder.
 * @param {string} projectId
 * @param {string} releaseId
 * @param {{ folder, name, item_type?, artifact_id?, notes?, status? }} payload
 */
export const addItem = (projectId, releaseId, payload) =>
  post(`/projects/${projectId}/releases/${releaseId}/items`, payload)

/**
 * HITL-approve an item (FDA AI Guidance 2026 §3.2).
 * Logs HITL_APPROVAL event to 21 CFR Part 11 audit trail.
 * @param {string} projectId
 * @param {string} releaseId
 * @param {string} itemId
 * @param {string} folder   folder name the item lives in
 */
export const approveItem = (projectId, releaseId, itemId, folder) =>
  patch(
    `/projects/${projectId}/releases/${releaseId}/items/${itemId}/approve`,
    { folder },
  )

/**
 * Move an item between folders / releases.
 * @param {string} projectId
 * @param {string} releaseId  source release
 * @param {string} itemId
 * @param {{ src_folder, dst_release_id, dst_folder }} payload
 */
export const moveItem = (projectId, releaseId, itemId, payload) =>
  post(
    `/projects/${projectId}/releases/${releaseId}/items/${itemId}/move`,
    payload,
  )

/**
 * Delete an item from a folder.
 * @param {string} projectId
 * @param {string} releaseId
 * @param {string} itemId
 * @param {string} folder
 */
export const deleteItem = (projectId, releaseId, itemId, folder) =>
  del(
    `/projects/${projectId}/releases/${releaseId}/items/${itemId}`,
    { folder },
  )


// ── Global Library ────────────────────────────────────────────

/** List Global Library entries, optionally filtered by entry_type. */
export const listLibrary = (entryType) => {
  const qs = entryType ? `?entry_type=${entryType}` : ''
  return get(`/library${qs}`)
}

/** Add a Global Library entry. */
export const addLibraryEntry = payload => post('/library', payload)

/** Delete a Global Library entry. */
export const deleteLibraryEntry = id => del(`/library/${id}`)
