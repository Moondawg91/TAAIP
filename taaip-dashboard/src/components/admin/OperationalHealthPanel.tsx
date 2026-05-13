import React, { useEffect, useMemo, useState } from 'react';
import { Card, Table } from '../shared/ui';
import { ENTERPRISE_PAGES } from '../../config/enterprisePages';
import { getAccessProfileForUser } from '../../lib/auth';
import { listAuditRecords, subscribeAuditRecords } from '../../lib/audit/controller';
import { getIngestionSnapshot, runAllIngestionModules, subscribeIngestionHealth } from '../../lib/ingestion/controller';
import { listNotifications, subscribeNotifications } from '../../lib/notifications/controller';
import { User } from '../../types/auth';

type Props = {
  user: User;
};

const API_HEALTH = [
  { id: 'auth', service: 'Auth API', status: 'Healthy', latency: '83ms' },
  { id: 'mi', service: 'Market Intelligence API', status: 'Healthy', latency: '110ms' },
  { id: 'docs', service: 'Document API', status: 'Degraded', latency: '190ms' },
];

const BACKUP_STATUS = [
  { id: 'db', item: 'Database Snapshot', status: 'Complete', lastRun: '02:03 UTC' },
  { id: 'docs', item: 'Doctrine Libraries', status: 'Complete', lastRun: '02:07 UTC' },
  { id: 'audit', item: 'Audit Archive', status: 'Complete', lastRun: '02:12 UTC' },
];

const UPDATE_STATUS = [
  { id: 'rel', stream: 'Release Channel', version: 'v2.11.0', status: 'Current' },
  { id: 'patch', stream: 'Security Patches', version: '2026.05-A', status: 'Current' },
  { id: 'data', stream: 'Doctrine Index Build', version: '2026.05.11', status: 'Current' },
];

