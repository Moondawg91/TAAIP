import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'

import ShellLayout from './layout/ShellLayout'
import { AuthProvider } from './contexts/AuthContext'
import RequireAdmin from './components/RequireAdmin'
import { ScopeProvider } from './contexts/ScopeContext'
import { UnitFilterProvider } from './contexts/UnitFilterContext'
import { FilterProvider } from './contexts/FilterContext'
import { OrgUnitStoreProvider } from './state/orgUnitStore'
import { OrgSelectionProvider } from './contexts/OrgSelectionContext'
// Unit cascade moved to TopHeader to avoid duplicate renders
import MaintenanceGuard from './components/MaintenanceGuard'
import MaintenancePage from './pages/MaintenancePage'
import ObservationsPage from './pages/system/ObservationsPage'
import ProposalsPage from './pages/system/ProposalsPage'
import SystemStatusSystemPage from './pages/system/SystemStatusPage'
import SystemAlertsPage from './pages/system/SystemAlertsPage'
import SystemProposalsPage from './pages/system/SystemProposalsPage'

import HomePage from './pages/HomePage'
import OperationsPage from './pages/OperationsPage'
import QBRPage from './pages/QBRPage'
import CommandCenterPage from './pages/CommandCenterPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/projects/ProjectDetailPage'
import MeetingsPage from './pages/MeetingsPage'
import CalendarPage from './pages/CalendarPage'
import ImportCenterPage from './pages/ImportCenterPage'

// new placeholders
import OpsCalendarPage from './pages/ops/CalendarPage'
import OpsProjectsPage from './pages/ops/ProjectsPage'
import OpsEventsPage from './pages/ops/EventsPage'
import OpsBudgetPage from './pages/ops/BudgetPage'
import OpsRoiPage from './pages/ops/RoiPage'
import RoiPage from './pages/RoiPage'

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
import MissionFeasibilityPage from './pages/command/MissionFeasibilityPage'
import FsLossPage from './pages/command/FsLossPage'
import TWGPageNew from './pages/command/TWGPage'
import FusionCellPage from './pages/command/FusionCellPage'
import FusionBriefing from './pages/command/FusionBriefing'
import PlanningLandingPage from './pages/planning/PlanningLandingPage'
import MissionAnalysisPage from './pages/operations/MissionAnalysisPage'
import MissionPlanningPage from './pages/operations/MissionPlanningPage'
import MarketIntelligencePage from './pages/operations/MarketIntelligencePage'
import TargetingMethodologyPage from './pages/operations/TargetingMethodologyPage'
import TargetingDataPage from './pages/operations/TargetingDataPage'
import USARECTargetingPage from './pages/operations/USARECTargetingPage'

// 420T command center / MDMP workspace
import Command420TPage from './pages/command/420TCommandCenterPage'
import MDMPWorkspacePage from './pages/command/MDMPWorkspacePage'

import TargetingBoardPage from './pages/planning/TargetingBoardPage'

import PerformanceAssessment from './pages/performance/AssessmentPage'

import ProjectsEventsPage from './pages/projects/ProjectsEventsPage'

import MarketSegmentationPage from './pages/operations/MarketSegmentationPage'

import { Navigate } from 'react-router-dom'
import SchoolLandingPage from './pages/school/SchoolLandingPage'
import SchoolProgramPage from './pages/school/SchoolProgramPage'
import OverviewPage from './pages/school/OverviewPage'
import CoveragePage from './pages/school/CoveragePage'
import CompliancePage from './pages/school/CompliancePage'
import EventsPageSchool from './pages/school/EventsPage'
import LeadsPage from './pages/school/LeadsPage'
import RoiPageSchool from './pages/school/RoiPage'
import IwPageSchool from './pages/school/IwPage'
import SchoolDataPage from './pages/school/DataPage'

import BudgetTrackerPage from './pages/budget/BudgetTrackerPage'
import ProjectsDashboardPage from './pages/dash/ProjectsDashboardPage'
import EventsDashboardPage from './pages/dash/EventsDashboardPage'
import { NotLoadedPage } from './pages/PlaceholderPage'
import CommandIntelPage from './pages/command/IntelPage'
import RecruitingOpsPage from './pages/command/RecruitingOpsPage'
import RecruitingAnalyticsPage from './pages/performance/RecruitingAnalyticsPage'
import RoiOverviewPage from './pages/budget/RoiOverviewPage'
import FundingAllocationsPage from './pages/budget/FundingAllocationsPage'
import SystemConfigPage from './pages/admin/SystemConfigPage'
// DataImportsPage removed from Admin; Data Hub will be a top-level resource
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
import PermissionsPage from './pages/admin/PermissionsPage'
import SystemSelfCheckPage from './pages/admin/SystemSelfCheckPage'
import ProtectedRoute from './components/ProtectedRoute'
import DocLibraryPage from './pages/resources/DocLibraryPage'
import ResourcesRegulationsPage from './pages/resources/ResourcesRegulationsPage'
import TrainingPage from './pages/resources/TrainingPage'
import UploadsPage from './pages/resources/UploadsPage'
import HistoricalDataPage from './pages/resources/HistoricalDataPage'
import RegulatoryPage from './pages/resources/RegulatoryPage'
import TraceabilityMatrixPage from './pages/resources/TraceabilityMatrixPage'
import DataHubPage from './pages/datahub/DataHubPage'
import DashboardPage from './pages/DashboardPage'
import DashboardLayout from './layouts/DashboardLayout'
import SubmitTicketPage from './pages/help/SubmitTicketPage'
import TicketStatusPage from './pages/help/TicketStatusPage'
import SystemStatusPage from './pages/help/SystemStatusPage'
import HelpDeskLandingPage from './pages/help/HelpDeskLandingPage'
import AccessDeniedPage from './pages/AccessDeniedPage'
import UnauthorizedPage from './pages/UnauthorizedPage'
import DebugAccessPage from './pages/DebugAccessPage'

