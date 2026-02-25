"""Compliance Command Center — React-based comparison dashboard.

Renders a self-contained React 18 + Tailwind CSS component via
``streamlit.components.v1.html()`` showing risk-exposure calculator,
continuous-compliance bar, and EVOLV vs Legacy benchmark table.

:requirement: URS-19.6 - Display side-by-side comparison.
"""

import streamlit.components.v1 as components


def render_compliance_command_center(
    gap_count: int,
    avg_audit_fine: float,
    delay_cost_per_week: float,
) -> None:
    """Render the Compliance Command Center React component.

    :param gap_count: Number of open compliance gaps.
    :param avg_audit_fine: Average audit fine per gap ($).
    :param delay_cost_per_week: Weekly delay cost ($).
    :requirement: URS-19.6 - Display side-by-side comparison.
    """
    html = _build_html(gap_count, avg_audit_fine, delay_cost_per_week)
    components.html(html, height=920, scrolling=True)


def _build_html(
    gap_count: int,
    avg_audit_fine: float,
    delay_cost_per_week: float,
) -> str:
    """Build the full self-contained HTML string.

    :param gap_count: Number of open compliance gaps.
    :param avg_audit_fine: Average audit fine per gap.
    :param delay_cost_per_week: Weekly delay cost.
    :return: HTML string with CDN-loaded React 18, Tailwind, htm.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {{
  theme: {{
    extend: {{
      colors: {{
        evolv: {{
          green: '#488421',
          'green-light': '#E8F5E9',
          blue: '#056696',
          'blue-light': '#0A7EB5',
          slate: '#54585A',
          'slate-light': '#6E7275',
          border: '#E0E0E0',
        }}
      }}
    }}
  }}
}}
</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/htm@3/dist/htm.umd.js"></script>
<style>
  body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #F4F5F6; }}
  .glow-green {{ box-shadow: 0 0 12px rgba(72,132,33,0.4); }}
</style>
</head>
<body>
<div id="root"></div>
<script>
const {{ createElement }} = React;
const html = htm.bind(createElement);

const GAP_COUNT = {gap_count};
const AVG_AUDIT_FINE = {avg_audit_fine};
const DELAY_COST_PER_WEEK = {delay_cost_per_week};

function calculateRiskExposure(gapCount, avgAuditFine, delayCostPerWeek) {{
  const auditRisk = gapCount * avgAuditFine;
  const delayWeeks = Math.ceil(gapCount * 1.5);
  const delayCost = delayWeeks * delayCostPerWeek;
  const totalExposure = auditRisk + delayCost;
  return {{ auditRisk, delayWeeks, delayCost, totalExposure }};
}}

function fmt(n) {{
  return '$' + n.toLocaleString('en-US', {{ maximumFractionDigits: 0 }});
}}

function MoneyLeakCard({{ data }}) {{
  return html\`
    <div class="bg-white border border-red-200 border-l-4 border-l-red-500 rounded-lg p-5 mb-5">
      <div class="flex items-center gap-2 mb-3">
        <span class="text-red-500 text-xl">&#9888;</span>
        <h3 class="text-lg font-bold text-gray-800 m-0">Compliance Risk Exposure</h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="text-center p-3 bg-red-50 rounded-lg">
          <div class="text-2xl font-bold text-red-600">${{fmt(data.totalExposure)}}</div>
          <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">Total Exposure</div>
        </div>
        <div class="text-center p-3 bg-amber-50 rounded-lg">
          <div class="text-xl font-bold text-amber-600">${{fmt(data.auditRisk)}}</div>
          <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">Audit Risk</div>
        </div>
        <div class="text-center p-3 bg-amber-50 rounded-lg">
          <div class="text-xl font-bold text-amber-600">${{data.delayWeeks}} wks</div>
          <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">Est. Delay</div>
        </div>
        <div class="text-center p-3 bg-amber-50 rounded-lg">
          <div class="text-xl font-bold text-amber-600">${{fmt(data.delayCost)}}</div>
          <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">Delay Cost</div>
        </div>
      </div>
    </div>
  \`;
}}

function ContinuousComplianceBar() {{
  return html\`
    <div class="bg-white border border-evolv-border rounded-lg p-5 mb-5">
      <h3 class="text-base font-bold text-gray-800 mb-4">Continuous Compliance Score</h3>
      <div class="space-y-3">
        <div>
          <div class="flex justify-between mb-1">
            <span class="text-sm font-semibold text-evolv-green">EVOLV</span>
            <span class="text-sm font-bold text-evolv-green">100%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-3">
            <div class="bg-evolv-green h-3 rounded-full glow-green" style="width: 100%"></div>
          </div>
        </div>
        <div>
          <div class="flex justify-between mb-1">
            <span class="text-sm font-semibold text-gray-500">Legacy Systems</span>
            <span class="text-sm font-bold text-amber-600">62%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-3">
            <div class="bg-amber-500 h-3 rounded-full" style="width: 62%"></div>
          </div>
        </div>
      </div>
    </div>
  \`;
}}

const COMPARISON_DATA = [
  {{
    pain: "Implementation Speed",
    legacy: "6\\u201318 months, heavy consulting",
    evolv: "3 days, AI-driven setup",
  }},
  {{
    pain: "Feature Request Lead Time",
    legacy: "180-day release cycles",
    evolv: "3 days, modular agents",
  }},
  {{
    pain: "AI Regulation Alignment",
    legacy: "Manual/Lagging SOP updates",
    evolv: "Jan 2026 FDA/EMA Live",
  }},
  {{
    pain: "Impact Analysis",
    legacy: "Static/Manual spreadsheets",
    evolv: "Dynamic/Automated risk matrix",
  }},
  {{
    pain: "Human-in-the-Loop",
    legacy: "Not Integrated, signature only",
    evolv: "Native AI-Collab at every step",
  }},
];

function ComparisonTable() {{
  return html\`
    <div class="bg-white border border-evolv-border rounded-lg p-5 mb-5">
      <h3 class="text-base font-bold text-gray-800 mb-4">
        EVOLV vs. Legacy Validation Systems (2026 Benchmark)
      </h3>
      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-sm">
          <thead>
            <tr class="border-b-2 border-gray-200">
              <th class="text-left py-3 px-4 font-bold text-gray-700 bg-gray-50">CSV Pain Point</th>
              <th class="text-left py-3 px-4 font-bold text-gray-700 bg-gray-50">Legacy Giants</th>
              <th class="text-left py-3 px-4 font-bold text-gray-700 bg-gray-50">EVOLV Strategy</th>
            </tr>
          </thead>
          <tbody>
            ${{COMPARISON_DATA.map((row, i) => html\`
              <tr key=${{i}} class="border-b border-gray-100 hover:bg-blue-50 transition-colors">
                <td class="py-3 px-4 font-semibold text-gray-700">${{row.pain}}</td>
                <td class="py-3 px-4">
                  <span class="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-500">
                    ${{row.legacy}}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <span class="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-green-50 text-green-700 glow-green">
                    ${{row.evolv}}
                  </span>
                </td>
              </tr>
            \`)}}
          </tbody>
        </table>
      </div>
    </div>
  \`;
}}

function App() {{
  const data = calculateRiskExposure(GAP_COUNT, AVG_AUDIT_FINE, DELAY_COST_PER_WEEK);
  return html\`
    <div class="max-w-5xl mx-auto p-4">
      <${{MoneyLeakCard}} data=${{data}} />
      <${{ContinuousComplianceBar}} />
      <${{ComparisonTable}} />
      <p class="text-center text-xs text-gray-400 mt-4">
        Powered by EVOLV | A WingstarTech Inc. Product
      </p>
    </div>
  \`;
}}

ReactDOM.createRoot(document.getElementById('root')).render(html\`<${{App}} />\`);
</script>
</body>
</html>"""
