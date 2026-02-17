import React, { useState, useEffect } from 'react';
import { Filter, ChevronDown } from 'lucide-react';

interface RSIDFilterProps {
  onFilterChange: (rsid: string | null, level: 'command' | 'brigade' | 'battalion' | 'station' | null) => void;
  currentRSID?: string | null;
}

// Army Recruiting Organizational Hierarchy
const RECRUITING_STRUCTURE = {
  brigades: [
    { id: '1BDE', name: '1st Recruiting Brigade' },
    { id: '2BDE', name: '2nd Recruiting Brigade' },
    { id: '3BDE', name: '3rd Recruiting Brigade' },
    { id: '4BDE', name: '4th Recruiting Brigade' },
    { id: '5BDE', name: '5th Recruiting Brigade' },
    { id: '6BDE', name: '6th Recruiting Brigade' },
  ],
  battalions: {
    '1BDE': ['1BN', '2BN', '3BN'],
    '2BDE': ['4BN', '5BN', '6BN'],
    '3BDE': ['7BN', '8BN', '9BN'],
    '4BDE': ['10BN', '11BN', '12BN'],
    '5BDE': ['13BN', '14BN', '15BN'],
    '6BDE': ['16BN', '17BN', '18BN'],
  },
  stations: {
    '1BN': ['1-1', '1-2', '1-3'],
    '2BN': ['2-1', '2-2', '2-3'],
    '3BN': ['3-1', '3-2', '3-3'],
    '4BN': ['4-1', '4-2', '4-3'],
    '5BN': ['5-1', '5-2', '5-3'],
    '6BN': ['6-1', '6-2', '6-3'],
    '7BN': ['7-1', '7-2', '7-3'],
    '8BN': ['8-1', '8-2', '8-3'],
    '9BN': ['9-1', '9-2', '9-3'],
    '10BN': ['10-1', '10-2', '10-3'],
    '11BN': ['11-1', '11-2', '11-3'],
    '12BN': ['12-1', '12-2', '12-3'],
    '13BN': ['13-1', '13-2', '13-3'],
    '14BN': ['14-1', '14-2', '14-3'],
    '15BN': ['15-1', '15-2', '15-3'],
    '16BN': ['16-1', '16-2', '16-3'],
    '17BN': ['17-1', '17-2', '17-3'],
    '18BN': ['18-1', '18-2', '18-3'],
  }
};

