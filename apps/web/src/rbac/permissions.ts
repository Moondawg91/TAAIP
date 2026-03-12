// Centralized permission key constants (canonical keys)
const Permissions = {
  BASE_APP_READ: 'app.read',
  BASE_APP_EXPORT: 'app.export',

  // Data Hub
  DATAHUB_VIEW: 'datahub.view',
  DATAHUB_UPLOAD_RAW: 'datahub.upload_raw',
  DATAHUB_MANAGE_REGISTRY: 'datahub.manage_registry',
  DATAHUB_VIEW_RUNS: 'datahub.view_runs',

  // Command / Analytics
  COMMANDCENTER_VIEW: 'commandcenter.view',
  MARKETINTEL_VIEW: 'marketintel.view',
  OPERATIONS_VIEW: 'operations.view',
  ROI_VIEW: 'roi.view',
  ROI_VIEW_DETAIL: 'roi.view_detail',

  // Planning / Events / Assets
  PLANNING_VIEW: 'planning.view',
  PLANNING_EDIT: 'planning.edit',
  EVENTS_VIEW: 'events.view',
  EVENTS_EDIT: 'events.edit',
  ASSETS_VIEW: 'assets.view',
  ASSETS_EDIT: 'assets.edit',

  // School Recruiting
  SCHOOLS_VIEW: 'schools.view',
  SCHOOLS_EDIT: 'schools.edit',

  // Budget
  BUDGET_VIEW: 'budget.view',
  BUDGET_EDIT: 'budget.edit',

  // Helpdesk
  HELPDESK_VIEW: 'helpdesk.view',
  HELPDESK_SUBMIT: 'helpdesk.submit',
  HELPDESK_MANAGE: 'helpdesk.manage',

  // Admin
  ADMIN_VIEW: 'admin.view',
  ADMIN_USERS_MANAGE: 'admin.users.manage',
  ADMIN_ROLES_MANAGE: 'admin.roles.manage',
  ADMIN_AUDIT_VIEW: 'admin.audit.view'
}

export default Permissions
