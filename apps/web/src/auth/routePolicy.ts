import permissions from './permissions'

export type RoutePolicy = {
  path: string
  requiredAll?: string[]
  requiredAny?: string[]
  navSection?: string
  navLabel?: string
  hideFromNav?: boolean
  dashboardPage?: boolean
  showTopFilters?: boolean
  filters?: { unit?: boolean; fy?: boolean; qtr?: boolean; compare?: boolean }
}

const ROUTE_POLICIES: RoutePolicy[] = [
  // Home should not display TopFilters; dashboards are under /command-center and related paths
  { path: '/', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: false, showTopFilters: false, filters: { unit: true, fy: true, qtr: true }, navSection: 'command' },
  { path: '/command-center', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'command' },
  { path: '/planning', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'planning' },
  { path: '/planning/calendar', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'planning' },
  { path: '/command-center/twg', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'command' },
  { path: '/roi', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true, compare: true }, navSection: 'roi' },
  { path: '/roi/events', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true, compare: true }, navSection: 'roi' },
  { path: '/operations/funnel', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'ops' },
  { path: '/operations/productivity', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'ops' },
  { path: '/operations/processing', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'ops' },
  { path: '/market-intel', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'ops' },
  { path: '/schools', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'schools' },
  { path: '/budget', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: true, showTopFilters: true, filters: { unit: true, fy: true, qtr: true }, navSection: 'budget' },
  { path: '/data-hub', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: false, showTopFilters: false, navSection: 'datahub' },
  { path: '/data-hub/imports', requiredAny: [permissions.DATA_UPLOAD], dashboardPage: false, showTopFilters: false, navSection: 'datahub' },
  { path: '/help/submit-ticket', requiredAny: [permissions.HELP_TICKET_CREATE], dashboardPage: false, showTopFilters: false, navSection: 'helpdesk' },
  { path: '/help/ticket-status', requiredAny: [permissions.HELP_TICKET_READ], dashboardPage: false, showTopFilters: false, navSection: 'helpdesk' },
  { path: '/system-status', requiredAny: [permissions.DASHBOARD_READ], dashboardPage: false, showTopFilters: false, navSection: 'helpdesk' },
  { path: '/admin', requiredAny: [permissions.ADMIN_USERS], dashboardPage: false, showTopFilters: false, navSection: 'administration' },
  { path: '/admin/users', requiredAny: [permissions.ADMIN_USERS], dashboardPage: false, showTopFilters: false, navSection: 'administration' },
]

export default ROUTE_POLICIES
