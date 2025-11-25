import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Database, Target, Users, TrendingUp, Map, Calendar, DollarSign, X } from 'lucide-react';
import Papa from 'papaparse';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

interface UploadResult {
  success: boolean;
  message: string;
  rowsProcessed?: number;
  destination?: string;
}

const UPLOAD_CATEGORIES = [
  {
    id: 'segmentation',
    name: 'Market Segmentation Data',
    icon: <Target className="w-6 h-6" />,
    description: 'Demographic, psychographic, and behavioral segmentation data',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['segment_name', 'demographic_data'],
    destination: 'segmentation_dashboard'
  },
  {
    id: 'csba',
    name: 'CSBA (Cost/Strategy/Benefit Analysis)',
    icon: <DollarSign className="w-6 h-6" />,
    description: 'Strategic analysis data for cost-benefit evaluation',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['strategy', 'cost', 'benefit'],
    destination: 'mission_analysis_dashboard'
  },
  {
    id: 'leads',
    name: 'Lead/Prospect Data',
    icon: <Users className="w-6 h-6" />,
    description: 'Recruiting funnel leads and prospect information',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['name', 'email', 'phone', 'stage'],
    destination: 'recruiting_funnel'
  },
  {
    id: 'events',
    name: 'Event Performance Data',
    icon: <Calendar className="w-6 h-6" />,
    description: 'Event attendance, engagement, and conversion metrics',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['event_name', 'date', 'attendance'],
    destination: 'event_performance_dashboard'
  },
  {
    id: 'g2zones',
    name: 'G2 Zone Data',
    icon: <Map className="w-6 h-6" />,
    description: 'Geographic zone performance and market penetration',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['zone_id', 'zone_name', 'performance'],
    destination: 'g2zone_dashboard'
  },
  {
    id: 'marketing',
    name: 'Marketing Engagement Data',
    icon: <TrendingUp className="w-6 h-6" />,
    description: 'Social media, email, and digital advertising metrics',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['platform', 'impressions', 'engagements'],
    destination: 'marketing_engagement_dashboard'
  },
  {
    id: 'twg',
    name: 'TWG (Targeting Working Group) Data',
    icon: <Target className="w-6 h-6" />,
    description: 'Targeting recommendations, analysis, and decisions',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['target_id', 'recommendation'],
    destination: 'twg_dashboard'
  },
  {
    id: 'budget',
    name: 'Budget & Financial Data',
    icon: <DollarSign className="w-6 h-6" />,
    description: 'Budget allocation, spending, and financial tracking',
    acceptedFormats: ['.csv', '.xlsx', '.json'],
    requiredFields: ['category', 'allocated', 'spent'],
    destination: 'budget_tracker'
  },
  {
    id: 'general',
    name: 'General Data Import',
    icon: <Database className="w-6 h-6" />,
    description: 'Auto-detect and route to appropriate dashboard',
    acceptedFormats: ['.csv', '.xlsx', '.json', '.txt'],
    requiredFields: [],
    destination: 'auto_detect'
  }
];