export default function App() {
  useEffect(() => {
    try {
      // E2E tests can wait for this flag to know the client has mounted
      window.__APP_READY__ = true
    } catch (e) {
      // noop
    }
    return () => {
      try {
        delete window.__APP_READY__
      } catch (e) {}
    }
  }, [])
  return (
    <Router>
      <AuthProvider>
      <ScopeProvider>
        <FilterProvider>
        <UnitFilterProvider>
        <OrgUnitStoreProvider>
        <OrgSelectionProvider>
          <MaintenanceGuard>
            <ShellLayout>
          {/* unit cascade is rendered in TopHeader for dashboard routes */}
          <Routes>
          <Route path="/" element={<DashboardLayout><HomePage /></DashboardLayout>} />
          <Route path="/dashboard" element={<DashboardLayout><DashboardPage /></DashboardLayout>} />
          <Route path="/qbr" element={<QBRPage />} />
          <Route path="/dashboards/command-center" element={<CommandCenterPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:id" element={<ProjectDetailPage />} />
          <Route path="/meetings" element={<MeetingsPage />} />
          <Route path="/calendar" element={<CalendarPage />} />

          {/* new ops routes (legacy kept) */}
          <Route path="/ops/calendar" element={<OpsCalendarPage />} />
          <Route path="/ops/projects" element={<OpsProjectsPage />} />
          <Route path="/ops/events" element={<OpsEventsPage />} />
          <Route path="/ops/budget" element={<OpsBudgetPage />} />
          <Route path="/ops/roi" element={<OpsRoiPage />} />
          <Route path="/roi" element={<RoiPage />} />

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
          <Route path="/command-center/feasibility" element={<MissionFeasibilityPage />} />
          <Route path="/command-center/fs-loss" element={<FsLossPage />} />
          <Route path="/command-center/420t" element={<Command420TPage />} />
          <Route path="/command-center/mdmp" element={<MDMPWorkspacePage />} />
          <Route path="/command-center/intel" element={<CommandIntelPage />} />
          <Route path="/command-center/recruiting-ops" element={<RecruitingOpsPage />} />
          <Route path="/command-center/mission-analysis" element={<MissionAnalysisPage />} />
          <Route path="/command-center/mission-planning" element={<MissionPlanningPage />} />
          <Route path="/command-center/usarec-targeting" element={<USARECTargetingPage />} />
          <Route path="/command-center/targeting-data" element={<TargetingDataPage />} />
          <Route path="/command-center/twg" element={<TWGPageNew />} />
          <Route path="/command-center/fusion-cell" element={<FusionCellPage />} />
          <Route path="/command-center/fusion-briefing" element={<FusionBriefing />} />

          {/* planning aliases and direct links for TWG/Fusion per TOR */}
          {/* Planning landing removed from primary nav; keep route for compatibility if needed */}
          <Route path="/planning" element={<PlanningLandingPage />} />
          <Route path="/planning/twg" element={<TWGPageNew />} />
          <Route path="/planning/fusion" element={<FusionCellPage />} />

          {/* planning */}
          <Route path="/planning/targeting-board" element={<TargetingBoardPage />} />
          <Route path="/ops" element={<OperationsPage />} />

          {/* Operations / Planning / Performance / Admin / Resources routes (placeholders) */}
          <Route path="/operations/mission-analysis" element={<MissionAnalysisPage />} />
          <Route path="/operations/mission-planning" element={<MissionPlanningPage />} />
          <Route path="/operations/targeting-methodology" element={<TargetingMethodologyPage />} />
          <Route path="/operations/targeting-data" element={<TargetingDataPage />} />
          {/* ROI/Events consolidated under /roi page; legacy /operations/event-performance retained for compatibility */}
          <Route path="/operations/event-performance" element={<EventPerformancePage />} />

          <Route path="/planning/projects-events" element={<ProjectsEventsPage />} />
          <Route path="/planning/asset-management" element={<AssetManagementPage />} />
          <Route path="/planning/community-engagement" element={<CommunityEngagementPage />} />
          {/* Environmental Recommendation Engine removed from top-level nav (kept as background input). */}
          <Route path="/planning/calendar" element={<PlanningCalendarPage />} />

          <Route path="/planning/recommendations" element={<RecommendationsPage />} />
          <Route path="/planning/event-performance" element={<EventPerformancePage />} />
          <Route path="/planning/marketing-roi" element={<MarketingROIPage />} />

          <Route path="/performance/production-dashboard" element={<ProductionDashboardPage />} />
          <Route path="/performance/market-segmentation" element={<PerformanceMarketSegmentationPage />} />
          <Route path="/performance/funnel-metrics" element={<FunnelMetricsPage />} />
          <Route path="/performance/recruiting-analytics" element={<RecruitingAnalyticsPage />} />
          <Route path="/performance/mission-assessment" element={<MissionAssessmentPage />} />

          <Route path="/admin/users" element={<ProtectedRoute path="/admin"><AdminUsersPage /></ProtectedRoute>} />
          <Route path="/admin/roles" element={<ProtectedRoute path="/admin"><AdminRolesPage /></ProtectedRoute>} />
          <Route path="/admin/roles/:id" element={<ProtectedRoute path="/admin"><RoleDetailPage /></ProtectedRoute>} />
          <Route path="/admin/maintenance" element={<ProtectedRoute path="/admin"><AdminMaintenancePage /></ProtectedRoute>} />
          <Route path="/admin/rbac" element={<ProtectedRoute path="/admin"><AdminRbacPage /></ProtectedRoute>} />
          <Route path="/admin/permissions" element={<ProtectedRoute path="/admin"><PermissionsPage /></ProtectedRoute>} />
          <Route path="/admin/system-self-check" element={<ProtectedRoute path="/admin"><SystemSelfCheckPage /></ProtectedRoute>} />
          <Route path="/admin/config" element={<ProtectedRoute path="/admin"><SystemConfigPage /></ProtectedRoute>} />

          <Route path="/resources/doc-library" element={<DocLibraryPage />} />
          <Route path="/data-hub" element={<DataHubPage />} />
          <Route path="/data-hub/imports" element={<Navigate to="/data-hub" replace />} />
          <Route path="/data-hub/schemas" element={<Navigate to="/data-hub" replace />} />
          <Route path="/data-hub/storage" element={<Navigate to="/data-hub" replace />} />
          <Route path="/access-denied" element={<AccessDeniedPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route path="/debug/access" element={<DebugAccessPage />} />
          <Route path="/resources/regulations" element={<ResourcesRegulationsPage />} />
          <Route path="/resources/regulatory" element={<RegulatoryPage />} />
          <Route path="/resources/traceability" element={<TraceabilityMatrixPage />} />
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
          <Route path="/operations/market-intelligence" element={<MarketIntelligencePage />} />

          {/* school recruiting (legacy kept) */}
          <Route path="/school-recruiting" element={<SchoolLandingPage />} />
          {/* legacy program route redirects to new dashboard to avoid breaking existing links */}
          <Route path="/school-recruiting/program" element={<Navigate to="/school/dashboard" replace />} />
          <Route path="/school-recruiting/overview" element={<OverviewPage />} />
          <Route path="/school-recruiting/coverage" element={<CoveragePage />} />
          <Route path="/school-recruiting/compliance" element={<CompliancePage />} />
          <Route path="/school-recruiting/events" element={<Navigate to="/planning/projects-events?category=school" replace />} />
          <Route path="/school-recruiting/leads" element={<LeadsPage />} />
          <Route path="/school-recruiting/roi" element={<RoiPageSchool />} />
          <Route path="/school-recruiting/iw" element={<IwPageSchool />} />

          {/* new School Recruiting routes (phase B) */}
          <Route path="/school/dashboard" element={<SchoolLandingPage />} />
          <Route path="/school/coverage" element={<CoveragePage />} />
          <Route path="/school/calendar" element={<EventsPageSchool />} />
          <Route path="/school/compliance" element={<CompliancePage />} />
          <Route path="/school/leadflow" element={<LeadsPage />} />
          <Route path="/school/events" element={<Navigate to="/planning/projects-events?category=school" replace />} />
          {/* Compatibility redirects: move school events under Planning -> Project & Event Management */}
          <Route path="/school/events" element={<Navigate to="/planning/projects-events?category=school" replace />} />
          <Route path="/school-recruiting/events" element={<Navigate to="/planning/projects-events?category=school" replace />} />
          <Route path="/school/data" element={<SchoolDataPage />} />

          {/* budget */}
          <Route path="/budget/tracker" element={<BudgetTrackerPage />} />
          <Route path="/dash/projects" element={<ProjectsDashboardPage />} />
          <Route path="/dash/events" element={<EventsDashboardPage />} />
          </Routes>
            </ShellLayout>
          </MaintenanceGuard>
        </OrgSelectionProvider>
        </OrgUnitStoreProvider>
        </UnitFilterProvider>
        </FilterProvider>
      </ScopeProvider>
      </AuthProvider>
    </Router>
  )
}
