import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

import ShellLayout from './layout/ShellLayout'
import { ScopeProvider } from './contexts/ScopeContext'
import MaintenanceGuard from './components/MaintenanceGuard'
import MaintenancePage from './pages/MaintenancePage'
import ObservationsPage from './pages/system/ObservationsPage'
import ProposalsPage from './pages/system/ProposalsPage'
import SystemStatusSystemPage from './pages/system/SystemStatusPage'
import SystemAlertsPage from './pages/system/SystemAlertsPage'
import SystemProposalsPage from './pages/system/SystemProposalsPage'

import HomePage from './pages/HomePage'
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
import MissionAnalysisPage from './pages/operations/MissionAnalysisPage'
import MissionPlanningPage from './pages/operations/MissionPlanningPage'
import TargetingMethodologyPage from './pages/operations/TargetingMethodologyPage'
import TargetingDataPage from './pages/operations/TargetingDataPage'
import USARECTargetingPage from './pages/operations/USARECTargetingPage'

import TargetingBoardPage from './pages/planning/TargetingBoardPage'

import PerformanceAssessment from './pages/performance/AssessmentPage'

import ProjectsEventsPage from './pages/projects/ProjectsEventsPage'

import MarketSegmentationPage from './pages/operations/MarketSegmentationPage'

import SchoolLandingPage from './pages/school/SchoolLandingPage'

import BudgetTrackerPage from './pages/budget/BudgetTrackerPage'
import ProjectsDashboardPage from './pages/dash/ProjectsDashboardPage'
import EventsDashboardPage from './pages/dash/EventsDashboardPage'
import PlaceholderPage from './pages/PlaceholderPage'
import CommandIntelPage from './pages/command/IntelPage'
import RecruitingOpsPage from './pages/command/RecruitingOpsPage'
import RecruitingAnalyticsPage from './pages/performance/RecruitingAnalyticsPage'
import RoiOverviewPage from './pages/budget/RoiOverviewPage'
import FundingAllocationsPage from './pages/budget/FundingAllocationsPage'
import SystemConfigPage from './pages/admin/SystemConfigPage'
import DataImportsPage from './pages/admin/DataImportsPage'
import ManualsPage from './pages/resources/ManualsPage'
import SopsPage from './pages/resources/SopsPage'
import TrainingModulesPage from './pages/resources/TrainingModulesPage'
import UserManualPage from './pages/resources/UserManualPage'
import AssetManagementPage from './pages/planning/AssetManagementPage'
import CommunityEngagementPage from './pages/planning/CommunityEngagementPage'
import EnvRecommendationPage from './pages/planning/EnvRecommendationPage'
import PlanningCalendarPage from './pages/planning/PlanningCalendarPage'
import RecommendationsPage from './pages/planning/RecommendationsPage'
import EventPerformancePage from './pages/planning/EventPerformancePage'
import MarketingROIPage from './pages/planning/MarketingROIPage'
import ProductionDashboardPage from './pages/performance/ProductionDashboardPage'
import PerformanceMarketSegmentationPage from './pages/performance/PerformanceMarketSegmentationPage'
import FunnelMetricsPage from './pages/performance/FunnelMetricsPage'
import PerformanceTrackingPage from './pages/performance/PerformanceTrackingPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminRolesPage from './pages/admin/AdminRolesPage'
import RoleDetailPage from './pages/admin/RoleDetailPage'
import AdminMaintenancePage from './pages/admin/AdminMaintenancePage'
import AdminRbacPage from './pages/admin/AdminRbacPage'
import SystemSelfCheckPage from './pages/admin/SystemSelfCheckPage'
import DocLibraryPage from './pages/resources/DocLibraryPage'
import ResourcesRegulationsPage from './pages/resources/ResourcesRegulationsPage'
import TrainingPage from './pages/resources/TrainingPage'
import UploadsPage from './pages/resources/UploadsPage'
import HistoricalDataPage from './pages/resources/HistoricalDataPage'
import SubmitTicketPage from './pages/help/SubmitTicketPage'
import TicketStatusPage from './pages/help/TicketStatusPage'
import SystemStatusPage from './pages/help/SystemStatusPage'
import HelpDeskLandingPage from './pages/help/HelpDeskLandingPage'

