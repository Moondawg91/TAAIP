import React, { useMemo, useState } from 'react';
import { Card, Table } from '../../components/shared/ui';

type StaffUpdate = {
  section: string;
  changed: string;
  supportNeeded: string;
  risks: string;
  tasks: string;
  suspense: string;
  documents: string;
};

const ATTENDEES = ['420T', 'ESS', 'A&PA', 'S3', 'BN XO', 'OPS SGM'];

const UPDATES: StaffUpdate[] = [
  {
    section: '420T',
    changed: 'Updated targeting assumptions from latest EMM sync.',
    supportNeeded: 'Validation from S3 on execution pacing.',
    risks: 'Lag in ZIP-level feed refresh.',
    tasks: 'Publish revised intel summary.',
    suspense: '2026-05-18',
    documents: 'Fusion Intel Summary v3',
  },
  {
    section: 'S3',
    changed: 'Adjusted event sequence for Q+0 operations.',
    supportNeeded: 'Budget impact validation from A&PA.',
    risks: 'Venue conflicts for two planned events.',
    tasks: 'Issue schedule fragment update.',
    suspense: '2026-05-20',
    documents: 'Execution Sync FRAGO',
  },
];

const ARCHIVE = [
  { month: '2026-04', notes: 'Assess to Execute handoff complete.', decisions: '4', followUps: '7' },
  { month: '2026-03', notes: 'TWG backlog reduced by 22%.', decisions: '6', followUps: '5' },
];

export const FusionCellPage: React.FC = () => {
  const [selectedSection, setSelectedSection] = useState<string>('420T');
  const selected = useMemo(
    () => UPDATES.find((u) => u.section === selectedSection) ?? null,
    [selectedSection],
  );

  return (
    <div className="space-y-6">
      <Card title="Fusion Cell Monthly Synchronization">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-sm text-slate-300">
          <div><span className="text-slate-500">Meeting Month:</span> 2026-05</div>
          <div><span className="text-slate-500">Agenda:</span> Staff update, risks, tasking, follow-up</div>
          <div><span className="text-slate-500">Battle Rhythm:</span> Monthly</div>
        </div>
      </Card>

      <Card title="Attendees">
        <div className="flex flex-wrap gap-2">
          {ATTENDEES.map((a) => (
            <span key={a} className="px-3 py-1 rounded border border-slate-700 text-xs text-slate-300">{a}</span>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-6">
        <Card title="Section Updates">
          <Table
            rows={UPDATES}
            columns={[
              { key: 'section', header: 'Section' },
              { key: 'changed', header: 'What Changed' },
              { key: 'supportNeeded', header: 'Support Needed' },
              { key: 'risks', header: 'Risks' },
              { key: 'tasks', header: 'Tasks' },
              { key: 'suspense', header: 'Suspense' },
            ]}
            getRowId={(row) => row.section}
            onRowClick={(row) => setSelectedSection(row.section)}
            selectedRow={selected ?? undefined}
          />
        </Card>

        <Card title="Section Detail Drawer">
          {selected ? (
            <div className="space-y-3 text-sm text-slate-300">
              <div><span className="text-slate-500">Section:</span> {selected.section}</div>
              <div><span className="text-slate-500">Changed:</span> {selected.changed}</div>
              <div><span className="text-slate-500">Support Needed:</span> {selected.supportNeeded}</div>
              <div><span className="text-slate-500">Risks:</span> {selected.risks}</div>
              <div><span className="text-slate-500">Tasks:</span> {selected.tasks}</div>
              <div><span className="text-slate-500">Suspense:</span> {selected.suspense}</div>
              <div><span className="text-slate-500">Documents:</span> {selected.documents}</div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Select a section update.</p>
          )}
        </Card>
      </div>

      <Card title="Previous Meeting Archive">
        <Table
          rows={ARCHIVE}
          columns={[
            { key: 'month', header: 'Month' },
            { key: 'notes', header: 'Notes' },
            { key: 'decisions', header: 'Decisions' },
            { key: 'followUps', header: 'Follow-Ups' },
          ]}
          getRowId={(row) => row.month}
        />
      </Card>
    </div>
  );
};

export default FusionCellPage;
