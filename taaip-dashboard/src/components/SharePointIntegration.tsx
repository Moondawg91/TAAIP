import React, { useState, useEffect } from 'react';
import { 
  FolderOpen, File, Download, Upload, Share2, Search, 
  FileText, Image, Video, Archive, RefreshCw, Trash2,
  ChevronRight, ChevronDown, Plus, X
} from 'lucide-react';
import { API_BASE } from '../config/api';

interface SharePointFile {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size: number;
  modified: string;
  modifiedBy: string;
  path: string;
  url: string;
  fileType: string;
}

interface SharePointFolder {
  id: string;
  name: string;
  path: string;
  files: SharePointFile[];
  subfolders: SharePointFolder[];
}

export const SharePointIntegration: React.FC = () => {
  const [currentPath, setCurrentPath] = useState('/');
  const [files, setFiles] = useState<SharePointFile[]>([]);
  const [folders, setFolders] = useState<SharePointFolder[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [selectedFileForShare, setSelectedFileForShare] = useState<SharePointFile | null>(null);

  useEffect(() => {
    loadSharePointContent();
  }, [currentPath]);

  const loadSharePointContent = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v2/integrations/sharepoint/browse?path=${encodeURIComponent(currentPath)}`);
      const data = await response.json();
      
      if (data.status === 'ok') {
        setFiles(data.files || []);
        setFolders(data.folders || []);
      }
    } catch (error) {
      console.error('Error loading SharePoint content:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (fileId: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
  };

  const handleDownload = async (file: SharePointFile) => {
    try {
      const response = await fetch(`${API_BASE}/api/v2/integrations/sharepoint/download/${file.id}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download file');
    }
  };

  const handleUpload = async (files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });
    formData.append('path', currentPath);

    try {
      const response = await fetch(`${API_BASE}/api/v2/integrations/sharepoint/upload`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        loadSharePointContent();
        setUploadModalOpen(false);
        alert('Files uploaded successfully!');
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload files');
    }
  };

  const handleShare = async (file: SharePointFile, emails: string[]) => {
    try {
      const response = await fetch(`${API_BASE}/api/v2/integrations/sharepoint/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_id: file.id,
          emails: emails
        })
      });
      
      if (response.ok) {
        alert('File shared successfully!');
        setShareModalOpen(false);
        setSelectedFileForShare(null);
      }
    } catch (error) {
      console.error('Share failed:', error);
      alert('Failed to share file');
    }
  };

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('image')) return <Image className="w-5 h-5 text-blue-500" />;
    if (fileType.includes('video')) return <Video className="w-5 h-5 text-purple-500" />;
    if (fileType.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />;
    if (fileType.includes('zip') || fileType.includes('archive')) return <Archive className="w-5 h-5 text-yellow-600" />;
    return <File className="w-5 h-5 text-gray-500" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-xl shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold uppercase tracking-wider flex items-center gap-3">
              <FolderOpen className="w-8 h-8 text-yellow-500" />
              SharePoint Integration
            </h1>
            <p className="text-gray-300 mt-2">TAAIP | G2 Report Zone | Document Management</p>
          </div>
          <button
            onClick={loadSharePointContent}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-black font-semibold rounded hover:bg-yellow-400"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="bg-white rounded-xl shadow-md p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          {/* Search */}
          <div className="flex-1 min-w-[300px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search files and folders..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Actions */}
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700"
          >
            <Upload className="w-4 h-4" />
            Upload
          </button>
          
          {selectedFiles.size > 0 && (
            <>
              <button
                onClick={() => {
                  const file = files.find(f => f.id === Array.from(selectedFiles)[0]);
                  if (file) handleDownload(file);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Download className="w-4 h-4" />
                Download ({selectedFiles.size})
              </button>
              <button
                onClick={() => setSelectedFiles(new Set())}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                <Trash2 className="w-4 h-4" />
                Clear Selection
              </button>
            </>
          )}
        </div>

        {/* Breadcrumb */}
        <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
          <span className="cursor-pointer hover:text-gray-900" onClick={() => setCurrentPath('/')}>
            Home
          </span>
          {currentPath.split('/').filter(Boolean).map((part, index, arr) => (
            <React.Fragment key={index}>
              <ChevronRight className="w-4 h-4" />
              <span 
                className={`cursor-pointer hover:text-gray-900 ${index === arr.length - 1 ? 'font-semibold text-gray-900' : ''}`}
                onClick={() => setCurrentPath('/' + arr.slice(0, index + 1).join('/'))}
              >
                {part}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading SharePoint content...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">
                    <input
                      type="checkbox"
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedFiles(new Set(files.map(f => f.id)));
                        } else {
                          setSelectedFiles(new Set());
                        }
                      }}
                      checked={selectedFiles.size === files.length && files.length > 0}
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Size</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Modified</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Modified By</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {/* Folders */}
                {folders.map(folder => (
                  <tr 
                    key={folder.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => setCurrentPath(folder.path)}
                  >
                    <td className="px-6 py-4"></td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <FolderOpen className="w-5 h-5 text-yellow-600" />
                        <span className="font-semibold text-gray-900">{folder.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-500">--</td>
                    <td className="px-6 py-4 text-gray-500">--</td>
                    <td className="px-6 py-4 text-gray-500">--</td>
                    <td className="px-6 py-4"></td>
                  </tr>
                ))}

                {/* Files */}
                {filteredFiles.map(file => (
                  <tr key={file.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedFiles.has(file.id)}
                        onChange={() => handleFileSelect(file.id)}
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {getFileIcon(file.fileType)}
                        <span className="text-gray-900">{file.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{formatFileSize(file.size)}</td>
                    <td className="px-6 py-4 text-gray-600">{new Date(file.modified).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-gray-600">{file.modifiedBy}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleDownload(file)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                          title="Download"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedFileForShare(file);
                            setShareModalOpen(true);
                          }}
                          className="p-2 text-green-600 hover:bg-green-50 rounded"
                          title="Share"
                        >
                          <Share2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredFiles.length === 0 && folders.length === 0 && (
              <div className="p-12 text-center text-gray-500">
                <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>No files or folders found</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Upload Files</h3>
              <button onClick={() => setUploadModalOpen(false)}>
                <X className="w-6 h-6 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
            <input
              type="file"
              multiple
              onChange={(e) => {
                if (e.target.files) handleUpload(e.target.files);
              }}
              className="w-full border-2 border-dashed border-gray-300 rounded-lg p-4"
            />
          </div>
        </div>
      )}

      {/* Share Modal */}
      {shareModalOpen && selectedFileForShare && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Share File</h3>
              <button onClick={() => setShareModalOpen(false)}>
                <X className="w-6 h-6 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
            <p className="text-gray-600 mb-4">Sharing: {selectedFileForShare.name}</p>
            <input
              type="text"
              placeholder="Enter email addresses (comma separated)"
              className="w-full border border-gray-300 rounded-lg p-3 mb-4"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const emails = (e.target as HTMLInputElement).value.split(',').map(e => e.trim());
                  handleShare(selectedFileForShare, emails);
                }
              }}
            />
            <button
              onClick={() => {
                const input = document.querySelector('input[placeholder*="email"]') as HTMLInputElement;
                const emails = input.value.split(',').map(e => e.trim());
                handleShare(selectedFileForShare, emails);
              }}
              className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700"
            >
              Share File
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