export const RSIDFilter: React.FC<RSIDFilterProps> = ({ onFilterChange, currentRSID }) => {
  const [selectedBrigade, setSelectedBrigade] = useState<string | null>(null);
  const [selectedBattalion, setSelectedBattalion] = useState<string | null>(null);
  const [selectedStation, setSelectedStation] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  // Parse current RSID on mount
  useEffect(() => {
    if (currentRSID) {
      const parts = currentRSID.split('-');
      if (parts.length >= 1) setSelectedBrigade(parts[0]);
      if (parts.length >= 2) setSelectedBattalion(parts[1]);
      if (parts.length >= 3) setSelectedStation(parts.slice(2).join('-'));
    }
  }, [currentRSID]);

  const handleBrigadeChange = (brigade: string | null) => {
    setSelectedBrigade(brigade);
    setSelectedBattalion(null);
    setSelectedStation(null);
    
    if (brigade) {
      onFilterChange(brigade, 'brigade');
    } else {
      onFilterChange(null, null);
    }
  };

  const handleBattalionChange = (battalion: string | null) => {
    setSelectedBattalion(battalion);
    setSelectedStation(null);
    
    if (battalion && selectedBrigade) {
      const rsid = `${selectedBrigade}-${battalion}`;
      onFilterChange(rsid, 'battalion');
    } else {
      onFilterChange(selectedBrigade, 'brigade');
    }
  };

  const handleStationChange = (station: string | null) => {
    setSelectedStation(station);
    
    if (station && selectedBrigade && selectedBattalion) {
      const rsid = `${selectedBrigade}-${selectedBattalion}-${station}`;
      onFilterChange(rsid, 'station');
    } else if (selectedBattalion && selectedBrigade) {
      const rsid = `${selectedBrigade}-${selectedBattalion}`;
      onFilterChange(rsid, 'battalion');
    } else {
      onFilterChange(selectedBrigade, 'brigade');
    }
  };

  const clearFilter = () => {
    setSelectedBrigade(null);
    setSelectedBattalion(null);
    setSelectedStation(null);
    onFilterChange(null, null);
  };

  const getFilterLabel = () => {
    if (selectedStation && selectedBattalion && selectedBrigade) {
      return `${selectedBrigade}-${selectedBattalion}-${selectedStation}`;
    }
    if (selectedBattalion && selectedBrigade) {
      return `${selectedBrigade}-${selectedBattalion}`;
    }
    if (selectedBrigade) {
      const brigade = RECRUITING_STRUCTURE.brigades.find(b => b.id === selectedBrigade);
      return brigade ? brigade.name : selectedBrigade;
    }
    return 'All Units';
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
      >
        <Filter className="w-4 h-4 text-gray-600" />
        <span className="font-medium text-gray-700">{getFilterLabel()}</span>
        <ChevronDown className={`w-4 h-4 text-gray-600 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
      </button>

      {showDropdown && (
        <div className="absolute top-full left-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-[300px] max-h-[500px] overflow-auto">
          {/* Header */}
          <div className="bg-blue-50 px-4 py-3 border-b border-blue-100">
            <h3 className="font-semibold text-blue-900">Unit Filter</h3>
            <p className="text-xs text-blue-700 mt-1">Select organizational level</p>
          </div>

          {/* Clear Filter */}
          {(selectedBrigade || selectedBattalion || selectedStation) && (
            <button
              onClick={clearFilter}
              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 border-b border-gray-200"
            >
              ✕ Clear Filter (Show All Units)
            </button>
          )}

          {/* Brigade Selection */}
          <div className="p-2">
            <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">Brigade</div>
            {RECRUITING_STRUCTURE.brigades.map((brigade) => (
              <button
                key={brigade.id}
                onClick={() => handleBrigadeChange(brigade.id)}
                className={`w-full px-3 py-2 text-left text-sm rounded hover:bg-blue-50 transition-colors ${
                  selectedBrigade === brigade.id ? 'bg-blue-100 text-blue-900 font-semibold' : 'text-gray-700'
                }`}
              >
                {brigade.id} - {brigade.name}
              </button>
            ))}
          </div>

          {/* Battalion Selection */}
          {selectedBrigade && (
            <div className="p-2 border-t border-gray-200">
              <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                Battalion (under {selectedBrigade})
              </div>
              {RECRUITING_STRUCTURE.battalions[selectedBrigade as keyof typeof RECRUITING_STRUCTURE.battalions]?.map((battalion) => (
                <button
                  key={battalion}
                  onClick={() => handleBattalionChange(battalion)}
                  className={`w-full px-3 py-2 text-left text-sm rounded hover:bg-blue-50 transition-colors ${
                    selectedBattalion === battalion ? 'bg-blue-100 text-blue-900 font-semibold' : 'text-gray-700'
                  }`}
                >
                  {battalion} - {battalion} Battalion
                </button>
              ))}
            </div>
          )}

          {/* Station Selection */}
          {selectedBattalion && (
            <div className="p-2 border-t border-gray-200">
              <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                Station (under {selectedBrigade}-{selectedBattalion})
              </div>
              {RECRUITING_STRUCTURE.stations[selectedBattalion as keyof typeof RECRUITING_STRUCTURE.stations]?.map((station) => (
                <button
                  key={station}
                  onClick={() => handleStationChange(station)}
                  className={`w-full px-3 py-2 text-left text-sm rounded hover:bg-blue-50 transition-colors ${
                    selectedStation === station ? 'bg-blue-100 text-blue-900 font-semibold' : 'text-gray-700'
                  }`}
                >
                  Station {station}
                </button>
              ))}
            </div>
          )}

          {/* Footer Info */}
          <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 text-xs text-gray-600">
            {selectedStation && selectedBattalion && selectedBrigade ? (
              <>Filtering: Station level ({selectedBrigade}-{selectedBattalion}-{selectedStation})</>
            ) : selectedBattalion && selectedBrigade ? (
              <>Filtering: Battalion level ({selectedBrigade}-{selectedBattalion})</>
            ) : selectedBrigade ? (
              <>Filtering: Brigade level ({selectedBrigade})</>
            ) : (
              <>Showing: All units</>
            )}
          </div>
        </div>
      )}

      {/* Overlay to close dropdown */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};
