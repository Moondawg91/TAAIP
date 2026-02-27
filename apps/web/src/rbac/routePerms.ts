const routePerms: { [path: string]: string } = {
  '/admin': 'ADMIN_MANAGE_USERS',
  '/admin/roles': 'ADMIN_MANAGE_ROLES',
  '/admin/permissions': 'ADMIN_MANAGE_ROLES',
  '/data-hub': 'DATAHUB_READ',
  '/command-center': 'DASHBOARDS_READ',
  '/helpdesk': 'HELPDESK_READ',
  '/reports': 'DASHBOARDS_READ',
  '/scoreboard': 'DASHBOARDS_READ',
  '/data-hub/imports': 'DATAHUB_UPLOAD',
  '/data-hub/uploads': 'DATAHUB_UPLOAD',
  '/data-hub/runs': 'DATAHUB_VIEW_RUNS',
  '/planning': 'PLANNING_READ',
  '/planning/board': 'PLANNING_EDIT',
  '/events': 'EVENTS_VIEW',
  '/events/new': 'EVENTS_EDIT',
  '/budgets': 'BUDGET_VIEW',
  '/budgets/edit': 'BUDGET_EDIT',
}

export default routePerms
