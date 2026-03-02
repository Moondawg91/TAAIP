const routePerms: { [path: string]: string } = {
  '/admin': 'ADMIN_USERS',
  '/admin/roles': 'ADMIN_USERS',
  '/admin/permissions': 'ADMIN_USERS',
  '/data-hub': 'DASHBOARD_READ',
  '/command-center': 'DASHBOARD_READ',
  '/helpdesk': 'HELP_TICKET_READ',
  '/reports': 'DASHBOARD_READ',
  '/scoreboard': 'DASHBOARD_READ',
  '/data-hub/imports': 'DATA_UPLOAD',
  '/data-hub/uploads': 'DATA_UPLOAD',
  '/data-hub/runs': 'DASHBOARD_READ',
  '/command/mission-feasibility': 'DASHBOARD_READ',
  '/planning': 'DASHBOARD_READ',
  '/planning/board': 'PLANNING_EDIT',
  '/events': 'DASHBOARD_READ',
  '/events/new': 'PLANNING_EDIT',
  '/budgets': 'DASHBOARD_READ',
  '/budgets/edit': 'PLANNING_EDIT',
}

export default routePerms
