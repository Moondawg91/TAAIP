import React from 'react';
import { Card, Table } from '../../components/shared/ui';
import { useEnterpriseAccess } from '../../hooks/useEnterpriseAccess';

export const ProfilePage: React.FC = () => {
  const { user, accessProfile } = useEnterpriseAccess();

  const permissionRows = user.role.permissions.map((p) => ({ permission: p, delegated: user.custom_permissions?.includes(p) ? 'Yes' : 'No' }));

  return (
    <div className="space-y-6">
      <Card title="Profile">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-200">
          <div><span className="text-slate-400">Username:</span> {user.username}</div>
          <div><span className="text-slate-400">Email:</span> {user.email}</div>
          <div><span className="text-slate-400">Position:</span> {user.position}</div>
          <div><span className="text-slate-400">Visibility Tier:</span> {user.role.tier}</div>
          <div><span className="text-slate-400">Role:</span> {user.role.role_name}</div>
          <div><span className="text-slate-400">Unit:</span> {user.unit_id}</div>
        </div>
      </Card>

      <Card title="Permissions & Access Controls">
        <Table
          rows={permissionRows}
          columns={[
            { key: 'permission', header: 'Permission' },
            { key: 'delegated', header: 'Delegated Override' },
          ]}
          getRowId={(row) => row.permission}
        />
      </Card>

      <Card title="Operational Role + Tier Visibility">
        <div className="space-y-2 text-sm text-slate-300">
          <div><span className="text-slate-500">Operational Role:</span> {accessProfile.role}</div>
          <div><span className="text-slate-500">Visibility Tier:</span> {accessProfile.tier}</div>
          <div><span className="text-slate-500">Allowed Data Domains:</span> {accessProfile.allowedDataDomains.join(', ')}</div>
          <div><span className="text-slate-500">Allowed Pages:</span> {accessProfile.allowedPages.length}</div>
        </div>
      </Card>
    </div>
  );
};

export default ProfilePage;
