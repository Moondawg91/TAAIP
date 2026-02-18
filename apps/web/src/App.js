import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

import ShellLayout from './layout/ShellLayout'

import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import DashboardDetailPage from './pages/DashboardDetailPage'
import QBRPage from './pages/QBRPage'
import CommandCenterPage from './pages/CommandCenterPage'
import ProjectsPage from './pages/ProjectsPage'
import MeetingsPage from './pages/MeetingsPage'
import CalendarPage from './pages/CalendarPage'
import ImportCenterPage from './pages/ImportCenterPage'

// new placeholders
import OpsCalendarPage from './pages/ops/CalendarPage'
import OpsProjectsPage from './pages/ops/ProjectsPage'
import OpsEventsPage from './pages/ops/EventsPage'
import OpsFusionPage from './pages/ops/FusionPage'
import OpsTWGPage from './pages/ops/TWGPage'
import OpsBudgetPage from './pages/ops/BudgetPage'
import OpsRoiPage from './pages/ops/RoiPage'

import DocsSharepoint from './pages/docs/SharepointPage'
import DocsLibrary from './pages/docs/LibraryPage'
import DocsRegulations from './pages/docs/RegulationsPage'

import InsightsCommandCenter from './pages/insights/CommandCenterPage'
import InsightsAnalytics from './pages/insights/AnalyticsPage'
import InsightsMarketIntel from './pages/insights/MarketIntelPage'
import InsightsFunnel from './pages/insights/FunnelPage'

// new command/planning/performance/etc pages
import CommandCenterPageNew from './pages/command/CommandCenterPage'
import LinesOfEffortPage from './pages/command/LinesOfEffortPage'
import CommandPrioritiesPage from './pages/command/CommandPrioritiesPage'
import MissionAssessmentPage from './pages/command/MissionAssessmentPage'
import TWGPageNew from './pages/command/TWGPage'
import FusionCellPage from './pages/command/FusionCellPage'
import MissionAnalysisPage from './pages/command/MissionAnalysisPage'
import MissionPlanningPage from './pages/command/MissionPlanningPage'
import USARECTargetingPage from './pages/command/USARECTargetingPage'
import TargetingDataPage from './pages/command/TargetingDataPage'

import TargetingBoardPage from './pages/planning/TargetingBoardPage'

import PerformanceAssessment from './pages/performance/AssessmentPage'

import ProjectsEventsPage from './pages/projects/ProjectsEventsPage'

import MarketSegmentationPage from './pages/operations/MarketSegmentationPage'

import SchoolLandingPage from './pages/school/SchoolLandingPage'

import BudgetTrackerPage from './pages/budget/BudgetTrackerPage'
import PlaceholderPage from './pages/PlaceholderPage'

