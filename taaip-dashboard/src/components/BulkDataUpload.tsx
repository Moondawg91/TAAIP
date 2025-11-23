import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, XCircle, Download, AlertCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface UploadResult {
  status: string;
  imported: number;
  total_rows: number;
  errors: string[] | null;
  message: string;
}

export const BulkDataUpload: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'events' | 'projects' | 'leads'>('events');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    // Validate file type
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
      setResult({
        status: 'error',
        imported: 0,
        total_rows: 0,
        errors: ['Only CSV and Excel files (.csv, .xlsx, .xls) are supported'],
        message: 'Invalid file type'
      });
      return;
    }

    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/api/v2/import/${activeTab}`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setResult(data);
      } else {
        setResult({
          status: 'error',
          imported: 0,
          total_rows: 0,
          errors: [data.detail || 'Upload failed'],
          message: 'Upload failed'
        });
      }
    } catch (error) {
      setResult({
        status: 'error',
        imported: 0,
        total_rows: 0,
        errors: ['Network error. Is the backend running?'],
        message: 'Upload failed'
      });
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = (type: string) => {
    let csvContent = '';
    
    if (type === 'events') {
      csvContent = 'name,type,location,start_date,end_date,budget,team_size,targeting_principles,status\n';
      csvContent += 'Spring Job Fair 2025,recruitment_event,San Antonio TX,2025-03-15,2025-03-15,5000,10,USAREC Cycle,planned\n';
      csvContent += 'College Visit - UTSA,college_visit,San Antonio TX,2025-04-10,2025-04-10,1000,5,USAREC Cycle,planned\n';
    } else if (type === 'projects') {
      csvContent = 'name,owner_id,start_date,target_date,objectives,event_id,funding_amount,status\n';
      csvContent += 'Q1 Digital Campaign,SSG Smith,2025-01-01,2025-03-31,Increase leads by 20%,EVT-12345,25000,in_progress\n';
      csvContent += 'Social Media Outreach,SGT Jones,2025-02-01,2025-04-30,Boost engagement,EVT-12346,15000,planning\n';
    } else if (type === 'leads') {
      csvContent = 'lead_id,age,education_level,cbsa_code,campaign_source,propensity_score\n';
      csvContent += 'LEAD-001,20,High School,41700,social_media,7\n';
      csvContent += 'LEAD-002,22,Some College,41700,web,8\n';
      csvContent += 'LEAD-003,19,High School,41700,event,6\n';
    }

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `taaip_${type}_template.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <h2 className="text-3xl font-extrabold text-gray-900">
          <Upload className="inline-block mr-2 w-7 h-7 text-blue-600" />
          Bulk Data Upload
        </h2>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          Upload CSV or Excel Files
        </h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Drag and drop your file or click to browse</li>
          <li>Supports CSV (.csv) and Excel (.xlsx, .xls) formats</li>
          <li>Download template below to see required column format</li>
          <li>Invalid rows will be skipped with error details</li>
        </ul>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-2 border-b">
        <button
          onClick={() => { setActiveTab('events'); setResult(null); }}
          className={`px-4 py-3 font-medium transition ${
            activeTab === 'events'
              ? 'border-b-2 border-green-600 text-green-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Events
        </button>
        <button
          onClick={() => { setActiveTab('projects'); setResult(null); }}
          className={`px-4 py-3 font-medium transition ${
            activeTab === 'projects'
              ? 'border-b-2 border-blue-600 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Projects
        </button>
        <button
          onClick={() => { setActiveTab('leads'); setResult(null); }}
          className={`px-4 py-3 font-medium transition ${
            activeTab === 'leads'
              ? 'border-b-2 border-purple-600 text-purple-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Leads
        </button>
      </div>

      {/* Download Template Button */}
      <div className="flex justify-center">
        <button
          onClick={() => downloadTemplate(activeTab)}
          className="flex items-center px-6 py-3 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition font-medium"
        >
          <Download className="w-5 h-5 mr-2" />
          Download {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Template
        </button>
      </div>

      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-xl p-12 text-center transition ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-white hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="fileInput"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileInput}
          className="hidden"
          disabled={uploading}
        />
        
        <label htmlFor="fileInput" className="cursor-pointer">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-semibold text-gray-700 mb-2">
            {uploading ? 'Uploading...' : 'Drop your file here or click to browse'}
          </p>
          <p className="text-sm text-gray-500">
            CSV or Excel files only (.csv, .xlsx, .xls)
          </p>
        </label>
      </div>

      {/* Results */}
      {result && (
        <div className={`border rounded-lg p-6 ${
          result.status === 'success' ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300'
        }`}>
          <div className="flex items-start">
            {result.status === 'success' ? (
              <CheckCircle className="w-6 h-6 text-green-600 mr-3 mt-0.5" />
            ) : (
              <XCircle className="w-6 h-6 text-red-600 mr-3 mt-0.5" />
            )}
            <div className="flex-1">
              <h3 className={`font-bold text-lg mb-2 ${
                result.status === 'success' ? 'text-green-900' : 'text-red-900'
              }`}>
                {result.message}
              </h3>
              
              {result.status === 'success' && (
                <p className="text-green-800 mb-2">
                  Imported <strong>{result.imported}</strong> of <strong>{result.total_rows}</strong> rows
                </p>
              )}

              {result.errors && result.errors.length > 0 && (
                <div className="mt-3">
                  <p className="font-semibold text-red-900 mb-2">Errors:</p>
                  <ul className="text-sm text-red-800 space-y-1 max-h-60 overflow-y-auto">
                    {result.errors.map((error, idx) => (
                      <li key={idx} className="border-l-2 border-red-400 pl-2">
                        {error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Column Reference */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="font-bold text-gray-900 mb-3">
          Required Columns for {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
        </h3>
        <div className="text-sm text-gray-700 space-y-1">
          {activeTab === 'events' && (
            <>
              <p><strong>Required:</strong> name, location, start_date, end_date</p>
              <p><strong>Optional:</strong> type, budget, team_size, targeting_principles, status</p>
              <p><strong>Date Format:</strong> YYYY-MM-DD (e.g., 2025-03-15)</p>
            </>
          )}
          {activeTab === 'projects' && (
            <>
              <p><strong>Required:</strong> name, owner_id, start_date, target_date, objectives</p>
              <p><strong>Optional:</strong> event_id, funding_amount, status</p>
              <p><strong>Date Format:</strong> YYYY-MM-DD (e.g., 2025-01-01)</p>
            </>
          )}
          {activeTab === 'leads' && (
            <>
              <p><strong>Required:</strong> age, education_level, cbsa_code, campaign_source</p>
              <p><strong>Optional:</strong> propensity_score (1-10), lead_id</p>
              <p><strong>Age Range:</strong> 17-42 (Army eligibility)</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
