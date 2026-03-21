"""Traceability Spider-Web Chart — interactive SVG/Canvas network.

Renders a force-directed network graph where:
  · Blue nodes   = Requirements (URS)
  · Purple nodes = Test Scripts (TS)
  · Red nodes    = Risk items

Clicking any node highlights all connected nodes and edges in
Cyber Lime (#32CD32).  The graph self-organises via a Verlet
force simulation written in vanilla JS (no D3 dependency).

Usage::

    from components.traceability_web import traceability_web

    traceability_web(
        nodes=[
            {"id": "URS-1.1", "label": "Accept CRs",    "type": "req"},
            {"id": "URS-2.1", "label": "Audit Trail",   "type": "req"},
            {"id": "TS-1.1",  "label": "Test CR accept","type": "test"},
            {"id": "RISK-001","label": "Emergency CR",  "type": "risk"},
        ],
        edges=[
            {"source": "URS-1.1", "target": "TS-1.1"},
            {"source": "URS-1.1", "target": "RISK-001"},
            {"source": "URS-2.1", "target": "TS-1.1"},
        ],
        height=480,
    )

:requirement: URS-7.3 - Traceability matrix visualisation.
"""

from __future__ import annotations
import json
import streamlit.components.v1 as components


_NODE_COLORS: dict[str, str] = {
    "req":  "#056696",   # EV Blue
    "test": "#7C3AED",   # Purple
    "risk": "#B94E4E",   # Red
    "vsr":  "#488421",   # Green
}
_NODE_LABELS: dict[str, str] = {
    "req":  "Requirement",
    "test": "Test Script",
    "risk": "Risk Item",
    "vsr":  "VSR Entry",
}


def traceability_web(
    nodes: list[dict],
    edges: list[dict],
    height: int = 480,
    title: str = "Traceability Web",
) -> None:
    """Render the interactive Spider-Web traceability chart.

    :param nodes: List of node dicts::

        {"id": str, "label": str, "type": "req"|"test"|"risk"|"vsr"}

    :param edges: List of edge dicts::

        {"source": str, "target": str}

    :param height: Component height in pixels.
    :param title: Chart title shown in the legend area.
    :requirement: URS-7.3 - Traceability matrix visualisation.
    """
    nodes_js = json.dumps(nodes)
    edges_js = json.dumps(edges)
    colors_js = json.dumps(_NODE_COLORS)
    labels_js = json.dumps(_NODE_LABELS)

    components.html(
        f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', 'Geist', system-ui, sans-serif;
    background: transparent;
    overflow: hidden;
  }}
  #wrap {{
    position: relative;
    width: 100%;
    height: {height}px;
    background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 100%);
    border-radius: 14px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
    overflow: hidden;
  }}
  canvas {{
    display: block;
    width: 100%;
    height: 100%;
  }}
  /* Legend */
  #legend {{
    position: absolute;
    top: 14px;
    left: 16px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    pointer-events: none;
  }}
  .legend-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: #64748B;
    margin-bottom: 2px;
  }}
  .legend-row {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #334155;
    font-weight: 500;
  }}
  .legend-dot {{
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  /* Tooltip */
  #tooltip {{
    position: absolute;
    background: #1E293B;
    color: #F1F5F9;
    border-radius: 7px;
    padding: 5px 10px;
    font-size: 12px;
    font-weight: 500;
    pointer-events: none;
    display: none;
    max-width: 180px;
    line-height: 1.4;
    box-shadow: 0 4px 12px rgba(0,0,0,.25);
    border: 1px solid rgba(255,255,255,.10);
    z-index: 10;
  }}
  /* Empty state */
  #empty {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #94A3B8;
    gap: 8px;
    font-size: 13px;
    font-weight: 500;
  }}
  .empty-icon {{ font-size: 32px; opacity: .4; }}
  /* Click hint */
  #hint {{
    position: absolute;
    bottom: 12px;
    right: 14px;
    font-size: 10px;
    color: #94A3B8;
    pointer-events: none;
  }}
</style>
</head>
<body>
<div id="wrap">
  <canvas id="c"></canvas>
  <div id="legend">
    <div class="legend-title">{title}</div>
  </div>
  <div id="tooltip"></div>
  <div id="empty" style="display:none">
    <span class="empty-icon">🕸</span>
    <span>No traceability data yet.</span>
    <span style="font-size:11px;opacity:.7">
      Generate requirements and test scripts to see connections.
    </span>
  </div>
  <div id="hint">Click a node to highlight connections</div>
</div>