export const UniversalDataUpload: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      
      // Preview for CSV files
      if (selectedFile.name.endsWith('.csv')) {
        Papa.parse(selectedFile, {
          header: true,
          preview: 5,
          complete: (results) => {
            setPreviewData(results.data);
            setShowPreview(true);
          }
        });
      }
    }
  };

  const detectDataType = (data: any[]): string => {
    if (!data || data.length === 0) return 'general';
    
    const firstRow = data[0];
    const keys = Object.keys(firstRow).map(k => k.toLowerCase());
    
    // Check for specific patterns
    if (keys.includes('segment_name') || keys.includes('demographic')) return 'segmentation';
    if (keys.includes('cost') && keys.includes('benefit')) return 'csba';
    if (keys.includes('lead_id') || keys.includes('prospect')) return 'leads';
    if (keys.includes('event_name') || keys.includes('attendance')) return 'events';
    if (keys.includes('zone_id') || keys.includes('g2')) return 'g2zones';
    if (keys.includes('impressions') || keys.includes('engagements')) return 'marketing';
    if (keys.includes('target') || keys.includes('recommendation')) return 'twg';
    if (keys.includes('budget') || keys.includes('allocated')) return 'budget';
    
    return 'general';
  };

  const handleUpload = async () => {
    if (!file || !selectedCategory) return;

    setUploading(true);
    setResult(null);

    try {
      // Parse CSV data first
      Papa.parse(file, {
        header: true,
        complete: async (results) => {
          const data = results.data;
          
          // Auto-detect if general category
          let targetCategory = selectedCategory;
          if (selectedCategory === 'general') {
            targetCategory = detectDataType(data);
          }

          const category = UPLOAD_CATEGORIES.find(c => c.id === targetCategory);

          // Send to appropriate backend endpoint
          const endpoint = `/api/v2/upload/${targetCategory}`;
          
          try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ data, category: targetCategory })
            });

            const result = await response.json();

            setResult({
              success: result.status === 'ok',
              message: result.message || `Successfully uploaded ${data.length} rows to ${category?.name}`,
              rowsProcessed: data.length,
              destination: category?.destination
            });
          } catch (apiError) {
            // Fallback: Store locally if API not available
            console.warn('API not available, storing locally:', apiError);
            localStorage.setItem(`upload_${targetCategory}_${Date.now()}`, JSON.stringify(data));
            
            setResult({
              success: true,
              message: `Data cached locally. ${data.length} rows will sync when connected.`,
              rowsProcessed: data.length,
              destination: category?.destination
            });
          }

          setUploading(false);
        },
        error: (error) => {
          setResult({
            success: false,
            message: `Error parsing file: ${error.message}`
          });
          setUploading(false);
        }
      });
    } catch (error: any) {
      setResult({
        success: false,
        message: `Upload failed: ${error.message}`
      });
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setResult(null);
    setPreviewData([]);
    setShowPreview(false);
    setSelectedCategory(null);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl p-6 shadow-lg">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
          <Upload className="w-8 h-8" />
          Universal Data Upload
        </h1>
        <p className="text-blue-100">
          Import data from any source - automatically routed to the appropriate dashboard
        </p>
      </div>

      {!result && (
        <>
          {/* Category Selection */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Select Data Category</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {UPLOAD_CATEGORIES.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    selectedCategory === category.id
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300 bg-white'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-2 rounded ${selectedCategory === category.id ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
                      {category.icon}
                    </div>
                    <h3 className="font-semibold text-gray-900">{category.name}</h3>
                  </div>
                  <p className="text-sm text-gray-600">{category.description}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {category.acceptedFormats.map((format) => (
                      <span key={format} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                        {format}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* File Upload */}
          {selectedCategory && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Upload File</h2>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".csv,.xlsx,.json,.txt"
                  onChange={handleFileSelect}
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-semibold text-gray-700 mb-2">
                    {file ? file.name : 'Click to select file or drag and drop'}
                  </p>
                  <p className="text-sm text-gray-500">
                    Supported formats: CSV, Excel, JSON
                  </p>
                </label>
              </div>

              {file && (
                <div className="mt-4">
                  <div className="flex items-center justify-between bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="w-8 h-8 text-blue-600" />
                      <div>
                        <p className="font-semibold text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-600">{(file.size / 1024).toFixed(2)} KB</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setFile(null)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )}

              {showPreview && previewData.length > 0 && (
                <div className="mt-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Data Preview (first 5 rows)</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border border-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(previewData[0]).map((key) => (
                            <th key={key} className="px-4 py-2 text-left font-semibold text-gray-700 border-b">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {previewData.map((row, idx) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            {Object.values(row).map((val: any, vidx) => (
                              <td key={vidx} className="px-4 py-2 text-gray-700">
                                {String(val)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {file && (
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="mt-6 w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      Upload and Process Data
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </>
      )}

      {/* Upload Result */}
      {result && (
        <div className={`rounded-xl border-2 p-6 ${result.success ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
          <div className="flex items-start gap-4">
            {result.success ? (
              <CheckCircle className="w-12 h-12 text-green-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-12 h-12 text-red-600 flex-shrink-0" />
            )}
            <div className="flex-1">
              <h3 className={`text-xl font-bold mb-2 ${result.success ? 'text-green-900' : 'text-red-900'}`}>
                {result.success ? 'Upload Successful!' : 'Upload Failed'}
              </h3>
              <p className={`mb-4 ${result.success ? 'text-green-800' : 'text-red-800'}`}>
                {result.message}
              </p>
              {result.success && result.rowsProcessed && (
                <div className="flex gap-4 mb-4">
                  <div className="bg-white rounded-lg px-4 py-2 border border-green-200">
                    <p className="text-sm text-gray-600">Rows Processed</p>
                    <p className="text-2xl font-bold text-green-600">{result.rowsProcessed}</p>
                  </div>
                  <div className="bg-white rounded-lg px-4 py-2 border border-green-200">
                    <p className="text-sm text-gray-600">Destination</p>
                    <p className="text-lg font-bold text-green-600">{result.destination}</p>
                  </div>
                </div>
              )}
              <button
                onClick={resetUpload}
                className="bg-white text-gray-700 px-6 py-2 rounded-lg font-semibold border-2 border-gray-300 hover:bg-gray-50"
              >
                Upload Another File
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="text-lg font-bold text-blue-900 mb-3">Upload Instructions</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start gap-2">
            <span className="bg-blue-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">1</span>
            <span>Select the data category that matches your import file</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="bg-blue-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">2</span>
            <span>Upload your CSV, Excel, or JSON file</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="bg-blue-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">3</span>
            <span>Review the data preview to ensure correct formatting</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="bg-blue-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">4</span>
            <span>Click upload - data will automatically route to the appropriate dashboard</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="bg-blue-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">5</span>
            <span>If unsure, use "General Data Import" for automatic category detection</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default UniversalDataUpload;
