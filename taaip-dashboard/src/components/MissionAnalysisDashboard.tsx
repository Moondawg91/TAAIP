import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface MissionAnalysisData {
  level: string;
  hierarchy: {
    usarec: string;
    brigade: string | null;
    battalion: string | null;
    company: string | null;
    station: string | null;
  };
  mission: {
    goal: number;
    actual: number;
    variance: number;
    attainment_pct: number;
  };
  production: {
    leads: number;
    appointments_made: number;
    appointments_conducted: number;
    tests_administered: number;
    tests_passed: number;
    enlistments: number;
    ships: number;
  };
  efficiency: {
    lead_to_enlistment_rate: number;
    appointment_show_rate: number;
    test_pass_rate: number;
  };
  fiscal_year: number;
  quarter: string;
}

const MissionAnalysisDashboard: React.FC = () => {
  const [missionData, setMissionData] = useState<MissionAnalysisData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState<'usarec' | 'brigade' | 'battalion' | 'company' | 'station'>('brigade');
  const [fiscalYear, setFiscalYear] = useState(2025);
  const [quarter, setQuarter] = useState('Q4');
  const [selectedBrigade, setSelectedBrigade] = useState<string | null>(null);
  const [selectedBattalion, setSelectedBattalion] = useState<string | null>(null);
  const [vizType, setVizType] = useState<'cards' | 'bar' | 'table'>('cards');

  useEffect(() => {
    fetchMissionData();
  }, [selectedLevel, fiscalYear, quarter, selectedBrigade, selectedBattalion]);

  const fetchMissionData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        analysis_level: selectedLevel,
        fiscal_year: fiscalYear.toString(),
        quarter: quarter
      });

      if (selectedBrigade) params.append('brigade', selectedBrigade);
      if (selectedBattalion) params.append('battalion', selectedBattalion);

      const response = await fetch(`http://localhost:8000/api/v2/mission-analysis?${params}`);
      const result = await response.json();
      
      if (result.status === 'ok') {
        setMissionData(result.data);
      }
    } catch (error) {
      console.error('Error fetching mission data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number) => {
    return num?.toLocaleString() || '0';
  };

  const getAttainmentColor = (pct: number) => {
    if (pct >= 100) return 'text-green-600';
    if (pct >= 90) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getAttainmentBgColor = (pct: number) => {
    if (pct >= 100) return 'bg-green-100';
    if (pct >= 90) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const renderCards = () => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {missionData.map((unit, idx) => {
          const unitName = unit.hierarchy.brigade || unit.hierarchy.battalion || unit.hierarchy.company || unit.hierarchy.station || 'USAREC';
          const attainmentColor = getAttainmentColor(unit.mission.attainment_pct);
          const attainmentBg = getAttainmentBgColor(unit.mission.attainment_pct);
          
          return (
            <div 
              key={idx}
              className={`border-2 rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow cursor-pointer ${attainmentBg}`}
              onClick={() => {
                if (selectedLevel === 'brigade' && unit.hierarchy.brigade) {
                  setSelectedBrigade(unit.hierarchy.brigade);
                  setSelectedLevel('battalion');
                } else if (selectedLevel === 'battalion' && unit.hierarchy.battalion) {
                  setSelectedBattalion(unit.hierarchy.battalion);
                  setSelectedLevel('company');
                }
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-800">{unitName}</h3>
                <span className={`text-2xl font-bold ${attainmentColor}`}>
                  {unit.mission.attainment_pct.toFixed(0)}%
                </span>
              </div>
              
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <p className="text-xs text-gray-600">Mission Goal</p>
                    <p className="text-lg font-semibold">{formatNumber(unit.mission.goal)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Actual</p>
                    <p className={`text-lg font-semibold ${attainmentColor}`}>
                      {formatNumber(unit.mission.actual)}
                    </p>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-gray-600 mb-1">Variance</p>
                  <p className={`text-xl font-bold ${unit.mission.variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {unit.mission.variance >= 0 ? '+' : ''}{formatNumber(unit.mission.variance)}
                  </p>
                </div>

                <div className="pt-2 border-t">
                  <p className="text-xs text-gray-600 mb-2">Production Pipeline</p>
                  <div className="grid grid-cols-3 gap-1 text-center">
                    <div>
                      <p className="text-xs text-gray-500">Leads</p>
                      <p className="text-sm font-semibold">{formatNumber(unit.production.leads)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Enlist</p>
                      <p className="text-sm font-semibold">{formatNumber(unit.production.enlistments)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Ships</p>
                      <p className="text-sm font-semibold">{formatNumber(unit.production.ships)}</p>
                    </div>
                  </div>
                </div>

                <div className="relative pt-2">
                  <div className="h-2 bg-gray-300">
                    <div 
                      className={`h-full transition-all ${
                        unit.mission.attainment_pct >= 100 ? 'bg-green-600' :
                        unit.mission.attainment_pct >= 90 ? 'bg-yellow-600' : 'bg-red-600'
                      }`}
                      style={{ width: `${Math.min(unit.mission.attainment_pct, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderBarChart = () => {
    const chartData = missionData.map(unit => ({
      name: unit.hierarchy.brigade || unit.hierarchy.battalion || unit.hierarchy.company || 'USAREC',
      goal: unit.mission.goal,
      actual: unit.mission.actual,
      variance: unit.mission.variance
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip formatter={(value) => formatNumber(Number(value))} />
          <Legend />
          <Bar dataKey="goal" fill="#94a3b8" name="Mission Goal" />
          <Bar dataKey="actual" fill="#22c55e" name="Actual Contracts" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderTable = () => {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Unit</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Goal</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Actual</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Variance</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Attainment</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Leads</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Enlistments</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Ships</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">L2E Rate</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {missionData.map((unit, idx) => {
              const unitName = unit.hierarchy.brigade || unit.hierarchy.battalion || unit.hierarchy.company || unit.hierarchy.station || 'USAREC';
              const attainmentColor = getAttainmentColor(unit.mission.attainment_pct);
              
              return (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-sm font-semibold text-gray-900">{unitName}</span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {formatNumber(unit.mission.goal)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold">
                    {formatNumber(unit.mission.actual)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    <span className={unit.mission.variance >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                      {unit.mission.variance >= 0 ? '+' : ''}{formatNumber(unit.mission.variance)}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`text-sm font-bold ${attainmentColor}`}>
                      {unit.mission.attainment_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {formatNumber(unit.production.leads)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {formatNumber(unit.production.enlistments)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {formatNumber(unit.production.ships)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {unit.efficiency.lead_to_enlistment_rate.toFixed(1)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  const renderVisualization = () => {
    switch (vizType) {
      case 'bar':
        return renderBarChart();
      case 'table':
        return renderTable();
      case 'cards':
      default:
        return renderCards();
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading mission analysis...</div>;
  }

  const totalGoal = missionData.reduce((sum, u) => sum + u.mission.goal, 0);
  const totalActual = missionData.reduce((sum, u) => sum + u.mission.actual, 0);
  const totalVariance = totalActual - totalGoal;
  const avgAttainment = totalGoal > 0 ? (totalActual / totalGoal) * 100 : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Mission Analysis</h1>
          <div className="flex gap-2 mt-2">
            {selectedBattalion && (
              <button
                onClick={() => {
                  setSelectedBattalion(null);
                  setSelectedLevel('battalion');
                }}
                className="text-sm text-blue-600 hover:underline"
              >
                ← Back to Battalions
              </button>
            )}
            {selectedBrigade && !selectedBattalion && (
              <button
                onClick={() => {
                  setSelectedBrigade(null);
                  setSelectedLevel('brigade');
                }}
                className="text-sm text-blue-600 hover:underline"
              >
                ← Back to Brigades
              </button>
            )}
          </div>
        </div>
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium opacity-90">Total Mission Goal</h3>
          <p className="text-2xl font-bold mt-2">{formatNumber(totalGoal)}</p>
          <p className="text-sm opacity-75 mt-1">FY{fiscalYear} {quarter}</p>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium opacity-90">Actual Contracts</h3>
          <p className="text-2xl font-bold mt-2">{formatNumber(totalActual)}</p>
          <p className="text-sm opacity-75 mt-1">{avgAttainment.toFixed(1)}% Attainment</p>
        </div>
        
        <div className={`bg-gradient-to-br ${totalVariance >= 0 ? 'from-green-400 to-green-500' : 'from-red-400 to-red-500'} text-white p-6 rounded-lg shadow`}>
          <h3 className="text-sm font-medium opacity-90">Variance</h3>
          <p className="text-2xl font-bold mt-2">
            {totalVariance >= 0 ? '+' : ''}{formatNumber(totalVariance)}
          </p>
          <p className="text-sm opacity-75 mt-1">{totalVariance >= 0 ? 'Exceeding Goal' : 'Below Goal'}</p>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium opacity-90">Units Reporting</h3>
          <p className="text-2xl font-bold mt-2">{missionData.length}</p>
          <p className="text-sm opacity-75 mt-1">
            {selectedBattalion ? 'Companies' : selectedBrigade ? 'Battalions' : 'Brigades'}
          </p>
        </div>
      </div>

      {/* Visualization */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          {selectedBattalion ? `${selectedBattalion} Companies` : 
           selectedBrigade ? `${selectedBrigade} Battalions` : 
           'Brigade Performance'}
        </h2>
        {renderVisualization()}
      </div>

      {/* Efficiency Metrics */}
      {missionData.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Efficiency Metrics</h2>
          <div className="grid grid-cols-3 gap-4">
            {missionData.slice(0, 3).map((unit, idx) => {
              const unitName = unit.hierarchy.brigade || unit.hierarchy.battalion || unit.hierarchy.company || 'USAREC';
              return (
                <div key={idx} className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-800 mb-3">{unitName}</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">L2E Rate:</span>
                      <span className="font-semibold">{unit.efficiency.lead_to_enlistment_rate.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Appt Show:</span>
                      <span className="font-semibold">{unit.efficiency.appointment_show_rate.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Test Pass:</span>
                      <span className="font-semibold">{unit.efficiency.test_pass_rate.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default MissionAnalysisDashboard;
