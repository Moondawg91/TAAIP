import React, { useState } from 'react';
import { Card, Table, PageShell } from './shared/ui';

// ─── Static demo data ─────────────────────────────────────────────────────────

interface FlashUpdate {
  id: string;
  priority: string;
  update: string;
  description: string;
  datetime: string;
}

interface WOPDUpdate {
  id: string;
  topic: string;
  published: string;
  status: string;
}

interface ProponentUpdate {
  id: string;
  title: string;
  source: string;
  date: string;
  description: string;
}

const FLASH_UPDATES: FlashUpdate[] = [
  { id: '1', priority: 'HIGH', update: 'FY26 Q3 Mission Adjustment', description: 'Brigade adjusted quarterly mission thresholds effective 01 Jun.', datetime: '08 May 2026 0600' },
  { id: '2', priority: 'MEDIUM', update: 'New Lead Qualification SOP', description: 'Updated qualification criteria for RSID 3022 market segment.', datetime: '07 May 2026 1430' },
  { id: '3', priority: 'LOW', update: 'System Maintenance Window', description: 'Scheduled maintenance 11 May 0200–0400. No data export during window.', datetime: '06 May 2026 0800' },
];

const WOPD_UPDATES: WOPDUpdate[] = [
  { id: '1', topic: 'Follow-Up Conversion Techniques', published: '05 May 2026', status: 'Published' },
  { id: '2', topic: 'Urban Market Penetration Strategy', published: '28 Apr 2026', status: 'Published' },
  { id: '3', topic: 'Enlistment Incentive Overview FY26', published: '15 Apr 2026', status: 'Archived' },
];

const PROPONENT_UPDATES: ProponentUpdate[] = [
  { id: '1', title: 'Revised Screening Standards', source: 'USAREC HQ', date: '04 May 2026', description: 'Updated MEPS screening guidance for FY26 applicants.' },
  { id: '2', title: 'Digital Media Policy Change', source: 'HQDA G1', date: '30 Apr 2026', description: 'New restrictions on unapproved social media recruiting platforms.' },
  { id: '3', title: 'Future Soldier Onboarding SOP', source: 'USAREC G3', date: '20 Apr 2026', description: 'Standardized onboarding checklist for FS management phase.' },
];

const priorityColor: Record<string, string> = {
  HIGH:   'text-[#EF4444] font-semibold',
  MEDIUM: 'text-[#F59E0B] font-semibold',
  LOW:    'text-[#94A3B8]',
};

const statusColor: Record<string, string> = {
  Published: 'text-[#10B981]',
  Archived:  'text-[#64748B]',
  Draft:     'text-[#F59E0B]',
};

// ─── Drawer ───────────────────────────────────────────────────────────────────

interface DrawerProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

const Drawer: React.FC<DrawerProps> = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex">
    <div className="flex-1 bg-black/50" onClick={onClose} />
    <div className="w-[480px] bg-[#0E2847] border-l border-[#1D3A5C] flex flex-col h-full overflow-y-auto">
      <div className="flex items-center justify-between px-5 py-3 border-b border-[#1D3A5C]">
        <span className="text-[14px] font-semibold text-[#F3F5F7]">{title}</span>
        <button onClick={onClose} className="text-[#64748B] hover:text-[#F3F5F7] text-xl leading-none">&times;</button>
      </div>
      <div className="p-5 space-y-4">{children}</div>
    </div>
  </div>
);

// ─── Component ────────────────────────────────────────────────────────────────

