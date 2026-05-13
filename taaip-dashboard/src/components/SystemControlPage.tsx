import React, { useMemo, useState } from 'react';
import { RefreshCw } from 'lucide-react';

export type SystemControlTab =
  | 'activity_logs'
  | 'maintenance'
  | 'system_information'
  | 'update_logs'
  | 'audit_trail';

type SystemControlPageProps = {
  initialTab?: SystemControlTab;
  onBack?: () => void;
};

type ActivityLogRow = {
  time: string;
  user: string;
  action: string;
  details: string;
  ip_address: string;
};

type MaintenanceRow = {
  date: string;
  maintenance_window: string;
  type: string;
  description: string;
  status: string;
};

type UpdateLogRow = {
  version: string;
  date: string;
  update_type: string;
  summary: string;
  approved_by: string;
  status: string;
};

type AuditTrailRow = {
  time: string;
  user: string;
  module: string;
  action: string;
  record_affected: string;
  result: string;
};

const ACTIVITY_LOGS: ActivityLogRow[] = [
  { time: '2026-04-24 09:15:02', user: 'admin.user', action: 'Role Updated', details: 'Updated Recruiter role permissions', ip_address: '10.24.18.91' },
  { time: '2026-04-24 08:42:17', user: 'sys.ops', action: 'Service Restart', details: 'Restarted API service group', ip_address: '10.24.18.52' },
  { time: '2026-04-23 16:31:44', user: 'helpdesk.tier2', action: 'Ticket Resolved', details: 'Closed user access incident #HD-882', ip_address: '10.24.18.133' },
];

const MAINTENANCE_WINDOWS: MaintenanceRow[] = [
  { date: '2026-04-27', maintenance_window: '0200-0330 UTC', type: 'Security Patch', description: 'Apply monthly security updates and restart services', status: 'Scheduled' },
  { date: '2026-05-04', maintenance_window: '0100-0200 UTC', type: 'Database Maintenance', description: 'Index optimization and integrity checks', status: 'Scheduled' },
  { date: '2026-04-20', maintenance_window: '0200-0300 UTC', type: 'Platform Update', description: 'Completed platform service patch rollup', status: 'Completed' },
];

const UPDATE_LOGS: UpdateLogRow[] = [
  { version: 'v2.11.0', date: '2026-04-20', update_type: 'Platform', summary: 'Improved admin routing and audit retention policy defaults', approved_by: 'Platform Change Board', status: 'Deployed' },
  { version: 'v2.10.3', date: '2026-04-11', update_type: 'Security', summary: 'Session timeout hardening and dependency patching', approved_by: 'Security Control Officer', status: 'Deployed' },
  { version: 'v2.12.0-rc1', date: '2026-04-26', update_type: 'Feature', summary: 'Release candidate for control center enhancements', approved_by: 'Platform Change Board', status: 'Pending Approval' },
];

const AUDIT_TRAIL: AuditTrailRow[] = [
  { time: '2026-04-24 09:20:08', user: 'admin.user', module: 'Admin', action: 'Permission Change', record_affected: 'role:recruiter', result: 'Success' },
  { time: '2026-04-24 08:55:41', user: 'sys.ops', module: 'System Control', action: 'Maintenance Update', record_affected: 'window:2026-04-27', result: 'Success' },
  { time: '2026-04-23 15:04:12', user: 'audit.reader', module: 'Audit', action: 'Trail Export', record_affected: 'audit_batch:APR23', result: 'Success' },
];

const TAB_META: Array<{ key: SystemControlTab; label: string }> = [
  { key: 'activity_logs', label: 'Activity Logs' },
  { key: 'maintenance', label: 'Maintenance' },
  { key: 'system_information', label: 'System Information' },
  { key: 'update_logs', label: 'Update Logs' },
  { key: 'audit_trail', label: 'Audit Trail' },
];