<script>
(function() {{
  var RAW_NODES  = {nodes_js};
  var RAW_EDGES  = {edges_js};
  var COLORS     = {colors_js};
  var TYPE_LABELS= {labels_js};
  var LIME       = '#32CD32';

  var wrap    = document.getElementById('wrap');
  var canvas  = document.getElementById('c');
  var ctx     = canvas.getContext('2d');
  var tooltip = document.getElementById('tooltip');
  var legend  = document.getElementById('legend');
  var empty   = document.getElementById('empty');

  if (!RAW_NODES.length) {{
    canvas.style.display = 'none';
    empty.style.display  = 'flex';
    return;
  }}

  // ── Build legend ────────────────────────────────────────────
  var seenTypes = {{}};
  RAW_NODES.forEach(function(n) {{ seenTypes[n.type] = true; }});
  Object.keys(seenTypes).forEach(function(t) {{
    var row = document.createElement('div');
    row.className = 'legend-row';
    row.innerHTML =
      '<span class="legend-dot" style="background:'
      + (COLORS[t] || '#888') + '"></span>'
      + (TYPE_LABELS[t] || t);
    legend.appendChild(row);
  }});

  // ── DPI-aware canvas sizing ──────────────────────────────────
  function resize() {{
    var dpr = window.devicePixelRatio || 1;
    var w   = wrap.clientWidth;
    var h   = wrap.clientHeight;
    canvas.width  = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width  = w + 'px';
    canvas.style.height = h + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return {{ w: w, h: h }};
  }}

  var dim = resize();
  var cx  = dim.w / 2;
  var cy  = dim.h / 2;

  // ── Initialise node positions (random circle) ────────────────
  var nodes = RAW_NODES.map(function(n, i) {{
    var angle = (2 * Math.PI * i) / RAW_NODES.length;
    var r     = Math.min(cx, cy) * 0.45;
    return {{
      id:    n.id,
      label: n.label,
      type:  n.type,
      x:  cx + r * Math.cos(angle) + (Math.random() - .5) * 30,
      y:  cy + r * Math.sin(angle) + (Math.random() - .5) * 30,
      vx: 0, vy: 0,
      r:  26,
    }};
  }});

  var nodeMap = {{}};
  nodes.forEach(function(n) {{ nodeMap[n.id] = n; }});

  var edges = RAW_EDGES.filter(function(e) {{
    return nodeMap[e.source] && nodeMap[e.target];
  }});

  // ── Selection state ──────────────────────────────────────────
  var selected = null;

  function connectedIds(nodeId) {{
    var ids = new Set([nodeId]);
    edges.forEach(function(e) {{
      if (e.source === nodeId) ids.add(e.target);
      if (e.target === nodeId) ids.add(e.source);
    }});
    return ids;
  }}

  // ── Force simulation (Verlet, 120 warm-up ticks) ─────────────
  var REPULSION = 2200;
  var SPRING    = 120;   // rest length
  var STIFFNESS = 0.055;
  var DAMPING   = 0.82;
  var GRAVITY   = 0.012;

  function tick() {{
    // Repulsion
    for (var i = 0; i < nodes.length; i++) {{
      for (var j = i + 1; j < nodes.length; j++) {{
        var a  = nodes[i], b = nodes[j];
        var dx = b.x - a.x, dy = b.y - a.y;
        var d  = Math.sqrt(dx * dx + dy * dy) || 1;
        var f  = REPULSION / (d * d);
        a.vx -= f * dx / d;  a.vy -= f * dy / d;
        b.vx += f * dx / d;  b.vy += f * dy / d;
      }}
    }}
    // Attraction along edges
    edges.forEach(function(e) {{
      var s = nodeMap[e.source], t = nodeMap[e.target];
      if (!s || !t) return;
      var dx = t.x - s.x, dy = t.y - s.y;
      var d  = Math.sqrt(dx * dx + dy * dy) || 1;
      var f  = (d - SPRING) * STIFFNESS;
      s.vx += f * dx / d;  s.vy += f * dy / d;
      t.vx -= f * dx / d;  t.vy -= f * dy / d;
    }});
    // Centre gravity
    nodes.forEach(function(n) {{
      n.vx += (cx - n.x) * GRAVITY;
      n.vy += (cy - n.y) * GRAVITY;
      // Boundary
      n.vx += Math.max(0, n.r + 10 - n.x) * 0.5;
      n.vx -= Math.max(0, n.x + n.r + 10 - dim.w) * 0.5;
      n.vy += Math.max(0, n.r + 10 - n.y) * 0.5;
      n.vy -= Math.max(0, n.y + n.r + 10 - dim.h) * 0.5;
      // Damp + integrate
      n.vx *= DAMPING;  n.vy *= DAMPING;
      n.x  += n.vx;     n.y  += n.vy;
    }});
  }}

  // Warm up
  for (var i = 0; i < 120; i++) tick();

  // ── Draw ─────────────────────────────────────────────────────
  function draw() {{
    var W = dim.w, H = dim.h;
    ctx.clearRect(0, 0, W, H);

    var selIds = selected ? connectedIds(selected) : null;

    // Edges
    edges.forEach(function(e) {{
      var s = nodeMap[e.source], t = nodeMap[e.target];
      if (!s || !t) return;
      var highlighted = selIds
        && selIds.has(e.source) && selIds.has(e.target);
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = highlighted
        ? LIME
        : 'rgba(148,163,184,0.45)';
      ctx.lineWidth = highlighted ? 2.5 : 1.2;
      ctx.stroke();
    }});

    // Nodes
    nodes.forEach(function(n) {{
      var baseColor  = COLORS[n.type] || '#888';
      var isSelected = selected === n.id;
      var isConn     = selIds && selIds.has(n.id);
      var dim2       = selIds && !isConn;

      ctx.save();
      // Glow for selected/connected
      if (isSelected || isConn) {{
        ctx.shadowBlur  = isSelected ? 18 : 10;
        ctx.shadowColor = isSelected ? LIME : baseColor;
      }}

      // Circle fill
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, 2 * Math.PI);
      ctx.fillStyle = dim2
        ? 'rgba(226,232,240,0.6)'
        : (isSelected || isConn) ? baseColor : baseColor + 'CC';
      ctx.fill();

      // Cyber Lime ring on active/connected nodes
      if (isSelected || isConn) {{
        ctx.strokeStyle = isSelected ? LIME : LIME + '99';
        ctx.lineWidth   = isSelected ? 2.5 : 1.5;
        ctx.stroke();
      }}
      ctx.restore();

      // Label — show short ID
      var shortId = n.id.length > 10
        ? n.id.slice(0, 9) + '…' : n.id;
      ctx.font = 'bold 9.5px Inter, sans-serif';
      ctx.fillStyle = dim2
        ? '#CBD5E1'
        : (isSelected ? LIME : '#FFFFFF');
      ctx.textAlign     = 'center';
      ctx.textBaseline  = 'middle';
      ctx.fillText(shortId, n.x, n.y);
    }});
  }}

  // ── Animation loop ───────────────────────────────────────────
  var settled = false;
  var frameCount = 0;
  function loop() {{
    if (!settled) {{
      tick();
      frameCount++;
      if (frameCount > 300) settled = true;
    }}
    draw();
    requestAnimationFrame(loop);
  }}
  loop();

  // ── Interactions ─────────────────────────────────────────────
  function hitTest(mx, my) {{
    for (var i = nodes.length - 1; i >= 0; i--) {{
      var n  = nodes[i];
      var dx = mx - n.x, dy = my - n.y;
      if (Math.sqrt(dx * dx + dy * dy) <= n.r + 4) return n;
    }}
    return null;
  }}

  canvas.addEventListener('mousemove', function(e) {{
    var rect = canvas.getBoundingClientRect();
    var mx   = e.clientX - rect.left;
    var my   = e.clientY - rect.top;
    var hit  = hitTest(mx, my);
    if (hit) {{
      canvas.style.cursor = 'pointer';
      tooltip.style.display = 'block';
      tooltip.style.left = (mx + 14) + 'px';
      tooltip.style.top  = (my - 10) + 'px';
      tooltip.innerHTML  =
        '<strong>' + hit.id + '</strong><br/>'
        + hit.label;
    }} else {{
      canvas.style.cursor = 'default';
      tooltip.style.display = 'none';
    }}
  }});

  canvas.addEventListener('click', function(e) {{
    var rect = canvas.getBoundingClientRect();
    var hit  = hitTest(e.clientX - rect.left, e.clientY - rect.top);
    if (hit) {{
      selected = (selected === hit.id) ? null : hit.id;
      settled  = false;  // resume slight animation on click
      frameCount = 250;
    }} else {{
      selected = null;
    }}
  }});

  canvas.addEventListener('mouseleave', function() {{
    tooltip.style.display = 'none';
  }});
}})();
</script>
</body>
</html>
        """,
        height=height + 8,
        scrolling=False,
    )
