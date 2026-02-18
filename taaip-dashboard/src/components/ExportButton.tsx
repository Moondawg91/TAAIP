import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileText, Database, ChevronDown } from 'lucide-react';

interface ExportButtonProps {
  data: any[];
  filename: string;
  className?: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ data, filename, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);

  const exportToCSV = () => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          const value = row[header];
          const stringValue = value === null || value === undefined ? '' : String(value);
          // Escape quotes and wrap in quotes if contains comma
          return stringValue.includes(',') || stringValue.includes('"') 
            ? `"${stringValue.replace(/"/g, '""')}"` 
            : stringValue;
        }).join(',')
      )
    ].join('\n');

    downloadFile(csvContent, `${filename}.csv`, 'text/csv');
    setIsOpen(false);
  };

  const exportToExcel = () => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    // Create Excel-compatible HTML table
    const headers = Object.keys(data[0]);
    const htmlContent = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
      <head><meta charset="UTF-8"></head>
      <body>
        <table border="1">
          <thead>
            <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
          </thead>
          <tbody>
            ${data.map(row => 
              `<tr>${headers.map(h => `<td>${row[h] ?? ''}</td>`).join('')}</tr>`
            ).join('')}
          </tbody>
        </table>
      </body>
      </html>
    `;

    downloadFile(htmlContent, `${filename}.xls`, 'application/vnd.ms-excel');
    setIsOpen(false);
  };

  const exportToJSON = () => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, `${filename}.json`, 'application/json');
    setIsOpen(false);
  };

  const exportToFormattedText = () => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    const headers = Object.keys(data[0]);
    const colWidths = headers.map(h => 
      Math.max(h.length, ...data.map(row => String(row[h] ?? '').length))
    );

    const formatRow = (row: any) => 
      headers.map((h, i) => String(row[h] ?? '').padEnd(colWidths[i])).join(' | ');

    const separator = colWidths.map(w => '-'.repeat(w)).join('-+-');

    const formattedContent = [
      formatRow(Object.fromEntries(headers.map(h => [h, h]))),
      separator,
      ...data.map(formatRow)
    ].join('\n');

    downloadFile(formattedContent, `${filename}.txt`, 'text/plain');
    setIsOpen(false);
  };

  const exportToPDF = () => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    // Create HTML for PDF printing
    const headers = Object.keys(data[0]);
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>${filename}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          h1 { color: #2563eb; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #2563eb; color: white; font-weight: bold; }
          tr:nth-child(even) { background-color: #f9fafb; }
          .footer { margin-top: 20px; font-size: 12px; color: #666; }
        </style>
      </head>
      <body>
        <h1>${filename}</h1>
        <p>Generated: ${new Date().toLocaleString()}</p>
        <table>
          <thead>
            <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
          </thead>
          <tbody>
            ${data.map(row => 
              `<tr>${headers.map(h => `<td>${row[h] ?? ''}</td>`).join('')}</tr>`
            ).join('')}
          </tbody>
        </table>
        <div class="footer">
          <p>TAAIP - Talent Acquisition Analytics and Intelligence Platform</p>
          <p>Total Records: ${data.length}</p>
        </div>
      </body>
      </html>
    `;

    // Open in new window for printing
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      printWindow.onload = () => {
        printWindow.print();
      };
    }
    setIsOpen(false);
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-2 bg-gray-700 text-gray-300 hover:bg-gray-600 flex items-center gap-2 border border-gray-600 font-bold text-xs uppercase tracking-wide"
      >
        <Download className="w-4 h-4" />
        Export
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-64 bg-white shadow-2xl border-2 border-gray-300 z-50">
            <div className="bg-gray-100 px-4 py-2 border-b-2 border-gray-300">
              <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider">Export Options</h3>
            </div>
            <div>
              <button
                onClick={exportToCSV}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 text-gray-700 border-b border-gray-200"
              >
                <FileSpreadsheet className="w-5 h-5 text-green-600" />
                <div>
                  <div className="font-bold text-sm">CSV</div>
                  <div className="text-xs text-gray-500">Comma-separated values</div>
                </div>
              </button>

              <button
                onClick={exportToExcel}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 text-gray-700 border-b border-gray-200"
              >
                <FileSpreadsheet className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="font-bold text-sm">Excel</div>
                  <div className="text-xs text-gray-500">Microsoft Excel format</div>
                </div>
              </button>

              <button
                onClick={exportToPDF}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 text-gray-700 border-b border-gray-200"
              >
                <FileText className="w-5 h-5 text-red-600" />
                <div>
                  <div className="font-bold text-sm">PDF</div>
                  <div className="text-xs text-gray-500">Print-ready document</div>
                </div>
              </button>

              <button
                onClick={exportToJSON}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 text-gray-700 border-b border-gray-200"
              >
                <Database className="w-5 h-5 text-purple-600" />
                <div>
                  <div className="font-bold text-sm">JSON</div>
                  <div className="text-xs text-gray-500">Raw data format</div>
                </div>
              </button>

              <button
                onClick={exportToFormattedText}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 text-gray-700"
              >
                <FileText className="w-5 h-5 text-gray-600" />
                <div>
                  <div className="font-bold text-sm">Formatted Text</div>
                  <div className="text-xs text-gray-500">Table-formatted .txt</div>
                </div>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
