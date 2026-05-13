import React from 'react';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, LineChart, Line } from 'recharts';
import { Card, KPIRow, Table } from '../../components/shared/ui';
import { ResourcesPane } from '../../components/ResourcesPane';

const MANPOWER = [
  { echelon: 'Recruiter', authorized: 210, assigned: 194 },
  { echelon: 'Company', authorized: 55, assigned: 51 },
  { echelon: 'BN', authorized: 14, assigned: 13 },
  { echelon: 'BDE', authorized: 4, assigned: 4 },
];

const FUNDING = [
  { month: 'Jan', planned: 1.6, obligated: 1.3 },
  { month: 'Feb', planned: 1.7, obligated: 1.4 },
  { month: 'Mar', planned: 1.8, obligated: 1.7 },
  { month: 'Apr', planned: 1.9, obligated: 1.8 },
];

const ALIGNMENT_ROWS = [
  { resource: 'Recruiters', missionDemand: 208, available: 194, gap: -14, action: 'Cross-level temporary support' },
  { resource: 'Event Budget', missionDemand: 1.9, available: 1.8, gap: -0.1, action: 'Shift from low ROI events' },
  { resource: 'School Access Teams', missionDemand: 33, available: 31, gap: -2, action: 'Reserve augmentation' },
];

export const ResourceAlignmentPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <KPIRow
        items={[
          { label: 'Manpower Alignment', value: '93%' },
          { label: 'Funding Alignment', value: '95%' },
          { label: 'Critical Gaps', value: '3' },
          { label: 'Reserve Augmentation', value: '2 Active' },
        ]}
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card title="Manpower Alignment by Echelon">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MANPOWER}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="echelon" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="authorized" fill="#2563eb" />
                <Bar dataKey="assigned" fill="#16a34a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Funding Alignment (Planned vs Obligated)">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={FUNDING}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="month" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Line type="monotone" dataKey="planned" stroke="#2563eb" strokeWidth={2} />
                <Line type="monotone" dataKey="obligated" stroke="#22c55e" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card title="Alignment Actions">
        <Table
          rows={ALIGNMENT_ROWS}
          columns={[
            { key: 'resource', header: 'Resource' },
            { key: 'missionDemand', header: 'Mission Demand' },
            { key: 'available', header: 'Available' },
            { key: 'gap', header: 'Gap' },
            { key: 'action', header: 'Action' },
          ]}
          getRowId={(row) => row.resource}
        />
      </Card>

      <ResourcesPane />
    </div>
  );
};

export default ResourceAlignmentPage;
