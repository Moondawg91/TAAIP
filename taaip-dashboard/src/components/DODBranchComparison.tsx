import React, { useState, useEffect } from 'react';
import { BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { API_BASE } from '../config/api';

interface DODComparisonData {
  branch: string;
  geographic_level: string;
  geographic_id: string;
  geographic_name: string;
  recruiters: number;
  leads: number;
  contracts: number;
  ships: number;
  conversion_rates: {
    lead_to_contract: number;
    contract_to_ship: number;
  };
  efficiency_score: number;
  productivity: {
    contracts_per_recruiter: number;
  };
  fiscal_year: number;
  quarter: string;
}

const BRANCH_COLORS: { [key: string]: string } = {
  'Army': '#4B5320',
  'Navy': '#000080',
  'Air Force': '#5D8AA8',
  'Marines': '#CC0000',
  'Space Force': '#000000',
  'Coast Guard': '#FA4616'
};

const DODBranchComparison: React.FC = () => {
  const [comparisonData, setComparisonData] = useState<DODComparisonData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  const [geographicLevel, setGeographicLevel] = useState('cbsa');
  const [geographicId, setGeographicId] = useState('41860');
  const [fiscalYear, setFiscalYear] = useState(2025);
  const [quarter, setQuarter] = useState('Q4');
  const [vizType, setVizType] = useState<'bar' | 'radar' | 'table' | 'cards'>('cards');

  useEffect(() => {
    fetchComparisonData();
  }, [selectedBranch, geographicLevel, geographicId, fiscalYear, quarter]);

  const fetchComparisonData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        geographic_level: geographicLevel,
        geographic_id: geographicId,
        fiscal_year: fiscalYear.toString(),
        quarter: quarter
      });

      if (selectedBranch) {
        params.append('branch', selectedBranch);
      }

      const response = await fetch(`${API_BASE}/api/v2/dod-comparison?${params}`);
      const result = await response.json();
      
      if (result.status === 'ok') {
        setComparisonData(result.data);
      }
    } catch (error) {
      console.error('Error fetching comparison data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return num?.toLocaleString() || '0';
  };

  const getArmyRank = (metric: keyof DODComparisonData | string) => {
    const sorted = [...comparisonData].sort((a, b) => {
      if (metric === 'contracts_per_recruiter') {
        return b.productivity.contracts_per_recruiter - a.productivity.contracts_per_recruiter;
      } else if (metric === 'efficiency_score') {
        return b.efficiency_score - a.efficiency_score;
      } else if (metric === 'lead_to_contract') {
        return b.conversion_rates.lead_to_contract - a.conversion_rates.lead_to_contract;
      }
      return 0;
    });
    
    const armyIndex = sorted.findIndex(d => d.branch === 'Army');
    return armyIndex + 1;
  };

  const renderCards = () => {
    const sortedData = [...comparisonData].sort((a, b) => b.contracts - a.contracts);

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedData.map((branch, idx) => (
          <div 
            key={branch.branch}
            className="bg-white border-2 rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow"
            style={{ borderColor: BRANCH_COLORS[branch.branch] || '#gray' }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold" style={{ color: BRANCH_COLORS[branch.branch] }}>
                {branch.branch}
              </h3>
              <span className="text-sm px-2 py-1 bg-gray-100 rounded font-semibold">
                #{idx + 1}
              </span>
            </div>
            
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Total Contracts</p>
                <p className="text-2xl font-bold" style={{ color: BRANCH_COLORS[branch.branch] }}>
                  {formatNumber(branch.contracts)}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-xs text-gray-600">Recruiters</p>
                  <p className="text-lg font-semibold">{formatNumber(branch.recruiters)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Per Recruiter</p>
                  <p className="text-lg font-semibold text-green-600">
                    {branch.productivity.contracts_per_recruiter.toFixed(1)}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-xs text-gray-600">Leads</p>
                  <p className="text-sm font-semibold">{formatNumber(branch.leads)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Ships</p>
                  <p className="text-sm font-semibold">{formatNumber(branch.ships)}</p>
                </div>
              </div>

              <div>
                <p className="text-xs text-gray-600 mb-1">Conversion Rates</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Lead → Contract:</span>
                    <span className="font-semibold">{branch.conversion_rates.lead_to_contract}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Contract → Ship:</span>
                    <span className="font-semibold">{branch.conversion_rates.contract_to_ship}%</span>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-xs text-gray-600 mb-1">Efficiency Score</p>
                <div className="relative pt-1">
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all"
                      style={{ 
                        width: `${branch.efficiency_score}%`,
                        backgroundColor: BRANCH_COLORS[branch.branch]
                      }}
                    />
                  </div>
                  <p className="text-right text-sm font-semibold mt-1">{branch.efficiency_score}%</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderBarChart = () => {
    const chartData = comparisonData.map(branch => ({
      branch: branch.branch,
      contracts: branch.contracts,
      leads: branch.leads,
      ships: branch.ships,
      efficiency: branch.efficiency_score
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="branch" />
          <YAxis />
          <Tooltip formatter={(value) => formatNumber(Number(value))} />
          <Legend />
          <Bar dataKey="contracts" fill="#22c55e" name="Contracts" />
          <Bar dataKey="ships" fill="#3b82f6" name="Ships" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderRadarChart = () => {
    const radarData = comparisonData.map(branch => ({
      branch: branch.branch,
      productivity: branch.productivity.contracts_per_recruiter * 10, // Scale for visibility
      lead_conversion: branch.conversion_rates.lead_to_contract,
      ship_rate: branch.conversion_rates.contract_to_ship,
      efficiency: branch.efficiency_score
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={radarData}>
          <PolarGrid />
          <PolarAngleAxis dataKey="branch" />
          <PolarRadiusAxis />
          <Radar name="Productivity" dataKey="productivity" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
          <Radar name="Lead Conversion" dataKey="lead_conversion" stroke="#22c55e" fill="#22c55e" fillOpacity={0.6} />
          <Radar name="Ship Rate" dataKey="ship_rate" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    );
  };

  const renderTable = () => {
    const sortedData = [...comparisonData].sort((a, b) => b.contracts - a.contracts);

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Rank</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Branch</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Recruiters</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Leads</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Contracts</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Ships</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Per Recruiter</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">L→C Rate</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">C→S Rate</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Efficiency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedData.map((branch, idx) => (
              <tr 
                key={branch.branch} 
                className={`hover:bg-gray-50 ${branch.branch === 'Army' ? 'bg-green-50 font-semibold' : ''}`}
              >
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm font-bold text-gray-900">#{idx + 1}</span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm font-semibold" style={{ color: BRANCH_COLORS[branch.branch] }}>
                    {branch.branch}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{formatNumber(branch.recruiters)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{formatNumber(branch.leads)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold">{formatNumber(branch.contracts)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">{formatNumber(branch.ships)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-bold text-green-600">
                  {branch.productivity.contracts_per_recruiter.toFixed(1)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {branch.conversion_rates.lead_to_contract}%
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {branch.conversion_rates.contract_to_ship}%
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold">
                  {branch.efficiency_score}%
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
      case 'radar':
        return renderRadarChart();
      case 'table':
        return renderTable();
      case 'cards':
      default:
        return renderCards();
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading DOD comparison data...</div>;
  }

  const armyData = comparisonData.find(d => d.branch === 'Army');
  const productivityRank = getArmyRank('contracts_per_recruiter');
  const efficiencyRank = getArmyRank('efficiency_score');
  const conversionRank = getArmyRank('lead_to_contract');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">DOD Branch Comparison</h1>
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
            onClick={() => setVizType('radar')}
            className={`px-4 py-2 rounded ${vizType === 'radar' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Radar
          </button>
          <button
            onClick={() => setVizType('table')}
            className={`px-4 py-2 rounded ${vizType === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Table
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow flex gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Geographic Level</label>
          <select
            value={geographicLevel}
            onChange={(e) => setGeographicLevel(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2"
          >
            <option value="cbsa">CBSA (Metro Areas)</option>
            <option value="zipcode">ZIP Code</option>
            <option value="state">State</option>
            <option value="national">National</option>
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

      {/* Army Performance Summary */}
      {armyData && (
        <div className="bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-green-600 p-6 rounded-lg">
          <h2 className="text-xl font-bold text-green-800 mb-4">Army Competitive Position</h2>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-green-700">Total Contracts</p>
              <p className="text-3xl font-bold text-green-900">{formatNumber(armyData.contracts)}</p>
              <p className="text-xs text-green-600 mt-1">
                {comparisonData.findIndex(d => d.branch === 'Army') === 0 ? '🏆 #1 Overall' : `#{comparisonData.findIndex(d => d.branch === 'Army') + 1} Overall`}
              </p>
            </div>
            <div>
              <p className="text-sm text-green-700">Productivity Rank</p>
              <p className="text-3xl font-bold text-green-900">#{productivityRank}</p>
              <p className="text-xs text-green-600 mt-1">
                {armyData.productivity.contracts_per_recruiter.toFixed(1)} per recruiter
              </p>
            </div>
            <div>
              <p className="text-sm text-green-700">Efficiency Rank</p>
              <p className="text-3xl font-bold text-green-900">#{efficiencyRank}</p>
              <p className="text-xs text-green-600 mt-1">
                {armyData.efficiency_score}% score
              </p>
            </div>
            <div>
              <p className="text-sm text-green-700">Conversion Rank</p>
              <p className="text-3xl font-bold text-green-900">#{conversionRank}</p>
              <p className="text-xs text-green-600 mt-1">
                {armyData.conversion_rates.lead_to_contract}% L→C
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Visualization */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          All DOD Branches - {comparisonData[0]?.geographic_name || 'National'}
        </h2>
        {renderVisualization()}
      </div>

      {/* Where Army Leads & Lags */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-green-800 mb-3">🏆 Where Army Leads</h3>
          <ul className="space-y-2">
            {productivityRank === 1 && (
              <li className="text-sm text-green-700">✓ Highest contracts per recruiter</li>
            )}
            {efficiencyRank === 1 && (
              <li className="text-sm text-green-700">✓ Top efficiency score</li>
            )}
            {conversionRank === 1 && (
              <li className="text-sm text-green-700">✓ Best lead-to-contract conversion</li>
            )}
            {armyData && armyData.contracts === Math.max(...comparisonData.map(d => d.contracts)) && (
              <li className="text-sm text-green-700">✓ Most total contracts</li>
            )}
          </ul>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-red-800 mb-3">⚠️ Improvement Opportunities</h3>
          <ul className="space-y-2">
            {productivityRank > 3 && (
              <li className="text-sm text-red-700">• Contracts per recruiter below top 3</li>
            )}
            {efficiencyRank > 3 && (
              <li className="text-sm text-red-700">• Efficiency score needs improvement</li>
            )}
            {conversionRank > 3 && (
              <li className="text-sm text-red-700">• Lead conversion rate lagging</li>
            )}
            {armyData && armyData.conversion_rates.contract_to_ship < 80 && (
              <li className="text-sm text-red-700">• Contract-to-ship rate below 80%</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DODBranchComparison;
