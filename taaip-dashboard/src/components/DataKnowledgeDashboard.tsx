import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, Filter, RefreshCw, Upload } from 'lucide-react';
import { API_BASE } from '../config/api';

type TabKey = 'document_center' | 'reports' | 'data_library';

type Folder = { id: string; name: string };

type DocumentRow = {
  id: string;
  document_name: string;
  type: string;
  folder: string;
  owner: string;
  last_modified: string;
  size: string;
  status: string;
};

type ReportRow = {
  report_name: string;
  report_type: string;
  period: string;
  owner: string;
  created_date: string;
  last_modified: string;
  status: string;
};

type DatasetRow = {
  dataset_name: string;
  source: string;
  period: string;
  file_type: string;
  uploaded_by: string;
  uploaded_date: string;
  status: string;
};

type AlertRow = {
  level: string;
  title: string;
  message: string;
};

type StorageInfo = {
  used_bytes: number;
  used_display: string;
  capacity_bytes: number;
  capacity_display: string;
  used_pct: number;
};

type Breadcrumb = {
  label: string;
  key: string;
};

type FilterOptions = {
  tabs: Array<{ key: TabKey; label: string }>;
  folders: Folder[];
  types: string[];
};

type Payload = {
  data_as_of: string;
  active_tab: TabKey;
  folders: Folder[];
  documents: DocumentRow[];
  reports: ReportRow[];
  datasets: DatasetRow[];
  alerts: AlertRow[];
  storage: StorageInfo;
  breadcrumbs: Breadcrumb[];
  filter_options: FilterOptions;
};

const EMPTY_STORAGE: StorageInfo = {
  used_bytes: 0,
  used_display: '0 B',
  capacity_bytes: 0,
  capacity_display: '0 B',
  used_pct: 0,
};

const tabLabel = (tab: TabKey): string => {
  if (tab === 'reports') return 'Reports';
  if (tab === 'data_library') return 'Data Library';
  return 'Document Center';
};

const alertClasses = (level: string): string => {
  const v = String(level || '').toLowerCase();
  if (v === 'high') return 'border-red-200 bg-red-50 text-red-800';
  if (v === 'medium') return 'border-amber-200 bg-amber-50 text-amber-800';
  return 'border-slate-200 bg-slate-50 text-slate-700';
};

const docTypeForFolder = (folderName: string): string => {
  const key = folderName.toLowerCase();
  if (key === 'regulations') return 'regulation';
  if (key === 'usarec messages') return 'usarec_message';
  if (key === 'sops') return 'general_document';
  return 'planning_reference';
};

