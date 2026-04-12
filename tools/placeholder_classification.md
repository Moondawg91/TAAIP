# Frontend Placeholder Classification

Scanned files rendering `NotLoadedPage` and classification decisions.

- apps/web/src/pages/budget/FundingAllocationsPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden (removed from nav)
- apps/web/src/pages/budget/RoiOverviewPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden (removed from nav)
- apps/web/src/pages/performance/RecruitingAnalyticsPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden
- apps/web/src/pages/performance/MarketSegmentationPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden
- apps/web/src/pages/performance/FunnelMetricsPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden
- apps/web/src/pages/command-center/TwgPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden
- apps/web/src/pages/command-center/PrioritiesPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden
- apps/web/src/pages/admin/SystemConfigPage.jsx: NotLoadedPage
  - Classification: must implement now for admin operations (leave in nav)
- apps/web/src/pages/resources/UserManualPage.jsx: NotLoadedPage
  - Classification: can be intentionally gated/hidden
- apps/web/src/pages/command/* and /operations/* contain several NotLoadedPage entries
  - Classification: gate/highlight based on team priorities; hidden by default

Notes:
- Changes made: high-impact user-facing placeholder pages removed from navigation registry to avoid clickable dead pages.
- Implementation approach: keep page source files intact; hide from nav so routes remain accessible via direct URL for developers/tests but not reachable via UI navigation.