export const SystemControlPage: React.FC<SystemControlPageProps> = ({
  initialTab = 'activity_logs',
  onBack,
}) => {
  const [activeTab, setActiveTab] = useState<SystemControlTab>(initialTab);
  const [dataAsOf, setDataAsOf] = useState(new Date().toISOString());

  const systemInfo = useMemo(
    () => ({
      platform_version: 'TAAIP Platform v2.11.0',
      database_version: 'SQLite Schema 2026.04.24',
      environment: 'Production',
      last_backup: '2026-04-24 02:03:11 UTC',
      uptime: '17 days 06 hours',
      system_status: 'Operational',
      support_contact: 'taaip-support@usarec.example.mil',
    }),
    [],
  );

  const refresh = (): void => {
    setDataAsOf(new Date().toISOString());
  };

  return (
    <div className="space-y-6 p-4">
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-6 text-white shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-wide">SYSTEM CONTROL</h1>
            <p className="mt-1 text-sm text-slate-300">System logs, maintenance, updates, and system information</p>
            <p className="mt-1 text-xs text-slate-400">Data as of {dataAsOf}</p>
          </div>
          <div className="flex items-center gap-2">
            {onBack && (
              <button
                onClick={onBack}
                className="rounded-lg border border-slate-500 bg-slate-700 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-600"
              >
                Back to Admin
              </button>
            )}
            <button
              onClick={refresh}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-500 bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-600"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-1 shadow-sm inline-flex flex-wrap">
        {TAB_META.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold ${
              activeTab === tab.key
                ? 'bg-slate-800 text-white'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'activity_logs' && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100">
                <th className="px-3 py-2 font-semibold">Time</th>
                <th className="px-3 py-2 font-semibold">User</th>
                <th className="px-3 py-2 font-semibold">Action</th>
                <th className="px-3 py-2 font-semibold">Details</th>
                <th className="px-3 py-2 font-semibold">IP Address</th>
              </tr>
            </thead>
            <tbody>
              {ACTIVITY_LOGS.map((row, idx) => (
                <tr key={`activity-${idx}`} className="border-b border-slate-100">
                  <td className="px-3 py-2">{row.time}</td>
                  <td className="px-3 py-2">{row.user}</td>
                  <td className="px-3 py-2">{row.action}</td>
                  <td className="px-3 py-2">{row.details}</td>
                  <td className="px-3 py-2">{row.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'maintenance' && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100">
                <th className="px-3 py-2 font-semibold">Date</th>
                <th className="px-3 py-2 font-semibold">Maintenance Window</th>
                <th className="px-3 py-2 font-semibold">Type</th>
                <th className="px-3 py-2 font-semibold">Description</th>
                <th className="px-3 py-2 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {MAINTENANCE_WINDOWS.map((row, idx) => (
                <tr key={`maintenance-${idx}`} className="border-b border-slate-100">
                  <td className="px-3 py-2">{row.date}</td>
                  <td className="px-3 py-2">{row.maintenance_window}</td>
                  <td className="px-3 py-2">{row.type}</td>
                  <td className="px-3 py-2">{row.description}</td>
                  <td className="px-3 py-2">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'system_information' && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Platform Version</p>
              <p className="mt-1 text-sm text-slate-800">{systemInfo.platform_version}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Database Version</p>
              <p className="mt-1 text-sm text-slate-800">{systemInfo.database_version}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Environment</p>
              <p className="mt-1 text-sm text-slate-800">{systemInfo.environment}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Last Backup</p>
              <p className="mt-1 text-sm text-slate-800">{systemInfo.last_backup}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Uptime</p>
              <p className="mt-1 text-sm text-slate-800">{systemInfo.uptime}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">System Status</p>
              <p className="mt-1 text-sm text-slate-800">{systemInfo.system_status}</p>
            </div>
          </div>
          <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">Support Contact</p>
            <p className="mt-1 text-sm text-slate-800">{systemInfo.support_contact}</p>
          </div>
        </div>
      )}

      {activeTab === 'update_logs' && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100">
                <th className="px-3 py-2 font-semibold">Version</th>
                <th className="px-3 py-2 font-semibold">Date</th>
                <th className="px-3 py-2 font-semibold">Update Type</th>
                <th className="px-3 py-2 font-semibold">Summary</th>
                <th className="px-3 py-2 font-semibold">Approved By</th>
                <th className="px-3 py-2 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {UPDATE_LOGS.map((row, idx) => (
                <tr key={`update-${idx}`} className="border-b border-slate-100">
                  <td className="px-3 py-2">{row.version}</td>
                  <td className="px-3 py-2">{row.date}</td>
                  <td className="px-3 py-2">{row.update_type}</td>
                  <td className="px-3 py-2">{row.summary}</td>
                  <td className="px-3 py-2">{row.approved_by}</td>
                  <td className="px-3 py-2">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'audit_trail' && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100">
                <th className="px-3 py-2 font-semibold">Time</th>
                <th className="px-3 py-2 font-semibold">User</th>
                <th className="px-3 py-2 font-semibold">Module</th>
                <th className="px-3 py-2 font-semibold">Action</th>
                <th className="px-3 py-2 font-semibold">Record Affected</th>
                <th className="px-3 py-2 font-semibold">Result</th>
              </tr>
            </thead>
            <tbody>
              {AUDIT_TRAIL.map((row, idx) => (
                <tr key={`audit-${idx}`} className="border-b border-slate-100">
                  <td className="px-3 py-2">{row.time}</td>
                  <td className="px-3 py-2">{row.user}</td>
                  <td className="px-3 py-2">{row.module}</td>
                  <td className="px-3 py-2">{row.action}</td>
                  <td className="px-3 py-2">{row.record_affected}</td>
                  <td className="px-3 py-2">{row.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