export default function App() {
  return (
    <Router>
      <ScopeProvider>
        <MaintenanceGuard>
          <ShellLayout>
          <Routes>
          <Route path="/" element={<HomePage />} />
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
          <Route path="/command-center/intel" element={<CommandIntelPage />} />
          <Route path="/command-center/recruiting-ops" element={<RecruitingOpsPage />} />
          <Route path="/command-center/mission-analysis" element={<MissionAnalysisPage />} />
          <Route path="/command-center/mission-planning" element={<MissionPlanningPage />} />
          <Route path="/command-center/usarec-targeting" element={<USARECTargetingPage />} />
          <Route path="/command-center/targeting-data" element={<TargetingDataPage />} />
          <Route path="/command-center/twg" element={<TWGPageNew />} />
          <Route path="/command-center/fusion-cell" element={<FusionCellPage />} />

          {/* planning */}
          <Route path="/planning/targeting-board" element={<TargetingBoardPage />} />

          {/* Operations / Planning / Performance / Admin / Resources routes (placeholders) */}
          <Route path="/operations/mission-analysis" element={<MissionAnalysisPage />} />
          <Route path="/operations/mission-planning" element={<MissionPlanningPage />} />
          <Route path="/operations/targeting-methodology" element={<TargetingMethodologyPage />} />
          <Route path="/operations/targeting-data" element={<TargetingDataPage />} />
          <Route path="/operations/marketing-roi" element={<MarketingROIPage />} />
          <Route path="/operations/event-performance" element={<EventPerformancePage />} />

          <Route path="/planning/projects-events" element={<ProjectsEventsPage />} />
          <Route path="/planning/asset-management" element={<AssetManagementPage />} />
          <Route path="/planning/community-engagement" element={<CommunityEngagementPage />} />
          <Route path="/planning/env-recommendation" element={<EnvRecommendationPage />} />
          <Route path="/planning/calendar" element={<PlanningCalendarPage />} />

          <Route path="/planning/recommendations" element={<RecommendationsPage />} />
          <Route path="/planning/event-performance" element={<EventPerformancePage />} />
          <Route path="/planning/marketing-roi" element={<MarketingROIPage />} />

          <Route path="/performance/production-dashboard" element={<ProductionDashboardPage />} />
          <Route path="/performance/market-segmentation" element={<PerformanceMarketSegmentationPage />} />
          <Route path="/performance/funnel-metrics" element={<FunnelMetricsPage />} />
          <Route path="/performance/recruiting-analytics" element={<RecruitingAnalyticsPage />} />
          <Route path="/performance/mission-assessment" element={<MissionAssessmentPage />} />

          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/roles" element={<AdminRolesPage />} />
          <Route path="/admin/roles/:id" element={<RoleDetailPage />} />
          <Route path="/admin/maintenance" element={<AdminMaintenancePage />} />
          <Route path="/admin/rbac" element={<AdminRbacPage />} />
          <Route path="/admin/system-self-check" element={<SystemSelfCheckPage />} />
          <Route path="/admin/config" element={<SystemConfigPage />} />
          <Route path="/admin/data-imports" element={<DataImportsPage />} />

          <Route path="/resources/doc-library" element={<DocLibraryPage />} />
          <Route path="/resources/regulations" element={<ResourcesRegulationsPage />} />
          <Route path="/resources/manuals" element={<ManualsPage />} />
          <Route path="/resources/sops" element={<SopsPage />} />
          <Route path="/resources/training" element={<TrainingModulesPage />} />
          <Route path="/resources/user-manual" element={<UserManualPage />} />
          <Route path="/resources/documents" element={<DocLibraryPage />} />
          <Route path="/resources/uploads" element={<UploadsPage />} />
          <Route path="/resources/historical-data" element={<HistoricalDataPage />} />

          {/* aliases for planning */}
          <Route path="/planning/project-events" element={<ProjectsEventsPage />} />

          {/* aliases for operations */}
          <Route path="/operations/usarec-targeting-methodology" element={<TargetingMethodologyPage />} />

          {/* budget aliases */}
          <Route path="/budget/roi-overview" element={<RoiOverviewPage />} />
          <Route path="/budget/funding-allocations" element={<FundingAllocationsPage />} />
          <Route path="/resources-training/documents" element={<DocLibraryPage />} />
          <Route path="/resources-training/training" element={<TrainingPage />} />

          <Route path="/help/submit-ticket" element={<SubmitTicketPage />} />
          <Route path="/help/ticket-status" element={<TicketStatusPage />} />
          <Route path="/help/system-status" element={<SystemStatusPage />} />
          <Route path="/help-desk" element={<HelpDeskLandingPage />} />

          <Route path="/system/observations" element={<ObservationsPage />} />
          <Route path="/system/proposals" element={<SystemProposalsPage />} />
          <Route path="/system/status" element={<SystemStatusSystemPage />} />
          <Route path="/system/alerts" element={<SystemAlertsPage />} />
          <Route path="/maintenance" element={<MaintenancePage />} />

          {/* performance */}
          <Route path="/performance/assessment" element={<PerformanceAssessment />} />
          <Route path="/performance-tracking" element={<PerformanceTrackingPage />} />

          {/* projects & events */}
          <Route path="/projects-events/manage" element={<ProjectsEventsPage />} />

          {/* operations */}
          <Route path="/operations/market-segmentation" element={<MarketSegmentationPage />} />

          {/* school recruiting */}
          <Route path="/school-recruiting" element={<SchoolLandingPage />} />

          {/* budget */}
          <Route path="/budget/tracker" element={<BudgetTrackerPage />} />
          <Route path="/dash/projects" element={<ProjectsDashboardPage />} />
          <Route path="/dash/events" element={<EventsDashboardPage />} />
          </Routes>
        </ShellLayout>
        </MaintenanceGuard>
      </ScopeProvider>
    </Router>
  )
}
