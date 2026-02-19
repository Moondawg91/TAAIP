import React, { useState } from 'react';
import { Upload, FileCheck, Download, AlertCircle, CheckCircle, Info, ChevronDown } from 'lucide-react';
import { API_BASE } from '../config/api';

interface UploadResult {
  status: string;
  imported: number;
  total_rows: number;
  errors?: string[];
  message: string;
}

const DATA_TYPES = [
  { id: 'leads', label: 'Leads', description: 'Initial contacts and inquiries' },
  { id: 'prospects', label: 'Prospects', description: 'Qualified and contacted leads' },
  { id: 'applicants', label: 'Applicants', description: 'Active applicants in process' },
  { id: 'future_soldiers', label: 'Future Soldiers', description: 'Contracted soldiers awaiting ship date' },
  { id: 'events', label: 'Events', description: 'Recruiting events and activities' },
  { id: 'projects', label: 'Projects', description: 'Project management and tracking' },
  { id: 'marketing_activities', label: 'Marketing Activities', description: 'Marketing campaigns and initiatives' },
  { id: 'budgets', label: 'Budgets', description: 'Budget allocation and tracking' },
];

export const UploadData: React.FC = () => {
  const [selectedType, setSelectedType] = useState('leads');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [showTemplateInfo, setShowTemplateInfo] = useState(true);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [showMappingModal, setShowMappingModal] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});

  const currentDataType = DATA_TYPES.find(dt => dt.id === selectedType);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    const validTypes = ['.csv', '.xlsx', '.xls'];
    const fileExt = '.' + selectedFile.name.split('.').pop()?.toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
      alert('Please upload a CSV or Excel file (.csv, .xlsx, .xls)');
      return;
    }
    
    setFile(selectedFile);
    setResult(null);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    // Step 1: preview file to allow mapping
    setUploading(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const previewResp = await fetch(`${API_BASE}/api/v2/upload/preview`, { method: 'POST', body: formData });
      if (!previewResp.ok) {
        const e = await previewResp.json();
        throw new Error(e.detail || 'Preview failed');
      }
      const previewJson = await previewResp.json();
      setPreview(previewJson);

      // build default mapping: try to auto-match uploaded columns to known fields
      const knownFields = [...fieldInfo.required, ...fieldInfo.optional];
      const mappingInit: Record<string, string> = {};
      (previewJson.columns || []).forEach((col: string) => {
        const lower = col.toLowerCase();
        const match = knownFields.find(f => f.toLowerCase() === lower || f.toLowerCase() === lower.replace(/\s|_/g, ''));
        if (match) mappingInit[col] = match;
        else mappingInit[col] = '';
      });
      // try to load a previously saved mapping for this data type and merge
      try {
        const saved = await fetch(`${API_BASE}/api/v2/upload/mappings/${selectedType}`);
        if (saved.ok) {
          const sm = await saved.json();
          if (sm && sm.mapping) {
            // map saved target fields onto uploaded columns where possible
            Object.keys(mappingInit).forEach(col => {
              if (sm.mapping[col]) mappingInit[col] = sm.mapping[col];
            });
          }
        }
      } catch (e) {
        // ignore mapping load errors
        console.warn('Failed to load saved mapping', e);
      }
      setColumnMapping(mappingInit);
      setShowMappingModal(true);
    } catch (error: any) {
      setResult({ status: 'error', imported: 0, total_rows: 0, message: error.message || 'Preview failed', errors: [error.message] });
      setUploading(false);
    }
  };

  const confirmMappingAndUpload = async () => {
    if (!file) return;
    setUploading(true);
    setShowMappingModal(false);
    try {
      // validate required fields are mapped
      const requiredFields = fieldInfo.required || [];
      const mappedTargets = Object.values(columnMapping || {}).filter(Boolean);
      const missingRequired = requiredFields.filter((req: string) => !mappedTargets.includes(req));
      if (missingRequired.length > 0) {
        setResult({ status: 'error', imported: 0, total_rows: 0, message: `Missing mappings for required fields: ${missingRequired.join(', ')}`, errors: ["Please map all required fields before uploading."] });
        setUploading(false);
        setShowMappingModal(true);
        return;
      }

      // persist mapping for future uploads (best-effort)
      try {
        const mform = new FormData();
        mform.append('data_type', selectedType);
        mform.append('mapping', JSON.stringify(columnMapping));
        await fetch(`${API_BASE}/api/v2/upload/save_mapping`, { method: 'POST', body: mform });
      } catch (e) {
        console.warn('Failed to save mapping', e);
      }
      // if replace flag set, create server backup first
      if (replaceExisting) {
        const bak = await fetch(`${API_BASE}/api/v2/upload/backup`, { method: 'POST' });
        if (!bak.ok) {
          const be = await bak.json();
          throw new Error(be.detail || 'Backup failed');
        }
      }

      const formData = new FormData();
      formData.append('file', file);
      // send mapping as JSON string in form field 'mapping'
      formData.append('mapping', JSON.stringify(columnMapping));

      const uploadUrl = `${API_BASE}/api/v2/upload/${selectedType}${replaceExisting ? '?replace=true' : ''}`;
      const resp = await fetch(uploadUrl, { method: 'POST', body: formData });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Upload failed');
      setResult(data);
      if (data.status === 'success') setFile(null);
    } catch (error: any) {
      setResult({ status: 'error', imported: 0, total_rows: 0, message: error.message || 'Upload failed', errors: [error.message] });
    } finally {
      setUploading(false);
    }
  };

  const updateMapping = (col: string, val: string) => {
    setColumnMapping(prev => ({ ...prev, [col]: val }));
  };

  const downloadTemplate = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v2/upload/templates`);
      const templates = await response.json();
      const template = templates[selectedType];
      
      if (!template) return;

      // Create CSV from template
      const headers = [...template.required, ...template.optional];
      const exampleRow = template.example;
      
      let csv = headers.join(',') + '\n';
      csv += headers.map(h => exampleRow[h] || '').join(',');

      // Download
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedType}_template.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download template:', error);
    }
  };

  const getFieldInfo = () => {
    const fieldInfo: Record<string, any> = {
      leads: {
        required: ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid'],
        optional: ['cbsa_code', 'middle_name', 'address', 'asvab_score']
      },
      prospects: {
        required: ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid', 'prospect_status'],
        optional: ['cbsa_code', 'middle_name', 'address', 'asvab_score', 'last_contact_date', 'recruiter_assigned', 'notes']
      },
      applicants: {
        required: ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid', 'application_date', 'applicant_status'],
        optional: ['cbsa_code', 'middle_name', 'address', 'asvab_score', 'meps_scheduled_date', 'recruiter_assigned', 'mos_preference']
      },
      future_soldiers: {
        required: ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid', 'contract_date', 'ship_date', 'mos_assigned', 'future_soldier_status'],
        optional: ['cbsa_code', 'middle_name', 'address', 'asvab_score', 'recruiter_assigned', 'unit_assignment']
      },
      events: {
        required: ['name', 'location', 'start_date', 'end_date'],
        optional: ['type', 'budget', 'team_size', 'targeting_principles', 'status']
      },
      projects: {
        required: ['name', 'owner_id', 'start_date', 'target_date', 'objectives'],
        optional: ['event_id', 'funding_amount', 'status']
      },
      marketing_activities: {
        required: ['activity_name', 'campaign_type', 'start_date', 'end_date', 'budget_allocated'],
        optional: ['target_audience', 'channels', 'leads_generated', 'cost_per_lead', 'status']
      },
      budgets: {
        required: ['campaign_name', 'allocated_amount', 'start_date', 'end_date'],
        optional: ['event_id', 'spent_amount', 'remaining_amount', 'fiscal_year']
      }
    };

    return fieldInfo[selectedType] || { required: [], optional: [] };
  };

  const fieldInfo = getFieldInfo();

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-extrabold text-gray-900 mb-2 flex items-center">
          <Upload className="w-8 h-8 mr-3 text-blue-600" />
          Upload Data
        </h2>
        <p className="text-gray-600">
          Bulk import data from CSV or Excel files into your TAAIP system
        </p>
      </div>

      {/* Data Type Selector */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          Select Data Type
        </label>
        <div className="relative">
          <select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setFile(null);
              setResult(null);
            }}
            className="w-full px-4 py-3 pr-10 bg-white border-2 border-gray-300 rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base font-medium"
          >
            {DATA_TYPES.map(type => (
              <option key={type.id} value={type.id}>
                {type.label} - {type.description}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
        </div>
        
        {currentDataType && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-800">
              <strong>{currentDataType.label}:</strong> {currentDataType.description}
            </p>
          </div>
        )}
      </div>

      {/* Template Information */}
      {showTemplateInfo && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 mb-6 border-l-4 border-blue-600">
          <div className="flex justify-between items-start mb-3">
            <h3 className="text-lg font-bold text-gray-900 flex items-center">
              <Info className="w-5 h-5 mr-2 text-blue-600" />
              Required Fields for {currentDataType?.label}
            </h3>
            <button
              onClick={() => setShowTemplateInfo(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-2">Required Columns:</h4>
              <ul className="space-y-1">
                {fieldInfo.required.map((field: string) => (
                  <li key={field} className="text-sm text-gray-600 flex items-center">
                    <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    {field}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-2">Optional Columns:</h4>
              <ul className="space-y-1">
                {fieldInfo.optional.map((field: string) => (
                  <li key={field} className="text-sm text-gray-600 flex items-center">
                    <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                    {field}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <button
            onClick={downloadTemplate}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center text-sm font-medium"
          >
            <Download className="w-4 h-4 mr-2" />
            Download Template for {currentDataType?.label}
          </button>
        </div>
      )}

      {/* Replace toggle (admin) */}
      <div className="mt-4 mb-6 flex items-center gap-3">
        <input id="replaceToggle" type="checkbox" checked={replaceExisting} onChange={(e) => setReplaceExisting(e.target.checked)} className="w-4 h-4" />
        <label htmlFor="replaceToggle" className="text-sm text-gray-700">Replace existing data (admin only) — creates backup before replace</label>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow-md p-8">
        <div
          className={`border-3 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : file
              ? 'border-green-500 bg-green-50'
              : 'border-gray-300 bg-gray-50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {!file ? (
            <>
              <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-semibold text-gray-700 mb-2">
                Drag and drop your file here
              </p>
              <p className="text-sm text-gray-500 mb-4">or</p>
              <label className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer inline-block transition-colors font-medium">
                Browse Files
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileInput}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-400 mt-4">
                Supported formats: CSV, Excel (.xlsx, .xls)
              </p>
            </>
          ) : (
            <>
              <FileCheck className="w-16 h-16 mx-auto mb-4 text-green-600" />
              <p className="text-lg font-semibold text-gray-700 mb-2">
                {file.name}
              </p>
              <p className="text-sm text-gray-500 mb-4">
                {(file.size / 1024).toFixed(2)} KB
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                    uploading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {uploading ? 'Uploading...' : `Upload ${currentDataType?.label}`}
                </button>
                <button
                  onClick={() => setFile(null)}
                  disabled={uploading}
                  className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                >
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className={`mt-6 rounded-lg shadow-md p-6 ${
          result.status === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex items-start">
            {result.status === 'success' ? (
              <CheckCircle className="w-6 h-6 text-green-600 mr-3 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600 mr-3 flex-shrink-0" />
            )}
            <div className="flex-1">
              <h3 className={`text-lg font-bold mb-2 ${
                result.status === 'success' ? 'text-green-900' : 'text-red-900'
              }`}>
                {result.message}
              </h3>
              
              {result.status === 'success' && (
                <div className="text-sm text-green-800 space-y-1">
                  <p>✓ Successfully imported: <strong>{result.imported}</strong> records</p>
                  <p>Total rows processed: <strong>{result.total_rows}</strong></p>
                </div>
              )}

                {/* Mapping Modal */}
                {showMappingModal && preview && (
                  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg w-11/12 max-w-3xl p-6">
                      <h3 className="text-lg font-bold mb-3">Preview & Field Mapping</h3>
                      <p className="text-sm text-gray-600 mb-3">File: {preview.filename} — {preview.row_count} rows. Map uploaded columns to target fields below.</p>
                      <div className="max-h-96 overflow-y-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left">
                              <th className="p-2 border-b">Uploaded Column</th>
                              <th className="p-2 border-b">Sample</th>
                              <th className="p-2 border-b">Map To Field</th>
                            </tr>
                          </thead>
                          <tbody>
                            {preview.columns.map((col: string, idx: number) => (
                              <tr key={col} className="align-top">
                                <td className="p-2 border-b align-top"><strong>{col}</strong></td>
                                <td className="p-2 border-b align-top">{(preview.sample_rows && preview.sample_rows[0] && preview.sample_rows[0][col]) || ''}</td>
                                <td className="p-2 border-b align-top">
                                  <select value={columnMapping[col] || ''} onChange={(e) => updateMapping(col, e.target.value)} className="w-full px-2 py-1 border rounded">
                                    <option value="">-- ignore --</option>
                                    {[...fieldInfo.required, ...fieldInfo.optional].map(f => (
                                      <option key={f} value={f}>{f}</option>
                                    ))}
                                  </select>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="mt-4 flex justify-end gap-3">
                        <button onClick={() => setShowMappingModal(false)} className="px-4 py-2 bg-gray-200 rounded">Cancel</button>
                        <button onClick={confirmMappingAndUpload} className="px-4 py-2 bg-blue-600 text-white rounded">Confirm & Upload</button>
                      </div>
                    </div>
                  </div>
                )}

              {result.errors && result.errors.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-semibold text-red-900 mb-2">
                    Errors ({result.errors.length}):
                  </p>
                  <div className="bg-white rounded border border-red-300 p-3 max-h-60 overflow-y-auto">
                    {result.errors.map((error, idx) => (
                      <p key={idx} className="text-xs text-red-700 mb-1">
                        • {error}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Info Note */}
      <div className="mt-6 p-4 bg-gray-100 rounded-lg">
        <p className="text-sm text-gray-600">
          <strong>Note:</strong> Auto-generated Smart Visuals now appear embedded at the bottom of key dashboards (Analytics, Funnel, Market, Mission, Events) after successful uploads.
        </p>
      </div>
    </div>
  );
};
