const ROUTES_REGISTRY = [
  {
    id: 'dashboards',
    label: 'Dashboard',
    icon: 'Dashboard',
    items: [
      { id: 'main-dashboard', label: 'Dashboard', path: '/dashboard', icon: 'Dashboard' }
    ]
  },
  {
    id: 'command-center',
    label: 'TAAIP',
    icon: 'Dashboard',
    items: [
      { id: '420t', label: '420T Command Center', path: '/command-center', icon: 'Dashboard' },
      { id: 'fusion', label: 'Fusion Cell', path: '/command-center/fusion-cell', icon: 'Groups' },
      { id: 'twg', label: 'Targeting Working Group (TWG)', path: '/command-center/twg', icon: 'Hub' },
      { id: 'intel', label: 'Analytics & Intelligence', path: '/command-center/intel', icon: 'Analytics' },
      { id: 'fusion-briefing', label: 'Fusion Briefing', path: '/command-center/fusion-briefing', icon: 'GridView' },
      { id: 'recruiting-ops', label: 'Recruiting Operations Plan/Program', path: '/command-center/recruiting-ops', icon: 'Work' },
      { id: 'priorities', label: 'Command Priorities', path: '/command-center/priorities', icon: 'Flag' },
      { id: 'mission-assess', label: 'Mission Assessment', path: '/command-center/mission-assessment', icon: 'Assessment' }
      ,{ id: 'mission-feasibility', label: 'Mission Feasibility', path: '/command-center/feasibility', icon: 'Analytics' }
        ,{ id: 'fs-loss', label: 'FS Loss', path: '/command-center/fs-loss', icon: 'Report' }
    ]
  },
  {
    id: 'operations',
    label: 'Operations',
    icon: 'TrackChanges',
    items: [
      { id: 'operations-home', label: 'Operations', path: '/ops', icon: 'TrackChanges' },
      { id: 'mission-analysis', label: 'Mission Analysis', path: '/operations/mission-analysis', icon: 'ManageSearch' },
      { id: 'mission-planning', label: 'Mission Planning', path: '/operations/mission-planning', icon: 'Map' },
      { id: 'targeting-method', label: 'USAREC Targeting Methodology', path: '/operations/targeting-methodology', icon: 'MilitaryTech' },
      { id: 'phonetics', label: 'Processing', path: '/operations/phonetics', icon: 'RecordVoiceOver' },
      { id: 'event-performance', label: 'Event Performance', path: '/operations/event-performance', icon: 'Event' }
    ]
  },
  {
    id: 'planning',
    label: 'Planning',
    icon: 'Build',
    items: [
      { id: 'projects-events', label: 'Project & Event Management', path: '/planning/projects-events', icon: 'PlaylistAddCheck' },
      
      // TWG and Fusion are surfaced under Command Center per TOR; planning keeps aliases hidden
      { id: 'engagement-roi', label: 'Engagement / ROI Analysis', path: '/roi', icon: 'TrendingUp' },
      { id: 'asset-management', label: 'Asset Management', path: '/planning/asset-management', icon: 'Inventory' },
      { id: 'community-engagement', label: 'Community Engagement', path: '/planning/community-engagement', icon: 'Handshake' },
      { id: 'targeting-board', label: 'Targeting Board', path: '/planning/targeting-board', icon: 'TableChart' },
      { id: 'calendar', label: 'Calendar / Scheduling', path: '/planning/calendar', icon: 'CalendarMonth' }
    ]
  },
  {
    id: 'school',
    label: 'School Recruiting',
    icon: 'School',
    items: [
      
      { id: 'school-program', label: 'Program', path: '/school-recruiting/program', icon: 'Campaign' },
      { id: 'school-compliance-activities', label: 'Compliance & Activities', path: '/school/compliance', icon: 'Gavel' },
      { id: 'school-leadflow', label: 'Lead Flow', path: '/school/leadflow', icon: 'ContactMail' },
      { id: 'school-calendar', label: 'Calendar & Milestones', path: '/school/calendar', icon: 'CalendarMonth' }
    ]
  },
  {
    id: 'performance',
    label: 'Performance Tracking',
    icon: 'Assessment',
    items: [
      { id: 'production', label: 'Production Dashboard', path: '/performance/production-dashboard', icon: 'DashboardCustomize' },
      { id: 'market-seg', label: 'Market Segmentation', path: '/performance/market-segmentation', icon: 'ScatterPlot' },
      { id: 'funnel-metrics', label: 'Funnel Metrics', path: '/performance/funnel-metrics', icon: 'Funnels' },
      { id: 'recruiting-analytics', label: 'Recruiting Analytics', path: '/performance/recruiting-analytics', icon: 'Insights' }
    ]
  },
  {
    id: 'budget',
    label: 'Budget',
    icon: 'AccountBalance',
    items: [
      { id: 'budget-tracker', label: 'Budget Tracker', path: '/budget/tracker', icon: 'AccountBalanceWallet' },
      { id: 'roi-overview', label: 'ROI Overview', path: '/budget/roi-overview', icon: 'TrendingUp' },
      { id: 'funding', label: 'Funding Allocations', path: '/budget/funding-allocations', icon: 'AttachMoney' }
    ]
  },
  {
    id: 'administration',
    label: 'Administration',
    icon: 'AdminPanelSettings',
    items: [
      { id: 'user-management', label: 'User Management', path: '/admin/users', icon: 'People' },
      { id: 'roles', label: 'Role & Echelon Control', path: '/admin/roles', icon: 'Security' },
      { id: 'system-config', label: 'System Configuration', path: '/admin/config', icon: 'Settings' },
      { id: 'system-self-check', label: 'System Self-Check', path: '/admin/system-self-check', icon: 'HealthAndSafety' }
    ]
  },
  {
    id: 'resources',
    label: 'Resources & Training',
    icon: 'MenuBook',
    items: [
      { id: 'doc-library', label: 'Document Library', path: '/resources/doc-library', icon: 'Description' },
      { id: 'regulations', label: 'Regulations', path: '/resources/regulations', icon: 'Gavel' },
      { id: 'regulatory-registry', label: 'Regulatory Registry', path: '/resources/regulatory', icon: 'Gavel' },
      { id: 'manuals', label: 'Manuals', path: '/resources/manuals', icon: 'MenuBook' },
      { id: 'sops', label: 'SOPs', path: '/resources/sops', icon: 'Article' },
      { id: 'training', label: 'Training Modules', path: '/resources/training', icon: 'School' },
      { id: 'data-hub', label: 'Data Hub', path: '/data-hub', icon: 'Storage' },
      { id: 'user-manual', label: 'User Manual', path: '/resources/user-manual', icon: 'ImportContacts' }
    ]
  },
  {
    id: 'helpdesk',
    label: 'Help Desk',
    icon: 'SupportAgent',
    items: [
      { id: 'submit-ticket', label: 'Submit Ticket', path: '/help/submit-ticket', icon: 'AddComment' },
      { id: 'ticket-status', label: 'Ticket Status', path: '/help/ticket-status', icon: 'ListAlt' },
      { id: 'system-status', label: 'System Status', path: '/help/system-status', icon: 'SettingsSystemDaydream' }
    ]
  }
]

export default ROUTES_REGISTRY
