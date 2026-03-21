/**
 * TraceabilityView — force-directed node-link graph.
 *
 * Graph is built from the live tree when available,
 * falling back to traceabilityMap mock data.
 */
import { useEffect, useRef, useState } from 'react'
import { buildTraceGraph } from '../../utils/treeHelpers.js'
import {
  requirements, testScripts, risks,
} from '../../data/traceabilityMap.js'

const NODE_COLOR = { req: '#3b82f6', test: '#a855f7', risk: '#f87171' }

const STATUS_GLOW = {
  failed:     '#f87171',
  open_issue: '#f0a500',
  approved:   '#22c55e',
  in_review:  '#f0a500',
  draft:      '#94a3b8',
}

// Build mock graph from traceabilityMap (demo fallback)
function buildMockGraph() {
  const nodes = [
    ...requirements.map(r => ({ id: r.id, label: r.id, type: 'req',  full: r.title, status: r.status })),
    ...testScripts.map(t  => ({ id: t.id, label: t.id, type: 'test', full: t.title, status: t.status })),
    ...risks.map(rk       => ({ id: rk.id, label: rk.id, type: 'risk', full: rk.title })),
  ]
  const edges = []
  requirements.forEach(r => {
    r.upstream.forEach(rid  => edges.push({ source: rid, target: r.id }))
    r.downstream.forEach(tid => edges.push({ source: r.id, target: tid }))
  })
  return { nodes, edges }
}

function useForceGraph(canvasRef, { width, height }, graphData) {
  const stateRef = useRef(null)
  const rafRef   = useRef(null)
  const [selected, setSelected] = useState(null)
  const [tooltip,  setTooltip]  = useState(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !graphData) return
    const ctx = canvas.getContext('2d')
    canvas.width  = width
    canvas.height = height

    const { nodes, edges } = graphData
    if (!nodes.length) return

    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI
      const r = Math.min(width, height) * 0.3
      n.x = width  / 2 + r * Math.cos(angle)
      n.y = height / 2 + r * Math.sin(angle)
      n.vx = 0; n.vy = 0
    })

    const nodeMap = {}
    nodes.forEach(n => { nodeMap[n.id] = n })

    function tick() {
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j]
          const dx = b.x - a.x, dy = b.y - a.y
          const dist = Math.sqrt(dx*dx + dy*dy) || 1
          const force = 1200 / (dist * dist)
          const fx = (dx/dist)*force, fy = (dy/dist)*force
          a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy
        }
      }
      edges.forEach(e => {
        const s = nodeMap[e.source], t = nodeMap[e.target]
        if (!s || !t) return
        const dx = t.x-s.x, dy = t.y-s.y
        const dist = Math.sqrt(dx*dx+dy*dy) || 1
        const force = (dist-80) * 0.04
        const fx = (dx/dist)*force, fy = (dy/dist)*force
        s.vx += fx; s.vy += fy; t.vx -= fx; t.vy -= fy
      })
      nodes.forEach(n => {
        n.vx += (width/2  - n.x) * 0.003
        n.vy += (height/2 - n.y) * 0.003
        n.vx *= 0.85; n.vy *= 0.85
        n.x += n.vx; n.y += n.vy
      })
    }

    for (let i = 0; i < 120; i++) tick()

    stateRef.current = { nodes, edges, nodeMap, selectedId: null, hoverId: null }

    function draw() {
      ctx.clearRect(0, 0, width, height)
      const { nodes: ns, edges: es, selectedId, hoverId } = stateRef.current
      const connectedIds = new Set()
      if (selectedId) {
        es.forEach(e => {
          if (e.source === selectedId) connectedIds.add(e.target)
          if (e.target === selectedId) connectedIds.add(e.source)
        })
        connectedIds.add(selectedId)
      }
      es.forEach(e => {
        const s = nodeMap[e.source], t = nodeMap[e.target]
        if (!s || !t) return
        const hi = selectedId && (e.source===selectedId || e.target===selectedId)
        ctx.beginPath()
        ctx.moveTo(s.x, s.y)
        ctx.lineTo(t.x, t.y)
        ctx.strokeStyle = hi ? '#32CD32' : 'rgba(255,255,255,0.06)'
        ctx.lineWidth   = hi ? 2 : 1
        ctx.shadowBlur  = hi ? 8 : 0
        ctx.shadowColor = '#32CD32'
        ctx.stroke()
        ctx.shadowBlur = 0
      })
      ns.forEach(n => {
        const isSel  = n.id === selectedId
        const isCon  = connectedIds.has(n.id)
        const isHov  = n.id === hoverId
        const dimmed = selectedId && !isCon
        const r = isSel ? 10 : isHov ? 9 : 7
        if (isSel) {
          ctx.beginPath()
          ctx.arc(n.x, n.y, r+6, 0, Math.PI*2)
          ctx.fillStyle = 'rgba(50,205,50,0.2)'
          ctx.fill()
        }
        ctx.beginPath()
        ctx.arc(n.x, n.y, r, 0, Math.PI*2)
        ctx.fillStyle = dimmed ? 'rgba(255,255,255,0.08)' : isSel ? '#32CD32' : NODE_COLOR[n.type]
        ctx.globalAlpha = dimmed ? 0.25 : 1
        ctx.fill()
        ctx.globalAlpha = 1
        if (!dimmed && n.status && STATUS_GLOW[n.status]) {
          ctx.beginPath()
          ctx.arc(n.x, n.y, r+2.5, 0, Math.PI*2)
          ctx.strokeStyle = STATUS_GLOW[n.status]
          ctx.lineWidth = 1.5
          ctx.globalAlpha = 0.6
          ctx.stroke()
          ctx.globalAlpha = 1
        }
        if (!dimmed) {
          ctx.font = `${isSel ? 'bold ' : ''}9px monospace`
          ctx.fillStyle = isSel ? '#32CD32' : 'rgba(255,255,255,0.7)'
          ctx.textAlign = 'center'
          ctx.fillText(n.label, n.x, n.y+r+11)
        }
      })
    }

    function loop() {
      tick()
      draw()
      rafRef.current = requestAnimationFrame(loop)
    }
    rafRef.current = requestAnimationFrame(loop)

    const getNode = (mx, my) =>
      stateRef.current.nodes.find(n => {
        const dx=n.x-mx, dy=n.y-my
        return Math.sqrt(dx*dx+dy*dy) < 14
      })

    const onMove = e => {
      const rect = canvas.getBoundingClientRect()
      const n = getNode(e.clientX-rect.left, e.clientY-rect.top)
      stateRef.current.hoverId = n?.id || null
      canvas.style.cursor = n ? 'pointer' : 'default'
      setTooltip(n ? { x: e.clientX-rect.left, y: e.clientY-rect.top, node: n } : null)
    }

    const onClick = e => {
      const rect = canvas.getBoundingClientRect()
      const n = getNode(e.clientX-rect.left, e.clientY-rect.top)
      const newId = n ? (stateRef.current.selectedId === n.id ? null : n.id) : null
      stateRef.current.selectedId = newId
      setSelected(newId)
    }

    canvas.addEventListener('mousemove', onMove)
    canvas.addEventListener('click', onClick)
    return () => {
      cancelAnimationFrame(rafRef.current)
      canvas.removeEventListener('mousemove', onMove)
      canvas.removeEventListener('click', onClick)
    }
  }, [width, height, graphData])

  return { selected, tooltip }
}

