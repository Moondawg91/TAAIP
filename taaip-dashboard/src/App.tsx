import React, { useEffect, useRef, useState, lazy, Suspense } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Sidebar, TabId } from './components/shared/Sidebar';
import { useEnterpriseAccess } from './hooks/useEnterpriseAccess';
import { useToast } from './components/shared/ToastProvider';
import GlobalNotificationCenter from './components/shared/GlobalNotificationCenter';
import { runAllIngestionModules } from './lib/ingestion/controller';
import { logAuditEvent } from './lib/audit/controller';
import { seedOperationalAlerts, subscribeNotifications } from './lib/notifications/controller';
import { usePageExport } from './lib/export';

const HomePage = lazy(() => import('./pages/enterprise/HomePage'));
const CommandCenterPage = lazy(() => import('./pages/enterprise/CommandCenterPage'));
const FusionCellPage = lazy(() => import('./pages/enterprise/FusionCellPage'));
const TWGPage = lazy(() => import('./pages/enterprise/TWGPage'));
const TargetingBoardPage = lazy(() => import('./pages/enterprise/TargetingBoardPage'));
const OperationsPage = lazy(() => import('./pages/enterprise/OperationsPage'));
const FieldActivitiesPage = lazy(() => import('./pages/enterprise/FieldActivitiesPage'));
const BudgetPage = lazy(() => import('./pages/enterprise/BudgetPage'));
const MarketIntelligenceEnterprisePage = lazy(() => import('./pages/enterprise/MarketIntelligenceEnterprisePage'));
const SchoolIntelligencePage = lazy(() => import('./pages/enterprise/SchoolIntelligencePage'));
const DODMarketSharePage = lazy(() => import('./pages/enterprise/DODMarketSharePage'));
const SegmentationPage = lazy(() => import('./pages/enterprise/SegmentationPage'));
const ReserveAlignmentPage = lazy(() => import('./pages/enterprise/ReserveAlignmentPage'));
const MarketPotentialPage = lazy(() => import('./pages/enterprise/MarketPotentialPage'));
const OutOfAreaAnalysisPage = lazy(() => import('./pages/enterprise/OutOfAreaAnalysisPage'));
const ROIAnalysisPage = lazy(() => import('./pages/enterprise/ROIAnalysisPage'));
const PerformancePage = lazy(() => import('./pages/enterprise/PerformancePage'));
const FunnelAnalysisPage = lazy(() => import('./pages/enterprise/FunnelAnalysisPage'));
const DataDocumentCenterPage = lazy(() => import('./pages/enterprise/DataDocumentCenterPage'));
const TrainingCenterPage = lazy(() => import('./pages/enterprise/TrainingCenterPage'));
const AdminPage = lazy(() => import('./pages/enterprise/AdminPage'));

const TAB_LABEL: Record<string, string> = {
  'home-page': 'Home',
  'command-center': 'Command Center',
  'fusion-cell': 'Fusion Cell',
  'twg': 'TWG',
  'targeting-board': 'Targeting Board',
  'operations-page': 'Operations',
  'field-activities-page': 'Field Activities',
  'budget-page': 'Budget',
  'market-intelligence': 'Market Intelligence',
  'school-intelligence': 'School Intelligence',
  'dod-market-share': 'DoD Market Share',
  segmentation: 'Segmentation',
  'reserve-alignment': 'Reserve Alignment',
  'market-potential': 'Market Potential',
  'out-of-area-analysis': 'Out-of-Area Analysis',
  'roi-analysis': 'ROI Analysis Page',
  'performance-page': 'Performance Page',
  'funnel-analysis': 'Funnel Analysis Page',
  'data-document-center': 'Data & Document Center',
  'training-center': 'Training Center',
  admin: 'Administration',
};

