import { useMemo } from 'react';
import { EnterprisePageId, ENTERPRISE_PAGES } from '../config/enterprisePages';
import { ROLE_TEMPLATES, User, hasPermission } from '../types/auth';
import { canAccessEnterprisePage, getAccessProfileForUser } from '../lib/auth';

const DEV_USER: User = {
  user_id: 'dev-user',
  username: 'taaip.engine',
  email: 'taaip.engine@local',
  position: '420T',
  unit_id: 'USAREC',
  created_at: new Date().toISOString(),
  is_active: true,
  role: ROLE_TEMPLATES.TIER_4_GLOBAL,
};

export const useEnterpriseAccess = () => {
  const user = DEV_USER;
  const accessProfile = useMemo(() => getAccessProfileForUser(user), [user]);

  const canAccessPage = useMemo(() => {
    return (pageId: EnterprisePageId) => {
      const def = ENTERPRISE_PAGES.find((p) => p.id === pageId);
      if (!def) {
        return false;
      }
      const permissionAllowed = def.requiredPermissions.every((perm) => hasPermission(user, perm));
      const roleAllowed = canAccessEnterprisePage(user, pageId);
      return permissionAllowed && roleAllowed;
    };
  }, [user]);

  return { user, canAccessPage, accessProfile };
};
