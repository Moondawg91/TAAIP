// Authentication and Authorization Types

export type AccessTier = 'tier-4-global' | 'tier-3-admin' | 'tier-2-manager' | 'tier-1-user' | 'tier-0-readonly';

export type Permission = 
  // Dashboard Access
  | 'view_all_dashboards'
  | 'view_own_company_only'
  | 'view_analytics'
  | 'view_market_data'
  | 'view_mission_analysis'
  
  // Data Management
  | 'upload_data'
  | 'edit_data'
  | 'delete_data'
  | 'export_data'
  
  // Targeting
  | 'create_events'
  | 'approve_events'
  | 'edit_events'
  | 'delete_events'
  | 'view_twg'
  | 'manage_twg'
  | 'view_tdb'
  | 'manage_tdb'
  
  // Team Management
  | 'view_team'
  | 'assign_roles'
  | 'manage_users'
  | 'delegate_permissions'
  
  // Budget
  | 'view_budget'
  | 'edit_budget'
  | 'approve_budget'
  
  // System
  | 'system_admin'
  | 'manage_integrations'
  | 'view_audit_logs';

export interface UserRole {
  role_id: string;
  role_name: string;
  tier: AccessTier;
  permissions: Permission[];
  description: string;
}

export interface User {
  user_id: string;
  username: string;
  email: string;
  rank?: string;
  position: string; // XO, 420T, Company Commander, Station Commander, Recruiter
  unit_id: string;
  company_id?: string;
  role: UserRole;
  custom_permissions?: Permission[]; // Additional permissions delegated by admin
  created_by?: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

// Predefined Role Templates
export const ROLE_TEMPLATES: Record<string, UserRole> = {
  TIER_4_GLOBAL: {
    role_id: 'tier-4-global',
    role_name: 'Global Administrator',
    tier: 'tier-4-global',
    permissions: [
      'view_all_dashboards',
      'view_analytics',
      'view_market_data',
      'view_mission_analysis',
      'upload_data',
      'edit_data',
      'delete_data',
      'export_data',
      'create_events',
      'approve_events',
      'edit_events',
      'delete_events',
      'view_twg',
      'manage_twg',
      'view_tdb',
      'manage_tdb',
      'view_team',
      'assign_roles',
      'manage_users',
      'delegate_permissions',
      'view_budget',
      'edit_budget',
      'approve_budget',
      'system_admin',
      'manage_integrations',
      'view_audit_logs'
    ],
    description: 'Full system access - controls everything, can delegate any permission'
  },
  
  TIER_3_420T_ADMIN: {
    role_id: 'tier-3-admin',
    role_name: '420T System Administrator',
    tier: 'tier-3-admin',
    permissions: [
      'view_all_dashboards',
      'view_analytics',
      'view_market_data',
      'view_mission_analysis',
      'upload_data',
      'edit_data',
      'export_data',
      'create_events',
      'approve_events',
      'edit_events',
      'view_twg',
      'manage_twg',
      'view_tdb',
      'manage_tdb',
      'view_team',
      'assign_roles',
      'manage_users',
      'view_budget',
      'edit_budget',
      'view_audit_logs'
    ],
    description: 'Battalion-level admin - manages users, roles, and all data. Cannot delete events or manage system integrations.'
  },
  
  TIER_2_XO_MANAGER: {
    role_id: 'tier-2-xo',
    role_name: 'Battalion XO / Manager',
    tier: 'tier-2-manager',
    permissions: [
      'view_all_dashboards',
      'view_analytics',
      'view_market_data',
      'view_mission_analysis',
      'export_data',
      'approve_events',
      'edit_events',
      'view_twg',
      'manage_twg',
      'view_tdb',
      'manage_tdb',
      'view_team',
      'view_budget',
      'approve_budget'
    ],
    description: 'Decision-maker - approves events, manages TWG/TDB, views all battalion data'
  },
  
  TIER_2_COMPANY_COMMANDER: {
    role_id: 'tier-2-company',
    role_name: 'Company Commander',
    tier: 'tier-2-manager',
    permissions: [
      'view_own_company_only',
      'view_analytics',
      'view_market_data',
      'view_mission_analysis',
      'export_data',
      'create_events',
      'edit_events',
      'view_twg',
      'view_tdb',
      'view_team',
      'view_budget'
    ],
    description: 'Company-level manager - creates/edits events for own company, views own data'
  },
  
  TIER_1_MMA_S3: {
    role_id: 'tier-1-staff',
    role_name: 'Staff (MMA/S3/ESS/APA)',
    tier: 'tier-1-user',
    permissions: [
      'view_all_dashboards',
      'view_analytics',
      'view_market_data',
      'view_mission_analysis',
      'upload_data',
      'edit_data',
      'export_data',
      'create_events',
      'edit_events',
      'view_twg',
      'view_tdb',
      'view_team',
      'view_budget'
    ],
    description: 'Battalion staff - full data access, can create/edit events, participates in TWG/TDB'
  },
  
  TIER_1_STATION_COMMANDER: {
    role_id: 'tier-1-station',
    role_name: 'Station Commander',
    tier: 'tier-1-user',
    permissions: [
      'view_own_company_only',
      'view_analytics',
      'view_market_data',
      'export_data',
      'create_events',
      'view_team',
      'view_budget'
    ],
    description: 'Station-level leader - views own data, creates events for own area'
  },
  
  TIER_0_RECRUITER: {
    role_id: 'tier-0-readonly',
    role_name: 'Recruiter',
    tier: 'tier-0-readonly',
    permissions: [
      'view_own_company_only',
      'view_analytics',
      'view_market_data',
      'export_data'
    ],
    description: 'Read-only access - views own company data and analytics'
  }
};

// Permission hierarchy - higher tiers inherit lower tier permissions
export const TIER_HIERARCHY: Record<AccessTier, number> = {
  'tier-4-global': 4,
  'tier-3-admin': 3,
  'tier-2-manager': 2,
  'tier-1-user': 1,
  'tier-0-readonly': 0
};

// Helper function to check if user has permission
export function hasPermission(user: User, permission: Permission): boolean {
  // Check role permissions
  if (user.role.permissions.includes(permission)) {
    return true;
  }
  
  // Check custom delegated permissions
  if (user.custom_permissions?.includes(permission)) {
    return true;
  }
  
  // Tier 4 has all permissions
  if (user.role.tier === 'tier-4-global') {
    return true;
  }
  
  return false;
}

// Helper function to check if user can delegate permission
export function canDelegatePermission(user: User, permission: Permission): boolean {
  // Only Tier 4 and Tier 3 (420T) can delegate
  const userTierLevel = TIER_HIERARCHY[user.role.tier];
  if (userTierLevel < 3) {
    return false;
  }
  
  // Must have the permission themselves to delegate it
  if (!hasPermission(user, permission)) {
    return false;
  }
  
  // Tier 3 (420T) cannot delegate system admin permissions
  if (user.role.tier === 'tier-3-admin' && 
      (permission === 'system_admin' || permission === 'manage_integrations')) {
    return false;
  }
  
  return true;
}

// Helper function to check tier level comparison
export function hasTierAccess(user: User, requiredTier: AccessTier): boolean {
  const userLevel = TIER_HIERARCHY[user.role.tier];
  const requiredLevel = TIER_HIERARCHY[requiredTier];
  return userLevel >= requiredLevel;
}
