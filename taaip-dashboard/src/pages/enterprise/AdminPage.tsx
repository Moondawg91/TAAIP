import React, { useEffect, useMemo, useState } from 'react';
import { Card } from '../../components/shared/ui';
import { UserManagement } from '../../components/UserManagement';
import { HelpDeskPortal } from '../../components/HelpDeskPortal';
import { SystemControlPage } from '../../components/SystemControlPage';
import GovernanceDashboard from '../../components/GovernanceDashboard';
import AuditLogAdmin from '../../components/AuditLogAdmin';
import { useEnterpriseAccess } from '../../hooks/useEnterpriseAccess';
import OperationalHealthPanel from '../../components/admin/OperationalHealthPanel';
import { logAuditEvent } from '../../lib/audit/controller';

type AdminModule =
  | 'User & Role Management'
  | 'Helpdesk / Support Tickets'
  | 'System Control'
  | 'Database Management'
  | 'System Update Logs'
  | 'System Backup'
  | 'Data Ingestion Monitor'
  | 'API Connection Health'
  | 'Audit Reports'
  | 'System Maintenance';

const MODULES: AdminModule[] = [
  'User & Role Management',
  'Helpdesk / Support Tickets',
  'System Control',
  'Database Management',
  'System Update Logs',
  'System Backup',
  'Data Ingestion Monitor',
  'API Connection Health',
  'Audit Reports',
  'System Maintenance',
];

export const AdminPage: React.FC = () => {
  const [active, setActive] = useState<AdminModule>('System Control');
  const { user, accessProfile } = useEnterpriseAccess();

  useEffect(() => {
    logAuditEvent({
      eventType: 'system_config_change',
      actor: user.username,
      message: `Admin module opened: ${active}`,
      target: active,
    });
  }, [active, user.username]);

  const content = useMemo(() => {
    if (active === 'User & Role Management') return <UserManagement currentUser={user} />;
    if (active === 'Helpdesk / Support Tickets') return <HelpDeskPortal />;
    if (active === 'System Control') return <OperationalHealthPanel user={user} />;
    if (active === 'Database Management') return <GovernanceDashboard />;
    if (active === 'System Update Logs') return <OperationalHealthPanel user={user} />;
    if (active === 'System Backup') return <OperationalHealthPanel user={user} />;
    if (active === 'Audit Reports') return <div className="space-y-4"><OperationalHealthPanel user={user} /><AuditLogAdmin /></div>;
    if (active === 'System Maintenance') return <OperationalHealthPanel user={user} />;
    if (active === 'Data Ingestion Monitor') return <OperationalHealthPanel user={user} />;
    if (active === 'API Connection Health') return <OperationalHealthPanel user={user} />;
    return <div className="text-sm text-slate-500">Select a module.</div>;
  }, [active, user]);

  return (
    <div className="space-y-6">
      <Card title="Admin Access Profile">
        <div className="text-sm text-slate-300">
          Role {accessProfile.role} | Tier {accessProfile.tier}
        </div>
      </Card>
      <Card title="Administration Launcher">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {MODULES.map((m) => (
            <button
              key={m}
              onClick={() => setActive(m)}
              className={`text-left px-4 py-3 rounded border text-sm ${active === m ? 'border-blue-500 bg-blue-950/30 text-blue-200' : 'border-slate-700 text-slate-300 hover:bg-slate-900/40'}`}
            >
              {m}
            </button>
          ))}
        </div>
      </Card>

      <Card title={active}>{content}</Card>
    </div>
  );
};

export default AdminPage;
