import React, { useEffect, useState } from 'react';
import { Card, Table } from '../../components/shared/ui';
import { TAAIP_DOCTRINE } from '../../config/taaipDoctrine';
import UniversalDataUpload from '../../components/UniversalDataUpload';
import { SharePointIntegration } from '../../components/SharePointIntegration';
import { getIngestionSnapshot, runIngestionModule, subscribeIngestionHealth } from '../../lib/ingestion/controller';
import { logAuditEvent } from '../../lib/audit/controller';
import { pushNotification } from '../../lib/notifications/controller';

const DOC_ROWS = TAAIP_DOCTRINE.doctrineLibraries.map((library, idx) => ({
  id: `${library}-${idx}`,
  library,
  status: 'Available',
  source: library === 'USAREC Messages' ? 'SharePoint' : 'Document Center',
  retention: 'Managed',
}));

export const DataDocumentCenterPage: React.FC = () => {
  const [ingestionSnapshot, setIngestionSnapshot] = useState(getIngestionSnapshot());

  useEffect(() => subscribeIngestionHealth(setIngestionSnapshot), []);

  return (
    <div className="space-y-6">
      <Card title="Data & Document Center">
        <p className="text-sm text-slate-300">
          Enterprise ingestion feeds: {TAAIP_DOCTRINE.ingestionFeeds.join(', ')}. Doctrine libraries maintained for regulations,
          UTCs, TOR, SRP/ROP/TWG workflows.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => { void runIngestionModule('document_center_index'); }}
            className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]"
          >
            Reindex Document Center
          </button>
          <button
            onClick={() => {
              logAuditEvent({
                eventType: 'document_upload',
                actor: 'taaip.engine',
                message: 'Manual document upload recorded from Data & Document Center',
                target: 'document-center',
              });
              pushNotification({
                title: 'Document Update',
                message: 'Document upload detected in Data & Document Center.',
                category: 'document',
                severity: 'info',
                source: 'Data & Document Center',
              });
            }}
            className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]"
          >
            Log Upload Event
          </button>
          <button
            onClick={() => {
              logAuditEvent({
                eventType: 'document_delete',
                actor: 'taaip.engine',
                message: 'Document deletion action recorded from Data & Document Center',
                target: 'document-center',
              });
            }}
            className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]"
          >
            Log Deletion Event
          </button>
        </div>
      </Card>

      <Card title="Document Ingestion Status">
        <Table
          rows={ingestionSnapshot.sources.map((source) => ({
            ...source,
            lastSyncAt: source.lastSyncAt ?? 'N/A',
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

      <Card title="Doctrine Library Registry">
        <Table
          rows={DOC_ROWS}
          columns={[
            { key: 'library', header: 'Library' },
            { key: 'status', header: 'Status' },
            { key: 'source', header: 'Source' },
            { key: 'retention', header: 'Retention' },
          ]}
          getRowId={(row) => row.id}
        />
      </Card>

      <UniversalDataUpload />
      <SharePointIntegration />
    </div>
  );
};

export default DataDocumentCenterPage;