const ALLOWED_TABS = Object.keys(TAB_LABEL) as TabId[];

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('home-page');
  const { canAccessPage } = useEnterpriseAccess();
  const { pushToast } = useToast();
  const seenCritical = useRef<Set<string>>(new Set());

  useEffect(() => {
    const qp = new URLSearchParams(window.location.search);
    const requested = qp.get('activeTab') as TabId | null;
    if (requested && ALLOWED_TABS.includes(requested)) {
      setActiveTab(requested);
    }
  }, []);

  useEffect(() => {
    const qp = new URLSearchParams(window.location.search);
    qp.set('activeTab', activeTab);
    const next = `${window.location.pathname}?${qp.toString()}`;
    window.history.replaceState({}, '', next);
  }, [activeTab]);

  function navigateTo(tab: string) {
    setActiveTab(tab as TabId);
  }

  const pageTitle = TAB_LABEL[activeTab] ?? 'TAAIP';
  const pageAccess = canAccessPage(activeTab as any);
  const { exportPdf } = usePageExport(activeTab, pageTitle);

  useEffect(() => {
    logAuditEvent({
      eventType: 'login',
      actor: 'taaip.engine',
      message: 'Session initialized in enterprise shell',
      target: 'app-shell',
    });
    seedOperationalAlerts();
    void runAllIngestionModules();
    const unsub = subscribeNotifications((items) => {
      items
        .filter((item) => item.severity === 'critical' && !item.read && !seenCritical.current.has(item.id))
        .forEach((item) => {
          seenCritical.current.add(item.id);
          pushToast('error', `${item.title}: ${item.message}`);
        });
    });
    return () => {
      unsub();
    };
  }, [pushToast]);

  useEffect(() => {
    logAuditEvent({
      eventType: 'page_access',
      actor: 'taaip.engine',
      message: `Visited enterprise page ${activeTab}`,
      target: activeTab,
    });
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-[#081B33] flex text-[#F3F5F7] font-['Inter',sans-serif]">
      <Sidebar activeTab={activeTab} onNavigate={(tab) => setActiveTab(tab)} />

      <div className="flex-1 min-w-0 flex flex-col">
        {/* Top header bar */}
        <header className="bg-[#060F1E] border-b border-[#1D3A5C] px-6 py-2.5 flex items-center justify-between flex-shrink-0">
          <span className="text-[13px] font-semibold uppercase tracking-[0.1em] text-[#94A3B8]">
            {pageTitle}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                void exportPdf({ page: activeTab, generatedAt: new Date().toISOString() });
              }}
              className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-2.5 py-1.5 text-[11px] uppercase tracking-[0.08em] text-[#CBD5E1] hover:bg-[#122A4A]"
            >
              Export Page
            </button>
            <GlobalNotificationCenter />
            <span className="text-[11px] text-[#64748B] uppercase tracking-[0.08em]">
              TAAIP v2.0 &nbsp;|&nbsp; {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit' })}
            </span>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-5 bg-[#081B33]">
          <ErrorBoundary>
            <Suspense fallback={
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-[#1D4ED8]" />
                  <p className="mt-3 text-[#64748B] text-sm">Loading…</p>
                </div>
              </div>
            }>
              {!pageAccess ? (
                <div className="rounded border border-red-900 bg-red-950/30 p-4 text-sm text-red-200">
                  Access denied for this role/tier profile.
                </div>
              ) : (
              activeTab === 'home-page' ? <HomePage onNavigate={navigateTo} /> :
               activeTab === 'command-center' ? <CommandCenterPage onNavigate={navigateTo} /> :
               activeTab === 'fusion-cell' ? <FusionCellPage /> :
               activeTab === 'twg' ? <TWGPage /> :
               activeTab === 'targeting-board' ? <TargetingBoardPage /> :
               activeTab === 'operations-page' ? <OperationsPage /> :
               activeTab === 'field-activities-page' ? <FieldActivitiesPage /> :
               activeTab === 'budget-page' ? <BudgetPage /> :
               activeTab === 'market-intelligence' ? <MarketIntelligenceEnterprisePage onNavigate={navigateTo} /> :
               activeTab === 'school-intelligence' ? <SchoolIntelligencePage /> :
               activeTab === 'dod-market-share' ? <DODMarketSharePage /> :
               activeTab === 'segmentation' ? <SegmentationPage /> :
               activeTab === 'reserve-alignment' ? <ReserveAlignmentPage /> :
               activeTab === 'market-potential' ? <MarketPotentialPage /> :
               activeTab === 'out-of-area-analysis' ? <OutOfAreaAnalysisPage /> :
               activeTab === 'roi-analysis' ? <ROIAnalysisPage /> :
               activeTab === 'performance-page' ? <PerformancePage /> :
               activeTab === 'funnel-analysis' ? <FunnelAnalysisPage /> :
               activeTab === 'data-document-center' ? <DataDocumentCenterPage /> :
               activeTab === 'training-center' ? <TrainingCenterPage /> :
               activeTab === 'admin' ? <AdminPage /> :
               <HomePage onNavigate={navigateTo} />
              )}
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};

export default App;
