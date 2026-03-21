/**
 * MainContent — view router.
 *
 * Maps currentView → the correct view component.
 * Falls back to DashboardView for unknown views.
 */
import DashboardView     from './views/DashboardView.jsx'
import URSView           from './views/URSView.jsx'
import RiskView          from './views/RiskView.jsx'
import TestScriptsView   from './views/TestScriptsView.jsx'
import TraceabilityView  from './views/TraceabilityView.jsx'
import FRSView           from './views/FRSView.jsx'
import VSRView           from './views/VSRView.jsx'
import SupplierView      from './views/SupplierView.jsx'

const VIEW_MAP = {
  dashboard:    DashboardView,
  urs:          URSView,
  risk:         RiskView,
  test:         TestScriptsView,
  traceability: TraceabilityView,
  frs:          FRSView,
  vsr:          VSRView,
  supplier:     SupplierView,
}

export default function MainContent({ view, node, breadcrumb, tree }) {
  const Component = VIEW_MAP[view] || DashboardView
  return <Component node={node} breadcrumb={breadcrumb} tree={tree} />
}