interface HomeScreenProps {
  onNavigate?: (tab: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = () => {
  const [selectedFlash, setSelectedFlash] = useState<FlashUpdate | null>(null);
  const [selectedWOPD, setSelectedWOPD] = useState<WOPDUpdate | null>(null);
  const [selectedProponent, setSelectedProponent] = useState<ProponentUpdate | null>(null);

  return (
    <PageShell title="Home">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* LEFT COLUMN */}
        <div className="flex flex-col gap-4">
          {/* Flash Updates */}
          <Card title="Flash Updates" noPad>
            <Table<FlashUpdate & Record<string, unknown>>
              columns={[
                {
                  key: 'priority', header: 'Priority',
                  render: (r) => <span className={priorityColor[(r as unknown as FlashUpdate).priority] ?? ''}>{(r as unknown as FlashUpdate).priority}</span>,
                  width: '80px',
                },
                { key: 'update', header: 'Update' },
                { key: 'description', header: 'Description' },
                { key: 'datetime', header: 'Date/Time', width: '160px' },
              ]}
              rows={FLASH_UPDATES as unknown as (FlashUpdate & Record<string, unknown>)[]}
              onRowClick={(r) => setSelectedFlash(r as unknown as FlashUpdate)}
              getRowId={(r) => (r as unknown as FlashUpdate).id}
              emptyText="No flash updates"
            />
          </Card>

          {/* WOPD Updates */}
          <Card title="WOPD Updates" noPad>
            <Table<WOPDUpdate & Record<string, unknown>>
              columns={[
                { key: 'topic', header: 'Topic' },
                { key: 'published', header: 'Published', width: '120px' },
                {
                  key: 'status', header: 'Status', width: '100px',
                  render: (r) => <span className={statusColor[(r as unknown as WOPDUpdate).status] ?? ''}>{(r as unknown as WOPDUpdate).status}</span>,
                },
              ]}
              rows={WOPD_UPDATES as unknown as (WOPDUpdate & Record<string, unknown>)[]}
              onRowClick={(r) => setSelectedWOPD(r as unknown as WOPDUpdate)}
              getRowId={(r) => (r as unknown as WOPDUpdate).id}
              emptyText="No WOPD updates"
            />
          </Card>
        </div>

        {/* RIGHT COLUMN */}
        <div className="flex flex-col gap-4">
          {/* TAWO of the Month */}
          <Card title="TAWO of the Month">
            <div className="flex gap-5">
              <div className="flex-1 space-y-2">
                <div>
                  <div className="text-[16px] font-semibold text-[#F3F5F7]">SSG Taylor Morgan</div>
                  <div className="text-[13px] text-[#64748B]">A Co, 1-1 Recruiting BN</div>
                </div>
                <div className="space-y-2 text-[13px]">
                  <div>
                    <span className="text-[11px] uppercase tracking-[0.07em] text-[#64748B] block mb-0.5">Achievement</span>
                    <span className="text-[#F3F5F7]">Exceeded monthly mission by 128%</span>
                  </div>
                  <div>
                    <span className="text-[11px] uppercase tracking-[0.07em] text-[#64748B] block mb-0.5">Impact</span>
                    <span className="text-[#F3F5F7]">Led two peer coaching sessions on follow-up conversion, contributing to company-wide improvement.</span>
                  </div>
                </div>
              </div>
              <div className="flex-shrink-0">
                <div className="w-24 h-28 bg-[#142F52] border border-[#1D3A5C] rounded overflow-hidden">
                  <img
                    src="https://images.unsplash.com/photo-1542909168-82c3e7fdca5c?auto=format&fit=crop&w=200&q=80"
                    alt="TAWO of the Month"
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Proponent Updates */}
          <Card title="Proponent Updates" noPad>
            <Table<ProponentUpdate & Record<string, unknown>>
              columns={[
                { key: 'title', header: 'Title' },
                { key: 'source', header: 'Source', width: '110px' },
                { key: 'date', header: 'Date', width: '110px' },
                { key: 'description', header: 'Description' },
              ]}
              rows={PROPONENT_UPDATES as unknown as (ProponentUpdate & Record<string, unknown>)[]}
              onRowClick={(r) => setSelectedProponent(r as unknown as ProponentUpdate)}
              getRowId={(r) => (r as unknown as ProponentUpdate).id}
              emptyText="No proponent updates"
            />
          </Card>
        </div>
      </div>

      {/* Drawers */}
      {selectedFlash && (
        <Drawer title="Flash Update Detail" onClose={() => setSelectedFlash(null)}>
          <div className="space-y-3 text-[13px]">
            <div><span className="text-[#64748B]">Priority:</span> <span className={`${priorityColor[selectedFlash.priority]} ml-2`}>{selectedFlash.priority}</span></div>
            <div><span className="text-[#64748B]">Update:</span> <span className="ml-2 text-[#F3F5F7]">{selectedFlash.update}</span></div>
            <div><span className="text-[#64748B]">Date/Time:</span> <span className="ml-2 text-[#F3F5F7]">{selectedFlash.datetime}</span></div>
            <div className="pt-2 border-t border-[#1D3A5C]"><p className="text-[#F3F5F7]">{selectedFlash.description}</p></div>
          </div>
        </Drawer>
      )}
      {selectedWOPD && (
        <Drawer title="WOPD Detail" onClose={() => setSelectedWOPD(null)}>
          <div className="space-y-3 text-[13px]">
            <div><span className="text-[#64748B]">Topic:</span> <span className="ml-2 text-[#F3F5F7]">{selectedWOPD.topic}</span></div>
            <div><span className="text-[#64748B]">Published:</span> <span className="ml-2 text-[#F3F5F7]">{selectedWOPD.published}</span></div>
            <div><span className="text-[#64748B]">Status:</span> <span className={`ml-2 ${statusColor[selectedWOPD.status]}`}>{selectedWOPD.status}</span></div>
          </div>
        </Drawer>
      )}
      {selectedProponent && (
        <Drawer title="Proponent Update Detail" onClose={() => setSelectedProponent(null)}>
          <div className="space-y-3 text-[13px]">
            <div><span className="text-[#64748B]">Title:</span> <span className="ml-2 text-[#F3F5F7]">{selectedProponent.title}</span></div>
            <div><span className="text-[#64748B]">Source:</span> <span className="ml-2 text-[#F3F5F7]">{selectedProponent.source}</span></div>
            <div><span className="text-[#64748B]">Date:</span> <span className="ml-2 text-[#F3F5F7]">{selectedProponent.date}</span></div>
            <div className="pt-2 border-t border-[#1D3A5C]"><p className="text-[#F3F5F7]">{selectedProponent.description}</p></div>
          </div>
        </Drawer>
      )}
    </PageShell>
  );
};

export default HomeScreen;
