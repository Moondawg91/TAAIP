import React from 'react';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card, KPIRow, Table } from '../../components/shared/ui';
import { TAAIP_DOCTRINE } from '../../config/taaipDoctrine';

type Stage = 'seniors' | 'juniors' | 'post-secondary';

interface SrpMetricRow {
  school: string;
  stage: Stage;
  reserveAlignment: number;
  itemlcUncontacted: number;
  applemtdUncontacted: number;
  totalUncontacted: number;
}

type SrpTableRow = SrpMetricRow & Record<string, unknown>;

const PIPELINE = [
  { stage: 'seniors', prospects: 842, qualified: 512, appointments: 361 },
  { stage: 'juniors', prospects: 664, qualified: 351, appointments: 221 },
  { stage: 'post-secondary', prospects: 529, qualified: 275, appointments: 158 },
];

const RESERVE_ALIGNMENT = [
  { name: 'USAR', value: 42 },
  { name: 'ARNG', value: 33 },
  { name: 'Active', value: 25 },
];

const SRP_ROWS: SrpTableRow[] = [
  { school: 'Northview HS', stage: 'seniors', reserveAlignment: 81, itemlcUncontacted: 14, applemtdUncontacted: 9, totalUncontacted: 23 },
  { school: 'Eastfield HS', stage: 'seniors', reserveAlignment: 74, itemlcUncontacted: 11, applemtdUncontacted: 12, totalUncontacted: 23 },
  { school: 'Cypress HS', stage: 'juniors', reserveAlignment: 69, itemlcUncontacted: 17, applemtdUncontacted: 8, totalUncontacted: 25 },
  { school: 'Lone Star College', stage: 'post-secondary', reserveAlignment: 63, itemlcUncontacted: 7, applemtdUncontacted: 6, totalUncontacted: 13 },
];

const COLORS = ['#2563eb', '#06b6d4', '#16a34a'];

export const SRPPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card title="School Recruiting Program (SRP)">
        <p className="text-sm text-slate-300">
          Doctrine: priority order {TAAIP_DOCTRINE.srpPriorityOrder.join(' > ')}. Uncontacted lead tracking uses{' '}
          {TAAIP_DOCTRINE.uncontactedLeadSignals.join(' + ')} and Reserve alignment is integrated by design.
        </p>
      </Card>

      <KPIRow
        items={[
          { label: 'Senior Priority Coverage', value: '91%' },
          { label: 'Reserve Alignment', value: '74%' },
          { label: 'Uncontacted Leads', value: '84' },
          { label: 'Qualified Appointments', value: '740' },
        ]}
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card title="SRP Pipeline by Priority Tier">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={PIPELINE}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="stage" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="prospects" fill="#2563eb" />
                <Bar dataKey="qualified" fill="#0ea5e9" />
                <Bar dataKey="appointments" fill="#16a34a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Reserve Alignment Mix">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={RESERVE_ALIGNMENT} dataKey="value" nameKey="name" outerRadius={100} label>
                  {RESERVE_ALIGNMENT.map((entry, idx) => (
                    <Cell key={entry.name} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card title="School-Level SRP Intelligence">
        <Table
          rows={SRP_ROWS}
          columns={[
            { key: 'school', header: 'School' },
            { key: 'stage', header: 'Priority Tier' },
            { key: 'reserveAlignment', header: 'Reserve Alignment %' },
            { key: 'itemlcUncontacted', header: 'ITEMLC Uncontacted' },
            { key: 'applemtdUncontacted', header: 'APPLEMDT Uncontacted' },
            { key: 'totalUncontacted', header: 'Total Uncontacted' },
          ]}
          getRowId={(row) => String(row.school)}
        />
      </Card>
    </div>
  );
};

export default SRPPage;