export default function TraceabilityView({ node, tree }) {
  const canvasRef    = useRef(null)
  const containerRef = useRef(null)
  const [size, setSize] = useState({ width: 800, height: 520 })

  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(([e]) => {
      setSize({ width: e.contentRect.width, height: 520 })
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  // Use live tree graph if available, else mock
  const graphData = tree
    ? buildTraceGraph(tree)
    : buildMockGraph()

  // Has live data if tree has items
  const isLive = graphData.nodes.length > 0

  const { selected, tooltip } = useForceGraph(canvasRef, size, isLive ? graphData : buildMockGraph())

  // Full lookup map for tooltip enrichment
  const nodeMap = {}
  ;[...requirements, ...testScripts, ...risks].forEach(n => {
    nodeMap[n.id] = n
  })
  // Also add tree nodes
  graphData.nodes.forEach(n => {
    if (!nodeMap[n.id]) nodeMap[n.id] = { title: n.full }
  })

  return (
    <div className="p-8">
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-widest text-accent mb-1">Traceability</p>
        <h2 className="text-xl font-bold text-white tracking-tight">Traceability Web</h2>
        <p className="text-sm text-muted mt-1">
          {graphData.nodes.length} nodes · {graphData.edges.length} links ·
          Click any node to highlight connections
        </p>
      </div>

      <div className="flex items-center gap-5 mb-4 text-[11px]">
        {[
          { color: '#3b82f6', label: 'Requirement' },
          { color: '#a855f7', label: 'Test Script'  },
          { color: '#f87171', label: 'Risk'          },
        ].map(l => (
          <span key={l.label} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full inline-block" style={{ background: l.color }}/>
            <span className="text-white/60">{l.label}</span>
          </span>
        ))}
        <span className="flex items-center gap-1.5 ml-2">
          <span className="w-3 h-3 rounded-full inline-block bg-lime"/>
          <span className="text-white/60">Selected / Link</span>
        </span>
      </div>

      <div ref={containerRef}
        className="relative rounded-2xl border border-white/5 overflow-hidden bg-navy-950">
        <canvas ref={canvasRef} className="block" />
        {tooltip && (
          <div className="absolute pointer-events-none z-10 max-w-xs
                          bg-navy-800/95 border border-white/10 rounded-xl
                          px-3 py-2 text-xs shadow-card-md backdrop-blur-sm"
            style={{ left: tooltip.x+14, top: tooltip.y-10 }}>
            <p className="font-mono text-accent text-[10px]">{tooltip.node.id}</p>
            <p className="text-white/75 mt-0.5 leading-snug">{tooltip.node.full}</p>
            {tooltip.node.status && (
              <p className="text-muted text-[10px] mt-1 capitalize">
                {tooltip.node.status.replace('_', ' ')}
              </p>
            )}
          </div>
        )}
      </div>

      {selected && (
        <div className="mt-4 p-4 rounded-2xl bg-lime/5 border border-lime/20">
          <p className="text-[10px] uppercase tracking-widest text-lime mb-1">Selected</p>
          <p className="text-sm font-semibold text-white">{selected}</p>
          <p className="text-xs text-white/60 mt-0.5">
            {nodeMap[selected]?.title || nodeMap[selected]?.full || ''}
          </p>
        </div>
      )}
    </div>
  )
}
