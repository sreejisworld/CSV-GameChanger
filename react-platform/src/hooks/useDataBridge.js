/**
 * useDataBridge — global Streamlit ↔ React data sync.
 *
 * Polls FastAPI endpoints every POLL_MS milliseconds and writes
 * fresh data into the Zustand store so all React pages stay in sync
 * with anything generated or saved in Streamlit.
 *
 * Endpoints polled:
 *   GET /requirements  — UR/FR list saved by Streamlit Requirements page
 *   GET /plan          — Plan metadata saved by Streamlit Plan page
 *
 * Mount once in App.jsx — no props needed.
 */
import { useEffect, useRef } from 'react'
import { useAppStore }       from '../store/useAppStore.js'
import { API_BASE } from '../config.js'

const API     = API_BASE
const POLL_MS = 10_000   // 10 seconds

export function useDataBridge() {
  const {
    requirements,   setRequirements,
    planData,       setPlanData,
    setBridgeMeta,
  } = useAppStore()

  const prevReqCount = useRef(requirements.length)

  useEffect(() => {
    let active = true

    // ── Poll requirements ────────────────────────────────────────
    const pollRequirements = async () => {
      try {
        const res = await fetch(`${API}/requirements`)
        if (!res.ok || !active) return
        const data = await res.json()
        const reqs = data.requirements ?? []
        if (reqs.length > 0 && reqs.length !== prevReqCount.current) {
          setRequirements(reqs)
          prevReqCount.current = reqs.length
        }
        if (reqs.length > 0 && active) {
          setBridgeMeta({
            reqCount:  reqs.length,
            reqSyncAt: data.saved_at ?? new Date().toISOString(),
          })
        }
      } catch { /* FastAPI not running — silently skip */ }
    }

    // ── Poll plan data ───────────────────────────────────────────
    const pollPlan = async () => {
      try {
        const res = await fetch(`${API}/plan`)
        if (!res.ok || !active) return
        const data = await res.json()
        if (!data.plan || !data.plan.projectName) return
        // Only sync fields that Streamlit actually set (don't overwrite React edits)
        const p = data.plan
        if (p.projectName  && p.projectName  !== planData.projectName)
          setPlanData('projectName',  p.projectName)
        if (p.gampCategory && p.gampCategory !== planData.gampCategory)
          setPlanData('gampCategory', p.gampCategory)
        if (p.systemDescription && p.systemDescription !== planData.systemDescription)
          setPlanData('systemDescription', p.systemDescription)
      } catch { /* FastAPI not running — silently skip */ }
    }

    // Run immediately, then on interval
    pollRequirements()
    pollPlan()
    const id = setInterval(() => {
      pollRequirements()
      pollPlan()
    }, POLL_MS)

    return () => { active = false; clearInterval(id) }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Expose a manual trigger for the Plan.jsx "Sync" button
  return {
    syncNow: async () => {
      try {
        const res = await fetch(`${API}/plan`)
        if (!res.ok) return null
        const data = await res.json()
        return data.plan ?? null
      } catch { return null }
    },
  }
}
