import React, { useMemo, useState } from 'react';
import { Card, Table, Tabs } from '../../components/shared/ui';
import { runSrpPriorityEngine } from '../../lib/engines';

type SchoolTab =
  | 'SRP Overview'
  | 'School Targeting'
  | 'Senior Market Share'
  | 'School Visits & Engagement'
  | 'School Funnel Analysis'
  | 'DoD School Competition'
  | 'SRP Alignment'
  | 'Opportunity Schools'
  | 'School Profiles'
  | 'Historical Performance';

const TAB_ITEMS = [
  'SRP Overview',
  'School Targeting',
  'Senior Market Share',
  'School Visits & Engagement',
  'School Funnel Analysis',
  'DoD School Competition',
  'SRP Alignment',
  'Opportunity Schools',
  'School Profiles',
  'Historical Performance',
].map((x) => ({ id: x, label: x }));

const SCHOOL_ROWS = [
  {
    school: 'Central High School',
    rsid: '1A1D',
    seniors: 468,
    contacted: 192,
    uncontacted: 276,
    leads: 59,
    contracts: 11,
    dodSeniorCapture: '34%'
  },
  {
    school: 'Liberty Technical College',
    rsid: '1A1D',
    seniors: 0,
    contacted: 74,
    uncontacted: 121,
    leads: 41,
    contracts: 7,
    dodSeniorCapture: 'N/A'
  },
];

export const SchoolIntelligencePage: React.FC = () => {
  const [tab, setTab] = useState<SchoolTab>('SRP Overview');
  const [selectedSchool, setSelectedSchool] = useState<string>('Central High School');
  const srpPriority = runSrpPriorityEngine({ seniors: 468, juniors: 410, postSecondary: 195 });

  const school = useMemo(
    () => SCHOOL_ROWS.find((r) => r.school === selectedSchool) ?? null,
    [selectedSchool],
  );

  return (
    <div className="space-y-6">
      <Card title="School Intelligence / School Recruiting Program">
        <p className="text-sm text-slate-300">
          Secondary and post-secondary intelligence with SRP alignment, contacted vs uncontacted markets, visit coverage, EMM lead capture,
          DoD competition, and recommendation support.
        </p>
      </Card>

      <Card title="School Intelligence Modules" noPad>
        <Tabs tabs={TAB_ITEMS} active={tab} onChange={(id) => setTab(id as SchoolTab)} />
      </Card>

      <Card title="SRP Priority Engine (Seniors > Juniors > Post-Secondary)">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
          {srpPriority.summaries.map((summary) => (
            <div key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-3 py-2 text-xs text-slate-300">
              {summary.label}: {summary.value}
            </div>
          ))}
        </div>
        <div className="text-xs text-slate-400">
          Priority order: {srpPriority.priorityOrder.map((row) => `${row.cohort} (${row.score.toFixed(1)})`).join(' -> ')}
        </div>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-6">
        <Card title={tab}>
          <Table
            rows={SCHOOL_ROWS}
            columns={[
              { key: 'school', header: 'School' },
              { key: 'rsid', header: 'RSID' },
              { key: 'seniors', header: 'HS Seniors' },
              { key: 'contacted', header: 'Contacted' },
              { key: 'uncontacted', header: 'Uncontacted' },
              { key: 'leads', header: 'Leads' },
              { key: 'contracts', header: 'Contracts' },
              { key: 'dodSeniorCapture', header: 'DoD Senior Capture' },
            ]}
            getRowId={(row) => row.school}
            onRowClick={(row) => setSelectedSchool(row.school)}
            selectedRow={school ?? undefined}
          />
        </Card>

        <Card title="School Detail Drawer">
          {school ? (
            <div className="space-y-2 text-sm text-slate-300">
              <div><span className="text-slate-500">School:</span> {school.school}</div>
              <div><span className="text-slate-500">RSID:</span> {school.rsid}</div>
              <div><span className="text-slate-500">Contacted / Uncontacted:</span> {school.contacted} / {school.uncontacted}</div>
              <div><span className="text-slate-500">Leads / Contracts:</span> {school.leads} / {school.contracts}</div>
              <div><span className="text-slate-500">Sources:</span> Vantage, AIE, EMM, Manual Upload</div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Select a school row.</p>
          )}
        </Card>
      </div>
    </div>
  );
};

export default SchoolIntelligencePage;
