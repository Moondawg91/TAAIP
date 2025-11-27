import React from 'react';
import { Printer } from 'lucide-react';

export const PrintButton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <button
    onClick={() => window.print()}
    className={`flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-900 font-bold transition-colors ${className}`}
    title="Print dashboard"
  >
    <Printer className="w-5 h-5" />
    <span>Print</span>
  </button>
);

export default PrintButton;
