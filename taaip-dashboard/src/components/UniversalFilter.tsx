import React, { useState } from 'react';
import { Filter, X } from 'lucide-react';

interface UniversalFilterProps {
  onFilterChange: (filters: FilterState) => void;
  showRSID?: boolean;
  showZipcode?: boolean;
  showCBSA?: boolean;
}

export interface FilterState {
  rsid: string;
  zipcode: string;
  cbsa: string;
}

// Army Recruiting Brigade Structure
const BRIGADES = [
  { id: '1BDE', name: '1st Recruiting Brigade' },
  { id: '2BDE', name: '2nd Recruiting Brigade' },
  { id: '3BDE', name: '3rd Recruiting Brigade' },
  { id: '4BDE', name: '4th Recruiting Brigade' },
  { id: '5BDE', name: '5th Recruiting Brigade' },
  { id: '6BDE', name: '6th Recruiting Brigade' },
];

// Major Metropolitan ZIP Codes
const MAJOR_ZIPCODES = [
  { code: '78201', city: 'San Antonio, TX' },
  { code: '10001', city: 'New York, NY' },
  { code: '90001', city: 'Los Angeles, CA' },
  { code: '60601', city: 'Chicago, IL' },
  { code: '77001', city: 'Houston, TX' },
  { code: '19019', city: 'Philadelphia, PA' },
  { code: '85001', city: 'Phoenix, AZ' },
  { code: '75201', city: 'Dallas, TX' },
  { code: '32801', city: 'Orlando, FL' },
  { code: '30301', city: 'Atlanta, GA' },
];

// Major CBSAs
const MAJOR_CBSAS = [
  { code: '41700', name: 'San Antonio-New Braunfels, TX' },
  { code: '35620', name: 'New York-Newark-Jersey City, NY-NJ-PA' },
  { code: '31080', name: 'Los Angeles-Long Beach-Anaheim, CA' },
  { code: '16980', name: 'Chicago-Naperville-Elgin, IL-IN-WI' },
  { code: '26420', name: 'Houston-The Woodlands-Sugar Land, TX' },
  { code: '37980', name: 'Philadelphia-Camden-Wilmington, PA-NJ-DE-MD' },
  { code: '38060', name: 'Phoenix-Mesa-Scottsdale, AZ' },
  { code: '19100', name: 'Dallas-Fort Worth-Arlington, TX' },
  { code: '36740', name: 'Orlando-Kissimmee-Sanford, FL' },
  { code: '12060', name: 'Atlanta-Sandy Springs-Roswell, GA' },
];

export const UniversalFilter: React.FC<UniversalFilterProps> = ({ 
  onFilterChange,
  showRSID = true,
  showZipcode = true,
  showCBSA = true
}) => {
  const [filters, setFilters] = useState<FilterState>({
    rsid: '',
    zipcode: '',
    cbsa: ''
  });
  const [showPanel, setShowPanel] = useState(false);

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearFilters = () => {
    const emptyFilters = { rsid: '', zipcode: '', cbsa: '' };
    setFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };

  const activeFilterCount = Object.values(filters).filter(v => v).length;

  return (
    <div className="relative">
      <button
        onClick={() => setShowPanel(!showPanel)}
        className={`flex items-center gap-2 px-3 py-2 border transition-colors font-bold text-xs uppercase tracking-wide ${
          activeFilterCount > 0
            ? 'bg-yellow-600 border-yellow-700 text-black'
            : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
        }`}
      >
        <Filter className="w-4 h-4" />
        <span>Filters</span>
        {activeFilterCount > 0 && (
          <span className="bg-black text-yellow-500 text-xs px-2 py-0.5 font-bold">
            {activeFilterCount}
          </span>
        )}
      </button>

      {showPanel && (
        <div className="absolute right-0 mt-2 w-80 bg-white shadow-2xl border-2 border-gray-300 z-50">
          <div className="p-4 border-b-2 border-gray-300 flex items-center justify-between bg-gray-100">
            <h3 className="font-bold text-gray-900 uppercase tracking-wide text-sm">Filter Data</h3>
            <button
              onClick={() => setShowPanel(false)}
              className="text-gray-600 hover:text-gray-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {showRSID && (
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">
                  RSID (Brigade/Battalion)
                </label>
                <select
                  value={filters.rsid}
                  onChange={(e) => handleFilterChange('rsid', e.target.value)}
                  className="w-full px-3 py-2 border-2 border-gray-300 focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 text-sm"
                >
                  <option value="">All Units</option>
                  {BRIGADES.map(brigade => (
                    <option key={brigade.id} value={brigade.id}>
                      {brigade.name} ({brigade.id})
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1 uppercase tracking-wide">
                  Filter by recruiting brigade
                </p>
              </div>
            )}

            {showZipcode && (
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">
                  Zip Code
                </label>
                <select
                  value={filters.zipcode}
                  onChange={(e) => handleFilterChange('zipcode', e.target.value)}
                  className="w-full px-3 py-2 border-2 border-gray-300 focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 text-sm"
                >
                  <option value="">All Zip Codes</option>
                  {MAJOR_ZIPCODES.map(zip => (
                    <option key={zip.code} value={zip.code}>
                      {zip.code} - {zip.city}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1 uppercase tracking-wide">
                  Select major metropolitan area
                </p>
              </div>
            )}

            {showCBSA && (
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">
                  CBSA (Metro Area)
                </label>
                <select
                  value={filters.cbsa}
                  onChange={(e) => handleFilterChange('cbsa', e.target.value)}
                  className="w-full px-3 py-2 border-2 border-gray-300 focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 text-sm"
                >
                  <option value="">All Metro Areas</option>
                  {MAJOR_CBSAS.map(cbsa => (
                    <option key={cbsa.code} value={cbsa.code}>
                      {cbsa.name} ({cbsa.code})
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1 uppercase tracking-wide">
                  Core Based Statistical Area
                </p>
              </div>
            )}

            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className="w-full py-2 px-4 bg-red-600 text-white hover:bg-red-700 transition-colors flex items-center justify-center gap-2 font-bold text-xs uppercase tracking-wide"
              >
                <X className="w-4 h-4" />
                Clear All Filters
              </button>
            )}
          </div>

          <div className="p-3 bg-gray-100 border-t-2 border-gray-300">
            <p className="text-xs text-gray-600 uppercase tracking-wide">
              ℹ️ Filters apply in real-time
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
