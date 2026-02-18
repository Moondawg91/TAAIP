const NAV_CONFIG = [
  // 1. Command Center
  {
    id: 'command-center',
    label: 'Command Center',
    icon: 'Dashboard',
    items: [
      { id: '420t', label: '420T Command Center', path: '/command-center', icon: 'Dashboard', disabled: false },
      { id: 'fusion', label: 'Fusion Cell', path: '/command-center/fusion-cell', icon: 'Groups', disabled: true },
      { id: 'twg', label: 'Targeting Working Group (TWG)', path: '/command-center/twg', icon: 'Hub', disabled: true },
      { id: 'intel', label: 'Analytics & Intelligence', path: '/command-center/intel', icon: 'Analytics', disabled: true },
      { id: 'recruiting-ops', label: 'Recruiting Operations Plan/Program', path: '/command-center/recruiting-ops', icon: 'Work', disabled: true },
      { id: 'priorities', label: 'Command Priorities', path: '/command-center/priorities', icon: 'Flag', disabled: false },
      { id: 'mission-assess', label: 'Mission Assessment', path: '/command-center/mission-assessment', icon: 'Assessment', disabled: false }
    ]
  },

  // 2. Operations
  {
    id: 'operations',
    label: 'Operations',
    icon: 'TrackChanges',
    items: [
      { id: 'mission-analysis', label: 'Mission Analysis', path: '/operations/mission-analysis', icon: 'ManageSearch', disabled: true },
      { id: 'mission-planning', label: 'Mission Planning', path: '/operations/mission-planning', icon: 'Map', disabled: false },
      { id: 'targeting-method', label: 'USAREC Targeting Methodology', path: '/operations/targeting-methodology', icon: 'MilitaryTech', disabled: false },
      { id: 'targeting-data', label: 'Targeting Data', path: '/operations/targeting-data', icon: 'Storage', disabled: false },
      { id: 'marketing-roi', label: 'Marketing & Advertisement ROI', path: '/operations/marketing-roi', icon: 'Campaign', disabled: true },
      { id: 'event-performance', label: 'Event Performance', path: '/operations/event-performance', icon: 'Event', disabled: true }
    ]
  },

  // 3. Planning
  {
    id: 'planning',
    label: 'Planning',
    icon: 'Build',
    items: [
      { id: 'projects-events', label: 'Project & Event Management', path: '/planning/projects-events', icon: 'PlaylistAddCheck', disabled: false },
      { id: 'asset-management', label: 'Asset Management', path: '/planning/asset-management', icon: 'Inventory', disabled: true },
      { id: 'community-engagement', label: 'Community Engagement', path: '/planning/community-engagement', icon: 'Handshake', disabled: true },
      { id: 'env-reco', label: 'Environmental Recommendation Engine', path: '/planning/env-recommendation', icon: 'AutoMode', disabled: true },
      { id: 'targeting-board', label: 'Targeting Board', path: '/planning/targeting-board', icon: 'TableChart', disabled: false },
      { id: 'calendar', label: 'Calendar / Scheduling', path: '/planning/calendar', icon: 'CalendarMonth', disabled: false }
    ]
  },

  // 4. School Recruiting
  {
    id: 'school',
    label: 'School Recruiting',
    icon: 'School',
    items: [
      { id: 'school-landing', label: 'School Recruiting Program', path: '/school-recruiting', icon: 'School', disabled: false }
    ]
  },

  // 5. Performance Tracking
  {
    id: 'performance',
    label: 'Performance Tracking',
    icon: 'Assessment',
    items: [
      { id: 'production', label: 'Production Dashboard', path: '/performance/production-dashboard', icon: 'DashboardCustomize', disabled: true },
      { id: 'market-seg', label: 'Market Segmentation', path: '/performance/market-segmentation', icon: 'ScatterPlot', disabled: true },
      { id: 'funnel-metrics', label: 'Funnel Metrics', path: '/performance/funnel-metrics', icon: 'Funnels', disabled: true },
      { id: 'recruiting-analytics', label: 'Recruiting Analytics', path: '/performance/recruiting-analytics', icon: 'Insights', disabled: true }
    ]
  },

  // 6. Budget
  {
    id: 'budget',
    label: 'Budget',
    icon: 'AccountBalance',
    items: [
      { id: 'budget-tracker', label: 'Budget Tracker', path: '/budget/tracker', icon: 'AccountBalanceWallet', disabled: false },
      { id: 'roi-overview', label: 'ROI Overview', path: '/budget/roi-overview', icon: 'TrendingUp', disabled: true },
      { id: 'funding', label: 'Funding Allocations', path: '/budget/funding-allocations', icon: 'AttachMoney', disabled: true }
    ]
  },

  // 7. Administration
  {
    id: 'administration',
    label: 'Administration',
    icon: 'AdminPanelSettings',
    items: [
      { id: 'user-management', label: 'User Management', path: '/admin/users', icon: 'People', disabled: true },
      { id: 'roles', label: 'Role & Scope Control', path: '/admin/roles', icon: 'Security', disabled: true },
      { id: 'system-config', label: 'System Configuration', path: '/admin/config', icon: 'Settings', disabled: true },
      { id: 'data-imports', label: 'Data Imports', path: '/admin/data-imports', icon: 'UploadFile', disabled: true }
    ]
  },

  // 8. Resources & Training
  {
    id: 'resources',
    label: 'Resources & Training',
    icon: 'MenuBook',
    items: [
      { id: 'doc-library', label: 'Document Library', path: '/resources/doc-library', icon: 'Description', disabled: false },
      { id: 'regulations', label: 'Regulations', path: '/resources/regulations', icon: 'Gavel', disabled: false },
      { id: 'manuals', label: 'Manuals', path: '/resources/manuals', icon: 'MenuBook', disabled: true },
      { id: 'sops', label: 'SOPs', path: '/resources/sops', icon: 'Article', disabled: true },
      { id: 'training', label: 'Training Modules', path: '/resources/training', icon: 'School', disabled: true },
      { id: 'user-manual', label: 'User Manual', path: '/resources/user-manual', icon: 'ImportContacts', disabled: true }
    ]
  },

  // 9. Help Desk
  {
    id: 'helpdesk',
    label: 'Help Desk',
    icon: 'SupportAgent',
    items: [
      { id: 'submit-ticket', label: 'Submit Ticket', path: '/help/submit-ticket', icon: 'AddComment', disabled: false },
      { id: 'ticket-status', label: 'Ticket Status', path: '/help/ticket-status', icon: 'ListAlt', disabled: false },
      { id: 'system-status', label: 'System Status', path: '/help/system-status', icon: 'SettingsSystemDaydream', disabled: false }
    ]
  }
]

export default NAV_CONFIG