export const DataKnowledgeDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<TabKey>('document_center');
  const [folder, setFolder] = useState('');
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const [dataAsOf, setDataAsOf] = useState('');
  const [folders, setFolders] = useState<Folder[]>([]);
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [reports, setReports] = useState<ReportRow[]>([]);
  const [datasets, setDatasets] = useState<DatasetRow[]>([]);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [storage, setStorage] = useState<StorageInfo>(EMPTY_STORAGE);
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([]);
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ tabs: [], folders: [], types: [] });

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set('tab', activeTab);
      if (activeTab === 'document_center' && folder) params.set('folder', folder);
      if (search) params.set('search', search);
      if (typeFilter) params.set('type', typeFilter);

      const res = await fetch(`${API_BASE}/api/v2/data-knowledge/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as Payload;

      setDataAsOf(payload.data_as_of ?? '');
      setActiveTab((payload.active_tab ?? activeTab) as TabKey);
      setFolders(Array.isArray(payload.folders) ? payload.folders : []);
      setDocuments(Array.isArray(payload.documents) ? payload.documents : []);
      setReports(Array.isArray(payload.reports) ? payload.reports : []);
      setDatasets(Array.isArray(payload.datasets) ? payload.datasets : []);
      setAlerts(Array.isArray(payload.alerts) ? payload.alerts : []);
      setStorage(payload.storage ?? EMPTY_STORAGE);
      setBreadcrumbs(Array.isArray(payload.breadcrumbs) ? payload.breadcrumbs : []);
      setFilterOptions(payload.filter_options ?? { tabs: [], folders: [], types: [] });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load Data & Knowledge');
      setFolders([]);
      setDocuments([]);
      setReports([]);
      setDatasets([]);
      setAlerts([]);
      setStorage(EMPTY_STORAGE);
      setBreadcrumbs([]);
      setFilterOptions({ tabs: [], folders: [], types: [] });
    } finally {
      setLoading(false);
    }
  }, [activeTab, folder, search, typeFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setSearch('');
    setTypeFilter('');
    if (activeTab !== 'document_center') {
      setFolder('');
    }
  }, [activeTab]);

  const resetFilters = (): void => {
    setSearch('');
    setTypeFilter('');
    if (activeTab === 'document_center') setFolder('');
  };

  const onUploadClick = (): void => {
    setUploadMessage('');
    fileInputRef.current?.click();
  };

  const onUploadSelected = async (ev: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = ev.target.files?.[0];
    if (!file) return;

    const sourceType = activeTab === 'reports' ? 'uploaded' : activeTab === 'data_library' ? 'data_hub_upload' : 'uploaded';
    const docType = activeTab === 'reports' ? 'planning_reference' : activeTab === 'data_library' ? 'dataset' : (folder ? docTypeForFolder(folder) : 'general_document');

    const form = new FormData();
    form.append('file', file);
    form.append('title', file.name);
    form.append('source_type', sourceType);
    form.append('doc_type', docType);

    setUploading(true);
    setUploadMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/docs/upload`, { method: 'POST', body: form });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setUploadMessage(`Uploaded ${file.name}`);
      await load();
    } catch (e: unknown) {
      setUploadMessage(e instanceof Error ? `Upload failed: ${e.message}` : 'Upload failed');
    } finally {
      setUploading(false);
      ev.target.value = '';
    }
  };

  const folderItems = useMemo(() => {
    return folders.length > 0
      ? folders
      : [
          { id: 'regulations', name: 'Regulations' },
          { id: 'usarec_messages', name: 'USAREC Messages' },
          { id: 'sops', name: 'SOPs' },
          { id: 'proponent_guidance', name: 'Proponent Guidance' },
        ];
  }, [folders]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold tracking-wide">DATA & KNOWLEDGE</h1>
            {dataAsOf && <p className="mt-1 text-xs text-slate-400">Data as of {dataAsOf}</p>}
          </div>
          <button
            onClick={() => void load()}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-500 bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-600"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-1 shadow-sm inline-flex">
        <button className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeTab === 'document_center' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`} onClick={() => setActiveTab('document_center')}>Document Center</button>
        <button className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeTab === 'reports' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`} onClick={() => setActiveTab('reports')}>Reports</button>
        <button className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeTab === 'data_library' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`} onClick={() => setActiveTab('data_library')}>Data Library</button>
      </div>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Loading data & knowledge...</div>}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      {activeTab === 'document_center' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex flex-wrap items-center gap-3">
            <Filter className="h-4 w-4 text-slate-400 shrink-0" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search documents"
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm min-w-[220px]"
            />
            <select value={folder} onChange={(e) => setFolder(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
              <option value="">All Folders</option>
              {folderItems.map((f) => (<option key={f.id} value={f.name}>{f.name}</option>))}
            </select>
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
              <option value="">All Types</option>
              {(filterOptions.types || []).map((t) => (<option key={t} value={t}>{t}</option>))}
            </select>
            <button onClick={resetFilters} className="px-3 py-2 rounded-lg text-sm font-medium border border-slate-300 bg-slate-50 text-slate-600 hover:bg-slate-100">Reset</button>
            <button onClick={onUploadClick} disabled={uploading} className="ml-auto inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60">
              <Upload className="h-4 w-4" />
              {uploading ? 'Uploading...' : `Upload (${tabLabel(activeTab)})`}
            </button>
            <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => { void onUploadSelected(e); }} />
          </div>

          {uploadMessage && <div className="rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-700">{uploadMessage}</div>}

          <div className="text-sm text-slate-600">
            {breadcrumbs.length > 0 ? breadcrumbs.map((b) => b.label).join(' / ') : 'Data & Knowledge / Document Center'}
          </div>

          <div className="grid gap-4 lg:grid-cols-[220px_1fr_300px]">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">Folders</h2>
              <div className="space-y-2">
                {folderItems.map((f) => (
                  <button key={f.id} onClick={() => setFolder(f.name)} className={`w-full text-left px-3 py-2 rounded-lg text-sm ${folder === f.name ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-50 text-slate-700 border border-slate-200 hover:bg-slate-100'}`}>
                    {f.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
              <h2 className="text-base font-semibold text-slate-900 mb-4">Documents</h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100">
                    <th className="px-3 py-2 font-semibold">Document Name</th>
                    <th className="px-3 py-2 font-semibold">Type</th>
                    <th className="px-3 py-2 font-semibold">Folder</th>
                    <th className="px-3 py-2 font-semibold">Owner</th>
                    <th className="px-3 py-2 font-semibold">Last Modified</th>
                    <th className="px-3 py-2 font-semibold">Size</th>
                    <th className="px-3 py-2 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.length > 0 ? documents.map((row) => (
                    <tr key={row.id} className="border-b border-slate-100">
                      <td className="px-3 py-2 font-medium text-slate-800">{row.document_name}</td>
                      <td className="px-3 py-2">{row.type}</td>
                      <td className="px-3 py-2">{row.folder}</td>
                      <td className="px-3 py-2">{row.owner}</td>
                      <td className="px-3 py-2">{row.last_modified}</td>
                      <td className="px-3 py-2">{row.size}</td>
                      <td className="px-3 py-2">{row.status}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-6 text-slate-500" colSpan={7}>No documents for current filters.</td></tr>}
                </tbody>
              </table>
            </div>

            <div className="space-y-4">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">Document Alerts</h2>
                <div className="space-y-2">
                  {alerts.length > 0 ? alerts.map((a, idx) => (
                    <div key={`${a.title}-${idx}`} className={`rounded-lg border p-3 ${alertClasses(a.level)}`}>
                      <p className="text-sm font-semibold inline-flex items-center gap-2"><AlertTriangle className="w-4 h-4" />{a.title}</p>
                      <p className="mt-1 text-sm">{a.message}</p>
                    </div>
                  )) : <p className="text-sm text-slate-500">No alerts.</p>}
                </div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">Storage Usage</h2>
                <p className="text-sm text-slate-700">Used: {storage.used_display}</p>
                <p className="text-sm text-slate-700">Capacity: {storage.capacity_display}</p>
                <p className="text-sm text-slate-700">Utilization: {storage.used_pct.toFixed(1)}%</p>
                <div className="mt-2 h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-600" style={{ width: `${Math.max(0, Math.min(storage.used_pct, 100))}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'reports' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex flex-wrap items-center gap-3">
            <Filter className="h-4 w-4 text-slate-400 shrink-0" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search reports" className="px-3 py-2 border border-slate-300 rounded-lg text-sm min-w-[220px]" />
            <button onClick={resetFilters} className="px-3 py-2 rounded-lg text-sm font-medium border border-slate-300 bg-slate-50 text-slate-600 hover:bg-slate-100">Reset</button>
            <button onClick={onUploadClick} disabled={uploading} className="ml-auto inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60"><Upload className="h-4 w-4" />{uploading ? 'Uploading...' : `Upload (${tabLabel(activeTab)})`}</button>
            <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => { void onUploadSelected(e); }} />
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
            <h2 className="text-base font-semibold text-slate-900 mb-4">Report List</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100">
                  <th className="px-3 py-2 font-semibold">Report Name</th>
                  <th className="px-3 py-2 font-semibold">Report Type</th>
                  <th className="px-3 py-2 font-semibold">Period</th>
                  <th className="px-3 py-2 font-semibold">Owner</th>
                  <th className="px-3 py-2 font-semibold">Created Date</th>
                  <th className="px-3 py-2 font-semibold">Last Modified</th>
                  <th className="px-3 py-2 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {reports.length > 0 ? reports.map((row, idx) => (
                  <tr key={`${row.report_name}-${idx}`} className="border-b border-slate-100">
                    <td className="px-3 py-2 font-medium text-slate-800">{row.report_name}</td>
                    <td className="px-3 py-2">{row.report_type}</td>
                    <td className="px-3 py-2">{row.period}</td>
                    <td className="px-3 py-2">{row.owner}</td>
                    <td className="px-3 py-2">{row.created_date}</td>
                    <td className="px-3 py-2">{row.last_modified}</td>
                    <td className="px-3 py-2">{row.status}</td>
                  </tr>
                )) : <tr><td className="px-3 py-6 text-slate-500" colSpan={7}>No reports for current filters.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'data_library' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex flex-wrap items-center gap-3">
            <Filter className="h-4 w-4 text-slate-400 shrink-0" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search datasets" className="px-3 py-2 border border-slate-300 rounded-lg text-sm min-w-[220px]" />
            <button onClick={resetFilters} className="px-3 py-2 rounded-lg text-sm font-medium border border-slate-300 bg-slate-50 text-slate-600 hover:bg-slate-100">Reset</button>
            <button onClick={onUploadClick} disabled={uploading} className="ml-auto inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60"><Upload className="h-4 w-4" />{uploading ? 'Uploading...' : `Upload (${tabLabel(activeTab)})`}</button>
            <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => { void onUploadSelected(e); }} />
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm overflow-x-auto">
            <h2 className="text-base font-semibold text-slate-900 mb-4">Dataset List</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500 bg-slate-50 border-b border-slate-100">
                  <th className="px-3 py-2 font-semibold">Dataset Name</th>
                  <th className="px-3 py-2 font-semibold">Source</th>
                  <th className="px-3 py-2 font-semibold">Period</th>
                  <th className="px-3 py-2 font-semibold">File Type</th>
                  <th className="px-3 py-2 font-semibold">Uploaded By</th>
                  <th className="px-3 py-2 font-semibold">Uploaded Date</th>
                  <th className="px-3 py-2 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {datasets.length > 0 ? datasets.map((row, idx) => (
                  <tr key={`${row.dataset_name}-${idx}`} className="border-b border-slate-100">
                    <td className="px-3 py-2 font-medium text-slate-800">{row.dataset_name}</td>
                    <td className="px-3 py-2">{row.source}</td>
                    <td className="px-3 py-2">{row.period}</td>
                    <td className="px-3 py-2">{row.file_type}</td>
                    <td className="px-3 py-2">{row.uploaded_by}</td>
                    <td className="px-3 py-2">{row.uploaded_date}</td>
                    <td className="px-3 py-2">{row.status}</td>
                  </tr>
                )) : <tr><td className="px-3 py-6 text-slate-500" colSpan={7}>No datasets for current filters.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
