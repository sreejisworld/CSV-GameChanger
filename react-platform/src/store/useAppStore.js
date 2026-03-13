/**
 * useAppStore — Zustand global store for the EVOLV Platform Shell.
 *
 * Responsibilities:
 *  - Tab management (open / close / switch, max 8 tabs, home pinned)
 *  - Draft state per app (text survives tab switches and re-opens)
 *  - Status badges per app (red/amber/green dot shown in Sidebar)
 */
import { create } from 'zustand'

const MAX_TABS = 8

// Initial status badges — demo data so the feature is visible on load
const INITIAL_BADGES = {
  'home':               null,
  'validation-factory': { type: 'warning', label: '1 risk pending' },
  'navigator':          null,
  'dev-portal':         null,
  'config':             null,
  'academy':            null,
  'impact-analytics':   null,
}

export const useAppStore = create((set, get) => ({
  // ── Tab state ──────────────────────────────────────────────
  tabs:        [{ appId: 'home' }],
  activeTabId: 'home',

  openTab: appId => set(state => {
    const exists = state.tabs.find(t => t.appId === appId)
    return {
      tabs: exists
        ? state.tabs
        : state.tabs.length >= MAX_TABS
          ? state.tabs
          : [...state.tabs, { appId }],
      activeTabId: appId,
    }
  }),

  closeTab: appId => set(state => {
    if (appId === 'home') return {}
    const idx  = state.tabs.findIndex(t => t.appId === appId)
    const next = state.tabs.filter(t => t.appId !== appId)
    const newActive =
      state.activeTabId === appId && next.length > 0
        ? next[Math.min(idx, next.length - 1)].appId
        : state.activeTabId
    return { tabs: next, activeTabId: newActive }
  }),

  switchTab: appId => set({ activeTabId: appId }),

  // ── Draft state ────────────────────────────────────────────
  // Per-app key-value bag.  Components read/write here so draft
  // survives tab switches, tab close+reopen, and Framer unmounts.
  drafts: {
    'academy':            { sandboxInput: '' },
    'validation-factory': {},
    'dev-portal':         {},
  },

  setDraft: (appId, key, value) => set(state => ({
    drafts: {
      ...state.drafts,
      [appId]: { ...(state.drafts[appId] ?? {}), [key]: value },
    },
  })),

  getDraft: (appId, key, fallback = '') => {
    return get().drafts[appId]?.[key] ?? fallback
  },

  // ── Status badges ──────────────────────────────────────────
  // type: 'error' | 'warning' | 'success' | 'info'
  statusBadges: INITIAL_BADGES,

  setStatusBadge: (appId, badge) => set(state => ({
    statusBadges: { ...state.statusBadges, [appId]: badge },
  })),

  clearStatusBadge: appId => set(state => ({
    statusBadges: { ...state.statusBadges, [appId]: null },
  })),
}))
