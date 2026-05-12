import React, { useState, useEffect } from 'react';
import { Eye } from 'lucide-react';
import { DynamicDashboard } from './DynamicDashboard';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { UniversalFilter, FilterState } from './UniversalFilter';
import { ExportButton } from './ExportButton';
import { API_BASE } from '../config/api';

interface MarketPotentialData {
  geographic_level: string;
  geographic_id: string;
  geographic_name: string;
  brigade: string;
  battalion: string;
  qualified_population: number;
  army: BranchData;
  navy: BranchData;
  air_force: BranchData;
  marines: BranchData;
  space_force: BranchData;
  coast_guard: BranchData;
  total_dod: { contacted: number; remaining: number };
  fiscal_year: number;
  quarter: string;
}

interface BranchData {
  contacted: number;
  remaining: number;
  market_share: number;
}

const BRANCH_COLORS = {
  army: '#4B5320',
  navy: '#000080',
  air_force: '#5D8AA8',
  marines: '#CC0000',
  space_force: '#000000',
  coast_guard: '#FA4616'
};

const MarketPotentialDashboard: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketPotentialData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGeographicLevel, setSelectedGeographicLevel] = useState('cbsa');
  const [selectedGeographicId, setSelectedGeographicId] = useState('41860'); // San Francisco
  const [fiscalYear, setFiscalYear] = useState(2025);
  const [quarter, setQuarter] = useState('Q4');
  const [vizType, setVizType] = useState<'bar' | 'line' | 'pie' | 'cards' | 'table'>('cards');
  const [filters, setFilters] = useState<FilterState>({ rsid: '', zipcode: '', cbsa: '' });

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  useEffect(() => {
    fetchMarketData();
  }, [selectedGeographicLevel, selectedGeographicId, fiscalYear, quarter, filters]);

  const fetchMarketData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        geographic_level: selectedGeographicLevel,
        geographic_id: selectedGeographicId,
        fiscal_year: fiscalYear.toString(),
        quarter: quarter
      });
      
      if (filters.rsid) params.append('rsid', filters.rsid);
      if (filters.zipcode) params.append('zipcode', filters.zipcode);
      if (filters.cbsa) params.append('cbsa', filters.cbsa);

      const response = await fetch(`${API_BASE}/api/v2/market/potential?${params}`);
      const result = await response.json();
      
      if (result.status === 'ok' && Array.isArray(result.data)) {
        setMarketData(result.data);
      } else {
        setMarketData([]);
      }
    } catch (error) {
      console.error('Error fetching market data:', error);
      setMarketData([]);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return num?.toLocaleString() || '0';
  };

  const getBranchComparisonData = () => {
    if (marketData.length === 0) return [];
    
    const data = marketData[0];
    return [
      { name: 'Army', contacted: data.army.contacted, remaining: data.army.remaining, market_share: data.army.market_share, color: BRANCH_COLORS.army },
      { name: 'Navy', contacted: data.navy.contacted, remaining: data.navy.remaining, market_share: data.navy.market_share, color: BRANCH_COLORS.navy },
      { name: 'Air Force', contacted: data.air_force.contacted, remaining: data.air_force.remaining, market_share: data.air_force.market_share, color: BRANCH_COLORS.air_force },
      { name: 'Marines', contacted: data.marines.contacted, remaining: data.marines.remaining, market_share: data.marines.market_share, color: BRANCH_COLORS.marines },
      { name: 'Space Force', contacted: data.space_force.contacted, remaining: data.space_force.remaining, market_share: data.space_force.market_share, color: BRANCH_COLORS.space_force },
      { name: 'Coast Guard', contacted: data.coast_guard.contacted, remaining: data.coast_guard.remaining, market_share: data.coast_guard.market_share, color: BRANCH_COLORS.coast_guard }
    ].sort((a, b) => b.market_share - a.market_share);
  };

  const renderCards = () => {
    const comparisonData = getBranchComparisonData();
    if (comparisonData.length === 0) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {comparisonData.map((branch, idx) => (
          <div 
            key={branch.name}
            className="bg-white border-2 p-6 hover:border-gray-400 transition-colors"
            style={{ borderColor: branch.color }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold" style={{ color: branch.color }}>
                {branch.name}
              </h3>
              <span className="text-sm px-2 py-1 bg-gray-100 rounded">
                #{idx + 1}
              </span>
            </div>
            
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Market Share</p>
                <p className="text-2xl font-bold" style={{ color: branch.color }}>
                  {branch.market_share}%
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-xs text-gray-600">Contacted</p>
                  <p className="text-lg font-semibold">{formatNumber(branch.contacted)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Remaining</p>
                  <p className="text-lg font-semibold">{formatNumber(branch.remaining)}</p>
                </div>
              </div>

              <div className="relative pt-2">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all"
                    style={{ 
                      width: `${branch.market_share}%`,
                      backgroundColor: branch.color
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderBarChart = () => {
    const comparisonData = getBranchComparisonData();
    
    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={comparisonData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip formatter={(value) => formatNumber(Number(value))} />
          <Legend />
          <Bar dataKey="contacted" fill="#4ade80" name="Contacted" />
          <Bar dataKey="remaining" fill="#fbbf24" name="Remaining Potential" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderPieChart = () => {
    const comparisonData = getBranchComparisonData();
    
    return (
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={comparisonData}
            dataKey="market_share"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={120}
            label={(entry) => `${entry.name}: ${entry.market_share}%`}
          >
            {comparisonData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `${Number(value).toFixed(2)}%`} />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderTable = () => {
    const comparisonData = getBranchComparisonData();
    
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Rank</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Branch</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Market Share</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Contacted</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Remaining</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Total Pool</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {comparisonData.map((branch, idx) => (
              <tr key={branch.name} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-bold text-gray-900">#{idx + 1}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-semibold" style={{ color: branch.color }}>
                    {branch.name}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-bold">{branch.market_share}%</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatNumber(branch.contacted)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatNumber(branch.remaining)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                  {formatNumber(branch.contacted + branch.remaining)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderVisualization = () => {
    switch (vizType) {
      case 'bar':
        return renderBarChart();
      case 'pie':
        return renderPieChart();
      case 'table':
        return renderTable();
      case 'cards':
      default:
        return renderCards();
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading market data...</div>;
  }

  const currentData = marketData[0];

  return (
    <div className="p-6 space-y-6">
      {/* Header with Filters */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Market Potential Analysis</h1>
        <div className="flex gap-3 items-center">
          <UniversalFilter 
            onFilterChange={handleFilterChange}
            showRSID={true}
            showZipcode={true}
            showCBSA={true}
          />
          <ExportButton 
            data={marketData}
            filename="market-potential-data"
          />
          <div className="flex gap-2">
            <button
              onClick={() => setVizType('cards')}
              className={`px-4 py-2 rounded ${vizType === 'cards' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Cards
            </button>
            <button
              onClick={() => setVizType('bar')}
              className={`px-4 py-2 rounded ${vizType === 'bar' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Bar Chart
            </button>
            <button
              onClick={() => setVizType('pie')}
              className={`px-4 py-2 rounded ${vizType === 'pie' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Pie Chart
            </button>
            <button
              onClick={() => setVizType('table')}
              className={`px-4 py-2 rounded ${vizType === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Table
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 border-2 border-gray-300 flex gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Geographic Level</label>
          <select
            value={selectedGeographicLevel}
            onChange={(e) => setSelectedGeographicLevel(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2"
          >
            <option value="cbsa">CBSA (Metro Areas)</option>
            <option value="zipcode">ZIP Code</option>
            <option value="rsid">RSID</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fiscal Year</label>
          <select
            value={fiscalYear}
            onChange={(e) => setFiscalYear(Number(e.target.value))}
            className="border border-gray-300 rounded px-3 py-2"
          >
            <option value={2024}>FY2024</option>
            <option value={2025}>FY2025</option>
            <option value={2026}>FY2026</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Quarter</label>
          <select
            value={quarter}
            onChange={(e) => setQuarter(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2"
          >
            <option value="Q1">Q1 (Oct-Dec)</option>
            <option value="Q2">Q2 (Jan-Mar)</option>
            <option value="Q3">Q3 (Apr-Jun)</option>
            <option value="Q4">Q4 (Jul-Sep)</option>
          </select>
        </div>
      </div>

      {/* Summary Stats */}
      {currentData && (
        <div className="grid grid-cols-4 gap-px bg-gray-300">
          <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
            <h3 className="text-xs uppercase tracking-wide text-gray-300">Location</h3>
            <p className="text-2xl font-bold text-yellow-500 mt-2">{currentData.geographic_name}</p>
            <p className="text-sm text-gray-400 mt-1">{currentData.brigade} / {currentData.battalion}</p>
          </div>
          
          <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
            <h3 className="text-xs uppercase tracking-wide text-gray-800">Total DOD Contacted</h3>
            <p className="text-2xl font-bold text-black mt-2">{formatNumber(currentData.total_dod.contacted)}</p>
            <p className="text-sm text-gray-900 mt-1">All Branches Combined</p>
          </div>
          
          <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
            <h3 className="text-xs uppercase tracking-wide text-gray-300">Remaining Potential</h3>
            <p className="text-2xl font-bold text-yellow-500 mt-2">{formatNumber(currentData.total_dod.remaining)}</p>
            <p className="text-sm text-gray-400 mt-1">Qualified Population</p>
          </div>
          
          <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
            <h3 className="text-xs uppercase tracking-wide text-gray-800">Army Market Share</h3>
            <p className="text-2xl font-bold text-black mt-2">{currentData.army.market_share}%</p>
            <p className="text-sm text-gray-900 mt-1">
              {currentData.army.market_share > 35 ? '🏆 Leading' : currentData.army.market_share > 25 ? '📈 Strong' : '⚠️ Opportunity'}
            </p>
          </div>
        </div>
      )}

      {/* Visualization */}
      <div className="bg-white p-6 border-2 border-gray-300">
        <h2 className="text-xl font-bold text-gray-800 mb-4">DOD Branch Comparison</h2>
        {renderVisualization()}
      </div>

      {/* Smart Visuals - Auto Generated */}
      <div className="bg-white border-2 border-gray-300 rounded-lg mt-6">
        <div className="flex items-center justify-between px-6 py-4 border-b-2 border-gray-300 bg-gray-100">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <Eye className="w-4 h-4 text-blue-600" /> Smart Visuals (Market Potential Data)
          </h3>
          <span className="text-xs text-gray-500">Source /api/v2/market-potential</span>
        </div>
        <DynamicDashboard dataType="projects" />
      </div>

      {/* Army Performance Highlight */}
      {currentData && (
        <div className="bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-green-600 p-6 rounded-lg">
          <h3 className="text-lg font-bold text-green-800 mb-2">Army Performance Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-green-700">Contacted</p>
              <p className="text-2xl font-bold text-green-900">{formatNumber(currentData.army.contacted)}</p>
            </div>
            <div>
              <p className="text-sm text-green-700">Remaining Potential</p>
              <p className="text-2xl font-bold text-green-900">{formatNumber(currentData.army.remaining)}</p>
            </div>
            <div>
              <p className="text-sm text-green-700">Penetration Rate</p>
              <p className="text-2xl font-bold text-green-900">
                {((currentData.army.contacted / (currentData.army.contacted + currentData.army.remaining)) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketPotentialDashboard;