export const OperationalHealthPanel: React.FC<Props> = ({ user }) => {
  const [ingestion, setIngestion] = useState(getIngestionSnapshot());
  const [auditRows, setAuditRows] = useState(() => listAuditRecords().slice(0, 8));
  const [notifications, setNotifications] = useState(() => listNotifications().slice(0, 8));
  const [maintenanceMode, setMaintenanceMode] = useState(false);

  useEffect(() => {
    const unsubIngestion = subscribeIngestionHealth(setIngestion);
    const unsubAudit = subscribeAuditRecords((records) => setAuditRows(records.slice(0, 8)));
    const unsubNotifications = subscribeNotifications((items) => setNotifications(items.slice(0, 8)));
    void runAllIngestionModules();
    return () => {
      unsubIngestion();
      unsubAudit();
      unsubNotifications();
    };
  }, []);

  const profile = useMemo(() => getAccessProfileForUser(user), [user]);

  return (
    <div className="space-y-6">
      <Card title="System Health Overview">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
          <div className="rounded border border-[#1D3A5C] bg-[#0E2847] p-3 text-[#E2E8F0]">
            <div className="uppercase text-[10px] text-[#94A3B8]">Ingestion Health</div>
            <div className="text-sm font-semibold mt-1">{ingestion.overallStatus}</div>
          </div>
          <div className="rounded border border-[#1D3A5C] bg-[#0E2847] p-3 text-[#E2E8F0]">
            <div className="uppercase text-[10px] text-[#94A3B8]">API Health</div>
            <div className="text-sm font-semibold mt-1">{API_HEALTH.filter((x) => x.status === 'Healthy').length}/{API_HEALTH.length} Healthy</div>
          </div>
          <div className="rounded border border-[#1D3A5C] bg-[#0E2847] p-3 text-[#E2E8F0]">
            <div className="uppercase text-[10px] text-[#94A3B8]">Sync Status</div>
            <div className="text-sm font-semibold mt-1">{ingestion.generatedAt ? 'Current' : 'Pending'}</div>
          </div>
          <div className="rounded border border-[#1D3A5C] bg-[#0E2847] p-3 text-[#E2E8F0]">
            <div className="uppercase text-[10px] text-[#94A3B8]">Backup Status</div>
            <div className="text-sm font-semibold mt-1">{BACKUP_STATUS.every((b) => b.status === 'Complete') ? 'Complete' : 'Review'}</div>
          </div>
          <button
            onClick={() => setMaintenanceMode((v) => !v)}
            className={`rounded border p-3 text-left ${maintenanceMode ? 'border-amber-600 bg-amber-950/30 text-amber-200' : 'border-[#1D3A5C] bg-[#0E2847] text-[#E2E8F0]'}`}
          >
            <div className="uppercase text-[10px] text-[#94A3B8]">Maintenance Mode</div>
            <div className="text-sm font-semibold mt-1">{maintenanceMode ? 'Enabled' : 'Disabled'}</div>
          </button>
        </div>
      </Card>

      <Card title="Ingestion Health">
        <Table
          rows={ingestion.sources.map((row) => ({
            ...row,
            lastSyncAt: row.lastSyncAt ?? 'N/A',
          }))}
          columns={[
            { key: 'sourceId', header: 'Source' },
            { key: 'status', header: 'Status' },
            { key: 'message', header: 'Message' },
            { key: 'lastSyncAt', header: 'Last Sync' },
          ]}
          getRowId={(row) => row.sourceId}
        />
      </Card>

      <Card title="API Connection Health">
        <Table
          rows={API_HEALTH}
          columns={[
            { key: 'service', header: 'Service' },
            { key: 'status', header: 'Status' },
            { key: 'latency', header: 'Latency' },
          ]}
          getRowId={(row) => row.id}
        />
      </Card>

      <Card title="Routing Table">
        <Table
          rows={ENTERPRISE_PAGES.map((page) => ({
            id: page.id,
            label: page.label,
            access: profile.allowedPages.includes(page.id) ? 'Allowed' : 'Denied',
          }))}
          columns={[
            { key: 'id', header: 'Route ID' },
            { key: 'label', header: 'Label' },
            { key: 'access', header: 'Access for Active Role' },
          ]}
          getRowId={(row) => row.id}
        />
      </Card>

      <Card title="Role Management / Permission Matrix">
        <div className="text-sm text-slate-300">Role: {profile.role} | Tier: {profile.tier}</div>
        <div className="mt-2 text-xs text-slate-400">Domains: {profile.allowedDataDomains.join(', ')}</div>
      </Card>

      <Card title="Update Management + Backup Status">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Table
            rows={UPDATE_STATUS}
            columns={[
              { key: 'stream', header: 'Update Stream' },
              { key: 'version', header: 'Version' },
              { key: 'status', header: 'Status' },
            ]}
            getRowId={(row) => row.id}
          />
          <Table
            rows={BACKUP_STATUS}
            columns={[
              { key: 'item', header: 'Backup Item' },
              { key: 'status', header: 'Status' },
              { key: 'lastRun', header: 'Last Run' },
            ]}
            getRowId={(row) => row.id}
          />
        </div>
      </Card>

      <Card title="Audit Logs (Recent)">
        <Table
          rows={auditRows.map((row) => ({
            id: row.id,
            timestamp: row.timestamp,
            actor: row.actor,
            eventType: row.eventType,
            target: row.target,
          }))}
          columns={[
            { key: 'timestamp', header: 'Timestamp' },
            { key: 'actor', header: 'Actor' },
            { key: 'eventType', header: 'Event' },
            { key: 'target', header: 'Target' },
          ]}
          getRowId={(row) => String(row.id)}
        />
      </Card>

      <Card title="Notification + Alert Stream">
        <Table
          rows={notifications.map((row) => ({
            id: row.id,
            category: row.category,
            severity: row.severity,
            title: row.title,
            source: row.source,
          }))}
          columns={[
            { key: 'category', header: 'Category' },
            { key: 'severity', header: 'Severity' },
            { key: 'title', header: 'Title' },
            { key: 'source', header: 'Source' },
          ]}
          getRowId={(row) => String(row.id)}
        />
      </Card>
    </div>
  );
};

export default OperationalHealthPanel;
