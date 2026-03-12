/**
 * useTabManager — manages open tabs in the Platform Shell.
 *
 * Rules:
 *  - 'home' tab is always open and cannot be closed.
 *  - Opening an app that already has a tab switches to it.
 *  - Maximum 8 tabs open simultaneously.
 *  - Tab order is preserved; new tabs are appended.
 */
import { useState, useCallback } from 'react'

const MAX_TABS = 8

export function useTabManager() {
  const [tabs, setTabs]           = useState([{ appId: 'home' }])
  const [activeTabId, setActive]  = useState('home')

  const openTab = useCallback(appId => {
    setTabs(prev => {
      const exists = prev.find(t => t.appId === appId)
      if (exists) return prev
      if (prev.length >= MAX_TABS) return prev   // silently cap
      return [...prev, { appId }]
    })
    setActive(appId)
  }, [])

  const closeTab = useCallback((appId, allTabs) => {
    if (appId === 'home') return  // home is pinned
    setTabs(prev => {
      const idx  = prev.findIndex(t => t.appId === appId)
      const next = prev.filter(t => t.appId !== appId)
      // If we closed the active tab, switch to neighbour
      if (activeTabId === appId && next.length > 0) {
        const newIdx = Math.min(idx, next.length - 1)
        setActive(next[newIdx].appId)
      }
      return next
    })
  }, [activeTabId])

  const switchTab = useCallback(appId => {
    setActive(appId)
  }, [])

  return { tabs, activeTabId, openTab, closeTab, switchTab }
}
