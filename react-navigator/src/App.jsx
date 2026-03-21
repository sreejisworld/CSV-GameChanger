/**
 * App — root layout.
 *
 * useProjectStore is called HERE (single instance) so the live tree
 * is shared between the sidebar and all view components.
 *
 * Left:   ProjectNavigator sidebar (fixed 288px)
 * Center: MainContent — Framer Motion view router
 * Right:  AgenticSidebar — Evolv Reasoning panel (auto-shown)
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { AnimatePresence, motion }        from 'framer-motion'
import ProjectNavigator                    from './components/ProjectNavigator.jsx'
import MainContent                         from './components/MainContent.jsx'
import AgenticSidebar                      from './components/AgenticSidebar.jsx'
import { useProjectStore }                 from './hooks/useProjectStore.js'

// ── Folder name → view id ─────────────────────────────────────────
const FOLDER_VIEW_MAP = {
  'URS':                  'urs',
  'Risk Matrix':          'risk',
  'Test Scripts':         'test',
  'Traceability':         'traceability',
  'Traceability Matrix':  'traceability',
  'Functional Specs':     'frs',
  'Supplier Assessment':  'supplier',
  'VSR':                  'vsr',
  dashboard:              'dashboard',
}

// ── Agentic continuity messages ───────────────────────────────────
const AGENTIC_HINTS = {
  'urs->test': {
    icon: '🧪',
    message: "I noticed you finished the URS. I've drafted test scripts based on your requirements.",
    action: 'Review Test Scripts',
    thoughts: [
      'Analysing approved requirements...',
      'Mapping SMART acceptance criteria to OQ steps...',
      'Applying CSA testing strategy (High risk → Formal OQ)...',
      'Generating test script skeletons...',
    ],
  },
  'urs->traceability': {
    icon: '🔗',
    message: "Requirements are ready. I've built the initial trace matrix linking each URS to its test script.",
    action: 'View Trace Matrix',
    thoughts: [
      'Indexing URS nodes...',
      'Resolving shadow links in Traceability folder...',
      'Calculating coverage gaps...',
    ],
  },
  'test->vsr': {
    icon: '📄',
    message: "All test scripts are present. I've pre-filled the VSR cover page — just add your signature.",
    action: 'Open VSR',
    thoughts: [
      'Aggregating test execution results...',
      'Checking for open issues...',
      'Drafting VSR summary table...',
    ],
  },
  'risk->urs': {
    icon: '📋',
    message: "Risk assessment complete. I've flagged requirements that may need criticality upgrades based on your RPN scores.",
    action: 'Review Requirements',
    thoughts: [
      'Cross-referencing RPN scores with URS criticality...',
      'Detecting under-classified requirements...',
    ],
  },
}

export default function App() {
  // ── Single store instance shared across sidebar + views ───────
  const store = useProjectStore()

  const [currentView,  setCurrentView]  = useState('dashboard')
  const [selectedNode, setSelectedNode] = useState(null)
  const [breadcrumb,   setBreadcrumb]   = useState([])
  const [agenticHint,  setAgenticHint]  = useState(null)
  const prevViewRef = useRef('dashboard')

  // ── EVOLV Platform context (received via postMessage) ─────────
  const [evolvContext, setEvolvContext] = useState({
    projectName: '', gampCategory: '', phaseCompletion: {},
  })

  useEffect(() => {
    const handler = e => {
      if (e.data?.type === 'EVOLV_CONTEXT') {
        setEvolvContext(e.data.payload)
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  const handleFolderSelect = useCallback((node, path) => {
    const viewId = FOLDER_VIEW_MAP[node.name] || 'dashboard'
    const prev   = prevViewRef.current
    const hintKey = `${prev}->${viewId}`
    setAgenticHint(AGENTIC_HINTS[hintKey] || null)
    prevViewRef.current = viewId
    setCurrentView(viewId)
    setSelectedNode(node)
    setBreadcrumb(path || [])
  }, [])

  const dismissHint = useCallback(() => setAgenticHint(null), [])
  const showSidebar = Boolean(agenticHint)

  return (
    <div className="flex h-screen bg-workspace text-white overflow-hidden
                    font-sans antialiased">

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <ProjectNavigator
        store={store}
        onFolderSelect={handleFolderSelect}
        currentView={currentView}
        evolvContext={evolvContext}
      />

      {/* ── Main stage ──────────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">

        <TopBar breadcrumb={breadcrumb} currentView={currentView} />

        <div className="flex flex-1 min-h-0 overflow-hidden">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={currentView}
              initial={{ opacity: 0, x: 32 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{    opacity: 0, x: -24 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
              className="flex-1 overflow-y-auto min-w-0"
            >
              <MainContent
                view={currentView}
                node={selectedNode}
                breadcrumb={breadcrumb}
                tree={store.tree}
              />
            </motion.div>
          </AnimatePresence>

          {/* ── Agentic sidebar (slide in from right) ────────── */}
          <AnimatePresence>
            {showSidebar && (
              <motion.div
                key="agentic-sidebar"
                initial={{ opacity: 0, x: 280, width: 0 }}
                animate={{ opacity: 1, x: 0,   width: 280 }}
                exit={{    opacity: 0, x: 280,  width: 0 }}
                transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                className="overflow-hidden shrink-0 border-l border-white/5"
              >
                <AgenticSidebar
                  hint={agenticHint}
                  onDismiss={dismissHint}
                  currentView={currentView}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

// ── Top bar ────────────────────────────────────────────────────────
const VIEW_LABELS = {
  dashboard:    'Dashboard',
  urs:          'User Requirements (URS)',
  risk:         'Risk Assessment',
  test:         'Test Scripts',
  traceability: 'Traceability Matrix',
  frs:          'Functional Specifications',
  vsr:          'Validation Summary Report',
  supplier:     'Supplier Assessment',
}

function TopBar({ breadcrumb, currentView }) {
  const projectName = breadcrumb[0]?.name || 'LabCore LIMS v4.2'
  const versionName = breadcrumb.find(b => b.type === 'release')?.name
  const viewLabel   = VIEW_LABELS[currentView] || 'Dashboard'

  return (
    <div className="sticky top-0 z-20 shrink-0
                    bg-navy-900/80 backdrop-blur-md
                    border-b border-white/5
                    px-6 py-3 flex items-center justify-between gap-4">
      <nav className="flex items-center gap-1.5 text-xs min-w-0 overflow-hidden">
        <span className="text-muted truncate shrink-0">{projectName}</span>
        {versionName && (
          <>
            <span className="text-white/20 shrink-0">›</span>
            <span className="text-muted truncate shrink-0">{versionName}</span>
          </>
        )}
        <span className="text-white/20 shrink-0">›</span>
        <span className="text-white font-semibold truncate">{viewLabel}</span>
      </nav>
      <div className="flex items-center gap-2 shrink-0">
        {['21 CFR Part 11 ✓', 'GAMP 5 ✓', 'FDA AI 2026 ✓'].map(b => (
          <span key={b}
            className="text-[10px] bg-navy-700/60 border border-white/8
                       text-muted rounded px-2 py-0.5 backdrop-blur-sm">
            {b}
          </span>
        ))}
      </div>
    </div>
  )
}
