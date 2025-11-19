import React, { useState, useEffect } from 'react';
import { Trophy, TrendingUp, TrendingDown, Minus, Award } from 'lucide-react';
import { ExportButton } from './ExportButton';

interface CompanyStanding {
  rank: number;
  previous_rank: number;
  company_id: string;
  company_name: string;
  battalion: string;
  brigade: string;
  rsid: string;
  station: string;
  ytd_mission: number;
  ytd_actual: number;
  ytd_attainment: number;
  monthly_mission: number;
  monthly_actual: number;
  monthly_attainment: number;
  total_enlistments: number;
  future_soldier_losses: number;
  net_gain: number;
  last_enlistment: string | null;
  trend: 'up' | 'down' | 'stable';
}

export const CompanyStandingsLeaderboard: React.FC = () => {
  const [standings, setStandings] = useState<CompanyStanding[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [filterValue, setFilterValue] = useState<string>('all');
  const [filterType, setFilterType] = useState<'brigade' | 'rsid' | 'station'>('brigade');
  const [viewMode, setViewMode] = useState<'ytd' | 'monthly'>('ytd');

  const fetchStandings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v2/standings/companies');
      const data = await response.json();
      if (data.status === 'ok') {
        setStandings(data.standings);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Error fetching company standings:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStandings();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchStandings, 30000);
    return () => clearInterval(interval);
  }, []);

  const filteredStandings = standings.filter(s => {
    if (filterValue === 'all') return true;
    
    if (filterType === 'brigade') return s.brigade === filterValue;
    if (filterType === 'rsid') return s.rsid === filterValue;
    if (filterType === 'station') return s.station === filterValue;
    
    return true;
  });

  const brigades = Array.from(new Set(standings.map(s => s.brigade))).sort();
  const rsids = Array.from(new Set(standings.map(s => s.rsid))).sort();
  const stations = Array.from(new Set(standings.map(s => s.station))).sort();
  
  const filterOptions = filterType === 'brigade' ? brigades : 
                        filterType === 'rsid' ? rsids : stations;
  
  const handleFilterTypeChange = (type: 'brigade' | 'rsid' | 'station') => {
    setFilterType(type);
    setFilterValue('all');
  };
  
  // Prepare export data
  const exportData = filteredStandings.map(c => ({
    Rank: c.rank,
    Company: c.company_name,
    Battalion: c.battalion,
    Brigade: c.brigade,
    RSID: c.rsid,
    Station: c.station,
    Mission: viewMode === 'ytd' ? c.ytd_mission : c.monthly_mission,
    Actual: viewMode === 'ytd' ? c.ytd_actual : c.monthly_actual,
    'Attainment %': (viewMode === 'ytd' ? c.ytd_attainment : c.monthly_attainment).toFixed(1),
    'Net Gain': c.net_gain,
    'Losses': c.future_soldier_losses,
    'Last Enlistment': c.last_enlistment || 'N/A'
  }));

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white';
    if (rank === 2) return 'bg-gradient-to-br from-gray-300 to-gray-400 text-gray-800';
    if (rank === 3) return 'bg-gradient-to-br from-orange-400 to-orange-600 text-white';
    return 'bg-gray-100 text-gray-700';
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="w-5 h-5 text-yellow-300" />;
    if (rank === 2) return <Award className="w-5 h-5 text-gray-500" />;
    if (rank === 3) return <Award className="w-5 h-5 text-orange-400" />;
    return null;
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getAttainmentColor = (attainment: number) => {
    if (attainment >= 100) return 'text-green-600 font-bold';
    if (attainment >= 85) return 'text-blue-600 font-semibold';
    if (attainment >= 70) return 'text-yellow-600 font-semibold';
    return 'text-red-600 font-semibold';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-md border-2 border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-md border-2 border-gray-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white px-6 py-4 border-b-2 border-yellow-500 rounded-t-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold uppercase tracking-wider flex items-center gap-2">
              <Trophy className="w-6 h-6 text-yellow-500" />
              Company Standings - YTD Mission
            </h2>
            <p className="text-sm text-gray-300 mt-1">Real-time competition scoreboard • Auto-updates every 30 seconds</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400">Last Update</p>
            <p className="text-sm font-semibold text-yellow-500">{lastUpdate.toLocaleTimeString()}</p>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-semibold text-gray-700">Filter By:</label>
          <div className="flex border border-gray-300 rounded overflow-hidden">
            <button
              onClick={() => handleFilterTypeChange('brigade')}
              className={`px-3 py-1 text-sm font-medium ${filterType === 'brigade' ? 'bg-gray-800 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
              title="Filter by Brigade"
            >
              Brigade
            </button>
            <button
              onClick={() => handleFilterTypeChange('rsid')}
              className={`px-3 py-1 text-sm font-medium ${filterType === 'rsid' ? 'bg-gray-800 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
              title="Filter by RSID"
            >
              RSID
            </button>
            <button
              onClick={() => handleFilterTypeChange('station')}
              className={`px-3 py-1 text-sm font-medium ${filterType === 'station' ? 'bg-gray-800 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
              title="Filter by Station"
            >
              Station
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filterValue}
            onChange={(e) => setFilterValue(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm"
            title={`Filter by ${filterType}`}
          >
            <option value="all">All {filterType === 'brigade' ? 'Brigades' : filterType === 'rsid' ? 'RSIDs' : 'Stations'}</option>
            {filterOptions.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-semibold text-gray-700">View:</label>
          <div className="flex border border-gray-300 rounded overflow-hidden">
            <button
              onClick={() => setViewMode('ytd')}
              className={`px-3 py-1 text-sm font-medium ${viewMode === 'ytd' ? 'bg-yellow-500 text-black' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
              title="Year-to-date mission attainment"
            >
              YTD
            </button>
            <button
              onClick={() => setViewMode('monthly')}
              className={`px-3 py-1 text-sm font-medium ${viewMode === 'monthly' ? 'bg-yellow-500 text-black' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
              title="Current month mission attainment"
            >
              Monthly
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <ExportButton
            data={exportData}
            filename={`company_standings_${viewMode}_${new Date().toISOString().split('T')[0]}`}
            className="bg-gray-800 text-white hover:bg-gray-700"
          />
        </div>

        <div className="w-full flex items-center gap-2 text-xs text-gray-600 justify-end">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>≥100%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-blue-500 rounded"></div>
            <span>85-99%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>70-84%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>&lt;70%</span>
          </div>
        </div>
      </div>

      {/* Leaderboard */}
      <div className="overflow-hidden">
        <div className="max-h-[600px] overflow-y-auto">
          <table className="w-full">
            <thead className="bg-gray-100 sticky top-0 z-10">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase" title="Current ranking position">Rank</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase" title="Company name and unit">Company</th>
                <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase" title="Mission goal for the period">Mission</th>
                <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase" title="Actual enlistments achieved">Actual</th>
                <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase" title="Percentage of mission completed">Attainment</th>
                <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase" title="Net gain: enlistments minus losses">Net Gain</th>
                <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase" title="Rank trend: up, down, or stable">Trend</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase" title="Time of most recent enlistment">Last Enlistment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredStandings.map((company, index) => {
                const mission = viewMode === 'ytd' ? company.ytd_mission : company.monthly_mission;
                const actual = viewMode === 'ytd' ? company.ytd_actual : company.monthly_actual;
                const attainment = viewMode === 'ytd' ? company.ytd_attainment : company.monthly_attainment;

                return (
                  <tr 
                    key={company.company_id} 
                    className={`hover:bg-gray-50 transition-colors ${index < 3 ? 'bg-yellow-50' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${getRankBadgeColor(company.rank)}`}>
                          {company.rank <= 3 ? getRankIcon(company.rank) : company.rank}
                        </div>
                        {company.rank !== company.previous_rank && (
                          <span className="text-xs text-gray-500">
                            {company.rank < company.previous_rank ? '↑' : '↓'}
                            {Math.abs(company.rank - company.previous_rank)}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-bold text-gray-900">{company.company_name}</p>
                        <p className="text-xs text-gray-500">{company.battalion} • {company.brigade}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-semibold text-gray-700">{mission}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-bold text-gray-900">{actual}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <span className={`text-lg font-bold ${getAttainmentColor(attainment)}`}>
                          {attainment.toFixed(1)}%
                        </span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all ${
                              attainment >= 100 ? 'bg-green-500' :
                              attainment >= 85 ? 'bg-blue-500' :
                              attainment >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${Math.min(attainment, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex flex-col items-center">
                        <span className={`font-semibold ${company.net_gain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {company.net_gain >= 0 ? '+' : ''}{company.net_gain}
                        </span>
                        <span className="text-xs text-gray-500">
                          {company.future_soldier_losses} losses
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getTrendIcon(company.trend)}
                    </td>
                    <td className="px-4 py-3">
                      {company.last_enlistment ? (
                        <div className="text-xs">
                          <p className="text-gray-700 font-medium">
                            {new Date(company.last_enlistment).toLocaleDateString()}
                          </p>
                          <p className="text-gray-500">
                            {new Date(company.last_enlistment).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">No activity</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer Stats */}
      <div className="bg-gray-50 px-6 py-4 border-t-2 border-gray-200 rounded-b-xl">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-xs text-gray-600">Total Companies</p>
            <p className="text-lg font-bold text-gray-800">{filteredStandings.length}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Avg Attainment</p>
            <p className="text-lg font-bold text-blue-600">
              {filteredStandings.length > 0 
                ? (filteredStandings.reduce((sum, c) => sum + (viewMode === 'ytd' ? c.ytd_attainment : c.monthly_attainment), 0) / filteredStandings.length).toFixed(1)
                : 0}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Total Enlistments</p>
            <p className="text-lg font-bold text-green-600">
              {filteredStandings.reduce((sum, c) => sum + c.total_enlistments, 0)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Total Losses</p>
            <p className="text-lg font-bold text-red-600">
              {filteredStandings.reduce((sum, c) => sum + c.future_soldier_losses, 0)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
