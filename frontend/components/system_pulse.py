"""System Pulse Dashboard — DataLens-style project health at a glance.

Renders a self-contained HTML/SVG/JS component:
  · Circular Progress Gauge  — Validation Completeness %
  · Heatmap Grid             — Risk × Implementation coverage
  · Mini sparkline row       — per-phase completion bars

All rendering is client-side (no Pinecone / LLM calls).

Usage::

    from components.system_pulse import system_pulse

    system_pulse(
        completeness=72,
        req_total=18,
        req_done=13,
        risk_matrix={
            # rows: GxP Direct / GxP Indirect / GxP None
            # cols: Custom / Configured / Out-of-Box
            "GxP Direct":   [3, 2, 1],
            "GxP Indirect": [1, 4, 0],
            "GxP None":     [0, 2, 5],
        },
        phase_bars={
            "Requirements": 85,
            "Risk":         60,
            "Test Scripts": 45,
            "Verification": 20,
        },
    )

:requirement: URS-20.3 - Structured intelligence package output.
"""

from __future__ import annotations
import json
import streamlit.components.v1 as components


def system_pulse(
    completeness: int = 0,
    req_total: int = 0,
    req_done: int = 0,
    risk_matrix: dict[str, list[int]] | None = None,
    phase_bars: dict[str, int] | None = None,
    height: int = 320,
) -> None:
    """Render the System Pulse Dashboard.

    :param completeness: Overall validation completeness 0–100.
    :param req_total: Total requirement count.
    :param req_done: Approved/verified requirement count.
    :param risk_matrix: Dict mapping row label → list of 3 cell counts
        (Custom, Configured, Out-of-Box columns).
    :param phase_bars: Dict mapping phase label → completion %.
    :param height: Component height in pixels.
    :requirement: URS-20.3 - Structured intelligence package output.
    """
    rm = risk_matrix or {
        "GxP Direct":   [0, 0, 0],
        "GxP Indirect": [0, 0, 0],
        "GxP None":     [0, 0, 0],
    }
    pb = phase_bars or {}

    # ── Gauge geometry ────────────────────────────────────────────
    R = 54          # circle radius
    C = 2 * 3.14159 * R  # circumference ≈ 339.3
    offset = C * (1 - completeness / 100)
    gauge_color = (
        "#488421" if completeness >= 71
        else "#D17D00" if completeness >= 41
        else "#B94E4E"
    )

    # ── Heatmap colour scale ──────────────────────────────────────
    # Max value across all cells for normalisation
    all_vals = [v for row in rm.values() for v in row]
    max_val = max(all_vals) if any(all_vals) else 1

    col_labels_js = json.dumps(["Custom", "Configured", "OtB"])
    rm_json = json.dumps(rm)

    # ── Phase sparklines HTML ─────────────────────────────────────
    phase_html = ""
    for phase, pct in pb.items():
        p_color = (
            "#488421" if pct >= 71
            else "#D17D00" if pct >= 41
            else "#B94E4E"
        )
        phase_html += (
            f'<div class="pb-row">'
            f'<span class="pb-label">{phase}</span>'
            f'<div class="pb-track">'
            f'<div class="pb-fill" '
            f'style="width:{pct}%;background:{p_color};"></div>'
            f'</div>'
            f'<span class="pb-pct">{pct}%</span>'
            f'</div>'
        )

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
    color: #334155;
    font-size: 13px;
  }}
  .pulse-wrap {{
    display: flex;
    gap: 20px;
    align-items: flex-start;
    padding: 20px 24px;
    background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 100%);
    border-radius: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,.06), 0 1px 3px rgba(0,0,0,.04);
    border: 1px solid #E2E8F0;
    min-height: {height - 32}px;
  }}
  /* ── Gauge panel ─────────────────────────────────────────── */
  .gauge-panel {{
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 140px;
  }}
  .gauge-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: #64748B;
    text-align: center;
  }}
  .gauge-svg {{ overflow: visible; }}
  .gauge-track {{
    fill: none;
    stroke: #E2E8F0;
    stroke-width: 9;
    stroke-linecap: round;
  }}
  .gauge-fill {{
    fill: none;
    stroke: {gauge_color};
    stroke-width: 9;
    stroke-linecap: round;
    stroke-dasharray: {C:.1f};
    stroke-dashoffset: {offset:.1f};
    transform: rotate(-90deg);
    transform-origin: 70px 70px;
    transition: stroke-dashoffset 1s ease;
  }}
  .gauge-pct {{
    font-size: 22px;
    font-weight: 800;
    fill: #334155;
    letter-spacing: -.03em;
  }}
  .gauge-sub {{
    font-size: 9px;
    fill: #64748B;
    letter-spacing: .04em;
    font-weight: 600;
    text-transform: uppercase;
  }}
  .gauge-meta {{
    font-size: 12px;
    color: #64748B;
    text-align: center;
    line-height: 1.4;
  }}
  .gauge-meta strong {{ color: #334155; }}

  /* ── Heatmap panel ───────────────────────────────────────── */
  .heatmap-panel {{
    flex: 1;
    min-width: 0;
  }}
  .heatmap-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: #64748B;
    margin-bottom: 10px;
  }}
  .heatmap-grid {{
    display: grid;
    grid-template-columns: 90px repeat(3, 1fr);
    gap: 4px;
  }}
  .hm-corner {{ /* empty top-left cell */ }}
  .hm-col-label {{
    font-size: 10px;
    font-weight: 700;
    color: #64748B;
    text-align: center;
    padding-bottom: 4px;
    letter-spacing: .04em;
  }}
  .hm-row-label {{
    font-size: 10px;
    font-weight: 600;
    color: #334155;
    display: flex;
    align-items: center;
    padding-right: 6px;
    line-height: 1.3;
  }}
  .hm-cell {{
    border-radius: 6px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    color: #FFFFFF;
    transition: transform .15s;
    cursor: default;
  }}
  .hm-cell:hover {{ transform: scale(1.08); }}
  .hm-cell.empty {{ background: #F1F5F9; color: #CBD5E1; }}

  /* ── Phase bars panel ────────────────────────────────────── */
  .phases-panel {{
    flex-shrink: 0;
    min-width: 150px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .phases-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: #64748B;
    margin-bottom: 6px;
  }}
  .pb-row {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .pb-label {{
    font-size: 11px;
    color: #334155;
    font-weight: 500;
    width: 88px;
    flex-shrink: 0;
  }}
  .pb-track {{
    flex: 1;
    height: 6px;
    background: #E2E8F0;
    border-radius: 999px;
    overflow: hidden;
  }}
  .pb-fill {{
    height: 100%;
    border-radius: 999px;
    transition: width 1s ease;
  }}
  .pb-pct {{
    font-size: 10px;
    font-weight: 700;
    color: #64748B;
    width: 28px;
    text-align: right;
    flex-shrink: 0;
  }}
</style>
</head>
<body>
<div class="pulse-wrap">

  <!-- Gauge -->
  <div class="gauge-panel">
    <div class="gauge-title">Validation<br>Completeness</div>
    <svg class="gauge-svg" width="140" height="140"
         viewBox="0 0 140 140">
      <circle class="gauge-track" cx="70" cy="70" r="{R}"/>
      <circle class="gauge-fill" cx="70" cy="70" r="{R}"/>
      <text class="gauge-pct" x="70" y="67"
            text-anchor="middle" dominant-baseline="middle">
        {completeness}%
      </text>
      <text class="gauge-sub" x="70" y="84"
            text-anchor="middle">complete</text>
    </svg>
    <div class="gauge-meta">
      <strong>{req_done}</strong> of <strong>{req_total}</strong>
      requirements<br>approved
    </div>
  </div>

  <!-- Heatmap -->
  <div class="heatmap-panel">
    <div class="heatmap-title">Risk Coverage Heatmap</div>
    <div class="heatmap-grid" id="hm"></div>
  </div>

  <!-- Phase bars -->
  {'<div class="phases-panel"><div class="phases-title">Phase Progress</div>'
   + phase_html + '</div>' if pb else ''}

</div>
<script>
(function() {{
  var rm   = {rm_json};
  var cols = {col_labels_js};
  var maxV = {max_val};

  function cellColor(v) {{
    if (v === 0) return null;
    var t = v / maxV;
    if (t > 0.66) return '#B94E4E';   // high density → red
    if (t > 0.33) return '#D17D00';   // medium       → amber
    return '#488421';                  // low           → green
  }}

  var hm = document.getElementById('hm');
  // Corner
  var corner = document.createElement('div');
  corner.className = 'hm-corner';
  hm.appendChild(corner);
  // Col headers
  cols.forEach(function(c) {{
    var d = document.createElement('div');
    d.className = 'hm-col-label';
    d.textContent = c;
    hm.appendChild(d);
  }});
  // Rows
  Object.keys(rm).forEach(function(row) {{
    var rl = document.createElement('div');
    rl.className = 'hm-row-label';
    rl.textContent = row;
    hm.appendChild(rl);
    rm[row].forEach(function(val) {{
      var cell = document.createElement('div');
      var col  = cellColor(val);
      if (col) {{
        cell.className = 'hm-cell';
        cell.style.background = col;
        cell.textContent = val || '';
        cell.title = row + ' · ' + val + ' requirement(s)';
      }} else {{
        cell.className = 'hm-cell empty';
        cell.textContent = '—';
      }}
      hm.appendChild(cell);
    }});
  }});
}})();
</script>
</body>
</html>
        """,
        height=height,
        scrolling=False,
    )
