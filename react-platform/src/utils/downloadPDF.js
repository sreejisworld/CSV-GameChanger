/**
 * Shared helper for POSTing a JSON body to a FastAPI endpoint
 * that returns ``application/pdf`` and triggering a browser
 * download of the resulting blob.
 *
 * Used by Plan / Design / Release phase pages to pull signed
 * Validation Factory deliverables (VP, DS, VSR) from the
 * /exports/* router.
 *
 * @param {string} url       Full endpoint URL.
 * @param {object} body      JSON-serialisable request payload.
 * @param {string} filename  Suggested filename for the download.
 * @throws Error if the response is not 2xx; the FastAPI
 *   ``detail`` string is preserved as ``error.message`` so the
 *   caller can surface it in an inline error banner.
 */
export async function downloadPDF(url, body, filename) {
  const res = await fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  const blob = await res.blob()
  const burl = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = burl
  a.download = filename
  a.click()
  URL.revokeObjectURL(burl)
}

/** Filesystem-safe ASCII slug for use in filenames. */
export function slugify(name) {
  return (
    String(name || '')
      .replace(/[^a-zA-Z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .toLowerCase()
  ) || 'project'
}