export default function App() {
  return (
    <Router>
      <ShellLayout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/:id" element={<DashboardDetailPage />} />
          <Route path="/qbr" element={<QBRPage />} />
          <Route path="/dashboards/command-center" element={<CommandCenterPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/meetings" element={<MeetingsPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/import-center" element={<ImportCenterPage />} />

          {/* new ops routes (legacy kept) */}
          <Route path="/ops/calendar" element={<OpsCalendarPage />} />
          <Route path="/ops/projects" element={<OpsProjectsPage />} />
          <Route path="/ops/events" element={<OpsEventsPage />} />
          <Route path="/ops/fusion" element={<OpsFusionPage />} />
          <Route path="/ops/twg" element={<OpsTWGPage />} />
          <Route path="/ops/budget" element={<OpsBudgetPage />} />
          <Route path="/ops/roi" element={<OpsRoiPage />} />

          {/* documents */}
          <Route path="/docs/sharepoint" element={<DocsSharepoint />} />
          <Route path="/docs/library" element={<DocsLibrary />} />
          <Route path="/docs/regulations" element={<DocsRegulations />} />

          {/* insights / resources (legacy) */}
          <Route path="/insights/command-center" element={<InsightsCommandCenter />} />
          <Route path="/insights/analytics" element={<InsightsAnalytics />} />
          <Route path="/insights/market-intel" element={<InsightsMarketIntel />} />
          <Route path="/insights/funnel" element={<InsightsFunnel />} />

          {/* new command center + children */}
          <Route path="/command-center" element={<CommandCenterPageNew />} />
          <Route path="/command-center/lines-of-effort" element={<LinesOfEffortPage />} />
          <Route path="/command-center/priorities" element={<CommandPrioritiesPage />} />
          <Route path="/command-center/mission-assessment" element={<MissionAssessmentPage />} />
          <Route path="/command-center/mission-analysis" element={<MissionAnalysisPage />} />
          <Route path="/command-center/mission-planning" element={<MissionPlanningPage />} />
          <Route path="/command-center/usarec-targeting" element={<USARECTargetingPage />} />
          <Route path="/command-center/targeting-data" element={<TargetingDataPage />} />
          <Route path="/command-center/twg" element={<TWGPageNew />} />
          <Route path="/command-center/fusion-cell" element={<FusionCellPage />} />

          {/* planning */}
          <Route path="/planning/targeting-board" element={<TargetingBoardPage />} />

          {/* Operations / Planning / Performance / Admin / Resources routes (placeholders) */}
          <Route path="/operations/mission-analysis" element={<PlaceholderPage title="Mission Analysis" subtitle="Placeholder" />} />
          <Route path="/operations/mission-planning" element={<PlaceholderPage title="Mission Planning" subtitle="Placeholder" />} />
          <Route path="/operations/targeting-methodology" element={<PlaceholderPage title="USAREC Targeting Methodology" subtitle="Placeholder" />} />
          <Route path="/operations/targeting-data" element={<PlaceholderPage title="Targeting Data" subtitle="Placeholder" />} />

          <Route path="/planning/projects-events" element={<PlaceholderPage title="Project & Event Management" subtitle="Placeholder" />} />
          <Route path="/planning/asset-management" element={<PlaceholderPage title="Asset Management" subtitle="Placeholder" />} />
          <Route path="/planning/community-engagement" element={<PlaceholderPage title="Community Engagement" subtitle="Placeholder" />} />
          <Route path="/planning/env-recommendation" element={<PlaceholderPage title="Enabler Recommendations" subtitle="Placeholder" />} />
          <Route path="/planning/calendar" element={<PlaceholderPage title="Calendar / Scheduling" subtitle="Placeholder" />} />

          <Route path="/performance/production-dashboard" element={<PlaceholderPage title="Production Dashboard" subtitle="Placeholder" />} />
          <Route path="/performance/market-segmentation" element={<PlaceholderPage title="Market Segmentation" subtitle="Placeholder" />} />
          <Route path="/performance/funnel-metrics" element={<PlaceholderPage title="Funnel Metrics" subtitle="Placeholder" />} />

          <Route path="/admin/users" element={<PlaceholderPage title="User Management" subtitle="Placeholder" />} />
          <Route path="/admin/roles" element={<PlaceholderPage title="Role & Scope Control" subtitle="Placeholder" />} />

          <Route path="/resources/doc-library" element={<PlaceholderPage title="Document Library" subtitle="Placeholder" />} />
          <Route path="/resources/regulations" element={<PlaceholderPage title="Regulations" subtitle="Placeholder" />} />

          <Route path="/help/submit-ticket" element={<PlaceholderPage title="Submit Ticket" subtitle="Help Desk" />} />
          <Route path="/help/ticket-status" element={<PlaceholderPage title="Ticket Status" subtitle="Help Desk" />} />
          <Route path="/help/system-status" element={<PlaceholderPage title="System Status" subtitle="Help Desk" />} />

          {/* performance */}
          <Route path="/performance/assessment" element={<PerformanceAssessment />} />

          {/* projects & events */}
          <Route path="/projects-events/manage" element={<ProjectsEventsPage />} />

          {/* operations */}
          <Route path="/operations/market-segmentation" element={<MarketSegmentationPage />} />

          {/* school recruiting */}
          <Route path="/school-recruiting" element={<SchoolLandingPage />} />

          {/* budget */}
          <Route path="/budget/tracker" element={<BudgetTrackerPage />} />
        </Routes>
      </ShellLayout>
    </Router>
  )
}
