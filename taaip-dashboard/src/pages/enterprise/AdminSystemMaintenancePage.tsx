import React from 'react';
import { AlertTriangle, ShieldCheck, Activity, Bell } from 'lucide-react';
import { Card, KPIRow, Table } from '../../components/shared/ui';
import AdminConsole from '../../components/AdminConsole';
import { HelpDeskPortal } from '../../components/HelpDeskPortal';

const HEALTH = [
  { service: 'API Gateway', status: 'Healthy', latency: '81ms', sync: 'In Sync' },
  { service: 'Ingestion Pipeline', status: 'Warning', latency: 'N/A', sync: 'Lag +5m' },
  { service: 'Audit Logger', status: 'Healthy', latency: '34ms', sync: 'In Sync' },
  { service: 'Export Engine (PDF/PPT)', status: 'Healthy', latency: '113ms', sync: 'In Sync' },
];

const ALERTS = [
  { id: 'a1', type: 'Maintenance Warning', detail: 'SharePoint sync delay exceeds threshold.' },
  { id: 'a2', type: 'System Alert', detail: 'Vantage ingestion queue depth elevated.' },
  { id: 'a3', type: 'Audit Notice', detail: 'Role permission changes pending commander review.' },
];

export const AdminSystemMaintenancePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <KPIRow
        items={[
          { label: 'API Health', value: '99.7%' },
          { label: 'Sync Health', value: '97.9%' },
          { label: 'Open Maintenance Warnings', value: '2' },
          { label: 'Audit Events (24h)', value: '146' },
        ]}
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card title="System Governance" action={<ShieldCheck className="w-4 h-4 text-emerald-400" />}>
          <ul className="text-sm text-slate-300 space-y-2">
            <li>Permissions management and role delegation</li>
            <li>Routing controls and page authorization policy</li>
            <li>Backup scheduling and restore checkpoints</li>
            <li>Enterprise audit behavior hooks</li>
          </ul>
        </Card>

        <Card title="Ingestion & API Monitoring" action={<Activity className="w-4 h-4 text-cyan-400" />}>
          <p className="text-sm text-slate-300">Monitors Vantage, AIE, DoD component, and SharePoint sync state.</p>
        </Card>

        <Card title="Alerts & Notifications" action={<Bell className="w-4 h-4 text-amber-300" />}>
          <div className="space-y-2">
            {ALERTS.map((alert) => (
              <div key={alert.id} className="text-sm border border-slate-700 rounded px-3 py-2 bg-slate-900/40">
                <div className="font-semibold text-slate-200">{alert.type}</div>
                <div className="text-slate-300">{alert.detail}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="System Health & Sync Monitoring" action={<AlertTriangle className="w-4 h-4 text-amber-400" />}>
        <Table
          rows={HEALTH}
          columns={[
            { key: 'service', header: 'Service' },
            { key: 'status', header: 'Status' },
            { key: 'latency', header: 'Latency' },
            { key: 'sync', header: 'Sync State' },
          ]}
          getRowId={(row) => row.service}
        />
      </Card>

      <AdminConsole />
      <HelpDeskPortal />
    </div>
  );
};

export default AdminSystemMaintenancePage;
