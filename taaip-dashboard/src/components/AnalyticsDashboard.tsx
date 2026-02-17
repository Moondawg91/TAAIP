import React, { useState, useEffect } from 'react';
import { BarChart, Bar, Line, LineChart, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, MapPin, School, Users, Target, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { UniversalFilter, FilterState } from './UniversalFilter';
import { PrintButton } from './PrintButton';
import { ExportButton } from './ExportButton';
import { VisualizationController, DataVisualizer, VisualizationType } from './VisualizationController';
import { API_BASE } from '../config/api';

// Color palette for charts
const COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#8b5cf6',
  teal: '#14b8a6',
  pink: '#ec4899',
};

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#ec4899', '#06b6d4'];

interface CBSAData {
  cbsa_code: string;
  cbsa_name: string;
  lead_count: number;
  avg_score: number;
  high_quality_count: number;
  market_share: number;
  conversion_potential: number;
}

interface SchoolData {
  name: string;
  city: string;
  type: string;
  leads: number;
  conversions: number;
  events: number;
  priority: string;
  conversion_rate: number;
  cost_per_lead: number;
}

interface SegmentData {
  segment_name: string;
  segment_code: string;
  size: number;
  leads_generated: number;
  penetration_rate: number;
  avg_propensity: number;
  conversions: number;
  priority: string;
  remaining_potential: number;
  conversion_rate: number;
}

interface ContractMetrics {
  fiscal_year: number;
  mission_goal: number;
  contracts_achieved: number;
  remaining: number;
  percent_complete: number;
  days_remaining: number;
  daily_rate_needed: number;
  current_daily_rate: number;
  on_track: boolean;
  by_month: Array<{
    month: string;
    goal: number;
    achieved: number;
    variance: number;
  }>;
  by_component: Array<{
    component: string;
    goal: number;
    achieved: number;
    percent: number;
  }>;
}

export const AnalyticsDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<'cbsa' | 'schools' | 'segments' | 'contracts'>('cbsa');
  const [filters, setFilters] = useState<FilterState>({ rsid: '', zipcode: '', cbsa: '' });
  const [visualizationType, setVisualizationType] = useState<VisualizationType>('chart');
  
  // Data state
  const [cbsaData, setCbsaData] = useState<CBSAData[]>([]);
  const [schoolData, setSchoolData] = useState<SchoolData[]>([]);
  const [segmentData, setSegmentData] = useState<SegmentData[]>([]);
  const [contractData, setContractData] = useState<ContractMetrics | null>(null);

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  // Fetch all analytics data
  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.rsid) params.append('rsid', filters.rsid);
      if (filters.zipcode) params.append('zipcode', filters.zipcode);
      if (filters.cbsa) params.append('cbsa', filters.cbsa);
      
      const queryString = params.toString();
      const [cbsaRes, schoolRes, segmentRes, contractRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/analytics/cbsa?limit=10${queryString ? '&' + queryString : ''}`),
        fetch(`${API_BASE}/api/v2/analytics/schools?limit=15${queryString ? '&' + queryString : ''}`),
        fetch(`${API_BASE}/api/v2/analytics/segments${queryString ? '?' + queryString : ''}`),
        fetch(`${API_BASE}/api/v2/analytics/contracts${queryString ? '?' + queryString : ''}`),
      ]);

      const cbsa = await cbsaRes.json();
      const schools = await schoolRes.json();
      const segments = await segmentRes.json();
      const contracts = await contractRes.json();

      if (cbsa.status === 'ok') setCbsaData(cbsa.cbsas);
      if (schools.status === 'ok') setSchoolData(schools.schools);
      if (segments.status === 'ok') setSegmentData(segments.segments);
      if (contracts.status === 'ok') {
        const m = contracts.metrics as ContractMetrics;
        const filtered = {
          ...m,
          by_component: Array.isArray(m.by_component)
            ? m.by_component.filter(c => (c.component || '').toUpperCase() !== 'ARNG' && (c.component || '').toUpperCase() !== 'ARMY NATIONAL GUARD (ARNG)')
            : [],
        } as ContractMetrics;
        setContractData(filtered);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [filters]);

  // Section Navigation
  const NavButton: React.FC<{ section: typeof activeSection; icon: React.ReactNode; label: string }> = ({ section, icon, label }) => (
    <button
      onClick={() => setActiveSection(section)}
      className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${
        activeSection === section
          ? 'bg-blue-600 text-white shadow-lg'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-lg text-gray-600">Loading analytics...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Filters */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Analytics & Insights</h1>
          <p className="text-gray-600 mt-1">Comprehensive recruitment performance visualizations</p>
        </div>
        <div className="flex items-center gap-3">
          <UniversalFilter 
            onFilterChange={handleFilterChange}
            showRSID={true}
            showZipcode={true}
            showCBSA={true}
          />
          <ExportButton 
            data={activeSection === 'cbsa' ? cbsaData : 
                  activeSection === 'schools' ? schoolData : 
                  activeSection === 'segments' ? segmentData : 
                  contractData ? [contractData] : []}
            filename={`analytics-${activeSection}-data`}
          />
          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh Data
          </button>
          {/* Print Button */}
          <PrintButton />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-3 flex-wrap">
        <NavButton section="cbsa" icon={<MapPin className="w-5 h-5" />} label="Top CBSAs" />
        <NavButton section="schools" icon={<School className="w-5 h-5" />} label="Targeted Schools" />
        <NavButton section="segments" icon={<Users className="w-5 h-5" />} label="Segments" />
        <NavButton section="contracts" icon={<Target className="w-5 h-5" />} label="Contract Progress" />
      </div>

      {/* Visualization Controller */}
      <div className="bg-white border-2 border-yellow-500 rounded-lg p-4">
        <VisualizationController
          currentView={visualizationType}
          onViewChange={setVisualizationType}
          availableViews={['chart', 'line', 'table', 'cards', 'pie', 'area']}
        />
      </div>

      {/* Content Sections */}
      {activeSection === 'cbsa' && <CBSASection data={cbsaData} visualizationType={visualizationType} />}
      {activeSection === 'schools' && <SchoolsSection data={schoolData} visualizationType={visualizationType} />}
      {activeSection === 'segments' && <SegmentsSection data={segmentData} visualizationType={visualizationType} />}
      {activeSection === 'contracts' && contractData && <ContractsSection data={contractData} visualizationType={visualizationType} />}
    </div>
  );
};

// CBSA Section
const CBSASection: React.FC<{ data: CBSAData[]; visualizationType: VisualizationType }> = ({ data, visualizationType }) => {
  // Prepare chart data
  const barChartData = data.map(cbsa => ({
    name: cbsa.cbsa_name.split(',')[0], // Short name
    leads: cbsa.lead_count,
    quality: cbsa.high_quality_count,
  }));

  const pieChartData = data.slice(0, 5).map(cbsa => ({
    name: cbsa.cbsa_name.split(',')[0],
    value: cbsa.lead_count,
  }));

  const lineChartData = data.map(cbsa => ({
    name: cbsa.cbsa_name.split(',')[0],
    leads: cbsa.lead_count,
    score: cbsa.avg_score,
  }));

  const areaChartData = data.map(cbsa => ({
    name: cbsa.cbsa_name.split(',')[0],
    potential: cbsa.conversion_potential,
    share: cbsa.market_share,
  }));

  return (
    <div className="space-y-4">
      {/* Summary Cards - Vantage Style */}
      <div className="grid grid-cols-3 gap-px bg-gray-300">
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-xs uppercase tracking-wide">Total CBSAs</p>
              <p className="text-3xl font-bold mt-1 text-yellow-500">{data.length}</p>
            </div>
            <MapPin className="w-10 h-10 text-yellow-500" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6 text-black">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-900 text-xs uppercase tracking-wide">Total Leads</p>
              <p className="text-3xl font-bold mt-1">
                {data.reduce((sum, cbsa) => sum + cbsa.lead_count, 0).toLocaleString()}
              </p>
            </div>
            <TrendingUp className="w-10 h-10" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300 text-xs uppercase tracking-wide">Avg Lead Score</p>
              <p className="text-3xl font-bold mt-1 text-yellow-500">
                {(data.reduce((sum, cbsa) => sum + cbsa.avg_score, 0) / data.length).toFixed(1)}
              </p>
            </div>
            <Target className="w-12 h-12 text-purple-200 opacity-50" />
          </div>
        </div>
      </div>

      {/* Dynamic Visualizations */}
      <DataVisualizer
        data={data}
        visualizationType={visualizationType}
        renderChart={() => (
          <div className="bg-white border-2 border-gray-300 p-6">
            <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
              <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Lead Volume by CBSA (Bar Chart)</h3>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={barChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={12} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="leads" fill={COLORS.primary} name="Total Leads" />
                <Bar dataKey="quality" fill={COLORS.success} name="High Quality" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
        renderLine={() => (
          <div className="bg-white border-2 border-gray-300 p-6">
            <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
              <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">CBSA Performance Trends (Line Graph)</h3>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={lineChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={12} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="leads" stroke={COLORS.primary} strokeWidth={2} name="Leads" />
                <Line yAxisId="right" type="monotone" dataKey="score" stroke={COLORS.success} strokeWidth={2} name="Avg Score" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
        renderPie={() => (
          <div className="bg-white border-2 border-gray-300 p-6">
            <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
              <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Top 5 CBSAs - Market Share (Pie Chart)</h3>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
        renderArea={() => (
          <div className="bg-white border-2 border-gray-300 p-6">
            <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
              <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">CBSA Potential Analysis (Area Chart)</h3>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={areaChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={12} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="potential" stackId="1" stroke={COLORS.purple} fill={COLORS.purple} fillOpacity={0.6} name="Conversion Potential %" />
                <Area type="monotone" dataKey="share" stackId="2" stroke={COLORS.teal} fill={COLORS.teal} fillOpacity={0.6} name="Market Share %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
        renderCards={() => (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.map((cbsa, idx) => (
              <div key={idx} className="bg-white border-2 border-gray-300 rounded-lg p-4 hover:shadow-lg transition-shadow">
                <h4 className="font-bold text-gray-900 mb-2">{cbsa.cbsa_name}</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Leads:</span>
                    <span className="font-semibold text-blue-600">{cbsa.lead_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Score:</span>
                    <span className="font-semibold text-green-600">{cbsa.avg_score.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">High Quality:</span>
                    <span className="font-semibold text-purple-600">{cbsa.high_quality_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Market Share:</span>
                    <span className="font-semibold text-yellow-600">{cbsa.market_share.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        renderTable={() => (
          <div className="bg-white border-2 border-gray-300">
        <div className="bg-gray-100 px-6 py-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">CBSA Performance Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">CBSA</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Leads</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Score</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">High Quality</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Market Share</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Potential</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.map((cbsa, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">{cbsa.cbsa_name}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{cbsa.lead_count.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{cbsa.avg_score.toFixed(1)}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{cbsa.high_quality_count}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{cbsa.market_share.toFixed(1)}%</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{cbsa.conversion_potential.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
        )}
      />
    </div>
  );
};

// Schools Section
const SchoolsSection: React.FC<{ data: SchoolData[]; visualizationType: VisualizationType }> = ({ data, visualizationType }) => {
  const chartData = data.slice(0, 10).map(school => ({
    name: school.name.substring(0, 20) + '...',
    leads: school.leads,
    conversions: school.conversions,
    conversionRate: school.conversion_rate,
  }));

  const priorityColors: Record<string, string> = {
    'Must Win': COLORS.danger,
    'Must Keep': COLORS.success,
    'Opportunity': COLORS.warning,
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-px bg-gray-300">
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
          <div className="flex items-center gap-3">
            <School className="w-10 h-10 text-yellow-500" />
            <div>
              <p className="text-gray-300 text-xs uppercase tracking-wide">Total Schools</p>
              <p className="text-2xl font-bold text-yellow-500">{data.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
          <div className="flex items-center gap-3">
            <Users className="w-10 h-10 text-black" />
            <div>
              <p className="text-gray-800 text-xs uppercase tracking-wide">Total Leads</p>
              <p className="text-2xl font-bold text-black">
                {data.reduce((sum, s) => sum + s.leads, 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-10 h-10 text-yellow-500" />
            <div>
              <p className="text-gray-300 text-xs uppercase tracking-wide">Conversions</p>
              <p className="text-2xl font-bold text-yellow-500">
                {data.reduce((sum, s) => sum + s.conversions, 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-10 h-10 text-black" />
            <div>
              <p className="text-gray-800 text-xs uppercase tracking-wide">Avg Conv. Rate</p>
              <p className="text-2xl font-bold text-black">
                {(data.reduce((sum, s) => sum + s.conversion_rate, 0) / data.length).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6">
        <div className="bg-white border-2 border-gray-300 p-6">
          <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Top Schools - Leads & Conversion Performance</h3>
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <DataVisualizer
              data={chartData}
              visualizationType={visualizationType}
              renderChart={() => (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} fontSize={11} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="leads" fill={COLORS.primary} name="Leads" />
                  <Bar yAxisId="left" dataKey="conversions" fill={COLORS.success} name="Conversions" />
                </BarChart>
              )}
              renderLine={() => (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} fontSize={11} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="leads" stroke={COLORS.primary} name="Leads" />
                  <Line type="monotone" dataKey="conversions" stroke={COLORS.success} name="Conversions" />
                  <Line type="monotone" dataKey="conversionRate" stroke={COLORS.danger} name="Conv. Rate %" />
                </LineChart>
              )}
              renderPie={() => (
                <PieChart>
                  <Tooltip />
                  <Legend />
                  <Pie data={chartData} dataKey="leads" nameKey="name" cx="50%" cy="50%" outerRadius={140} fill={COLORS.primary} label />
                </PieChart>
              )}
              renderArea={() => (
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} fontSize={11} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="leads" stroke={COLORS.primary} fill={COLORS.primary} fillOpacity={0.4} name="Leads" />
                  <Area type="monotone" dataKey="conversions" stroke={COLORS.success} fill={COLORS.success} fillOpacity={0.4} name="Conversions" />
                </AreaChart>
              )}
            />
          </ResponsiveContainer>
        </div>
      </div>

      {/* Schools Table */}
      <div className="bg-white border-2 border-gray-300">
        <div className="bg-gray-100 px-6 py-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Targeted Schools Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">School</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Leads</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Conversions</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Conv. Rate</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Events</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CPL</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.map((school, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{school.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{school.city}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{school.leads}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{school.conversions}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{school.conversion_rate}%</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{school.events}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">${school.cost_per_lead}</td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
                      style={{
                        backgroundColor: priorityColors[school.priority] + '20',
                        color: priorityColors[school.priority],
                      }}
                    >
                      {school.priority}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Segments Section
const SegmentsSection: React.FC<{ data: SegmentData[]; visualizationType: VisualizationType }> = ({ data, visualizationType }) => {
  // Chart data for penetration vs potential
  const scatterData = data.map(seg => ({
    name: seg.segment_name.substring(0, 25),
    penetration: seg.penetration_rate,
    size: seg.size,
    propensity: seg.avg_propensity,
    remaining: seg.remaining_potential,
  }));

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-px bg-gray-300">
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
          <p className="text-gray-300 text-xs uppercase tracking-wide">Total Segments</p>
          <p className="text-3xl font-bold text-yellow-500 mt-1">{data.length}</p>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
          <p className="text-gray-800 text-xs uppercase tracking-wide">Total Market Size</p>
          <p className="text-3xl font-bold text-black mt-1">
            {(data.reduce((sum, s) => sum + s.size, 0) / 1000).toFixed(1)}K
          </p>
        </div>
        
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
          <p className="text-gray-300 text-xs uppercase tracking-wide">Leads Generated</p>
          <p className="text-3xl font-bold text-yellow-500 mt-1">
            {(data.reduce((sum, s) => sum + s.leads_generated, 0) / 1000).toFixed(1)}K
          </p>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
          <p className="text-gray-800 text-xs uppercase tracking-wide">Remaining Potential</p>
          <p className="text-3xl font-bold text-black mt-1">
            {(data.reduce((sum, s) => sum + s.remaining_potential, 0) / 1000).toFixed(1)}K
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border-2 border-gray-300 p-6">
          <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Penetration Rate by Segment</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <DataVisualizer
              data={scatterData}
              visualizationType={visualizationType}
              renderChart={() => (
                <BarChart data={scatterData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" unit="%" />
                  <YAxis dataKey="name" type="category" width={150} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="penetration" fill={COLORS.primary} name="Penetration %" />
                </BarChart>
              )}
              renderLine={() => (
                <LineChart data={scatterData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="penetration" stroke={COLORS.primary} name="Penetration %" />
                </LineChart>
              )}
              renderPie={() => (
                <PieChart>
                  <Tooltip />
                  <Legend />
                  <Pie data={scatterData} dataKey="penetration" nameKey="name" cx="50%" cy="50%" outerRadius={120} fill={COLORS.primary} label />
                </PieChart>
              )}
              renderArea={() => (
                <AreaChart data={scatterData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="penetration" stroke={COLORS.primary} fill={COLORS.primary} fillOpacity={0.4} name="Penetration %" />
                </AreaChart>
              )}
            />
          </ResponsiveContainer>
        </div>

        <div className="bg-white border-2 border-gray-300 p-6">
          <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Average Propensity Score</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <DataVisualizer
              data={scatterData}
              visualizationType={visualizationType}
              renderChart={() => (
                <BarChart data={scatterData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                  <YAxis domain={[0, 10]} />
                  <Tooltip />
                  <Bar dataKey="propensity" fill={COLORS.purple} name="Propensity Score" />
                </BarChart>
              )}
              renderLine={() => (
                <LineChart data={scatterData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                  <YAxis domain={[0, 10]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="propensity" stroke={COLORS.purple} name="Propensity Score" />
                </LineChart>
              )}
              renderPie={() => (
                <PieChart>
                  <Tooltip />
                  <Legend />
                  <Pie data={scatterData} dataKey="propensity" nameKey="name" cx="50%" cy="50%" outerRadius={120} fill={COLORS.purple} label />
                </PieChart>
              )}
              renderArea={() => (
                <AreaChart data={scatterData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                  <YAxis domain={[0, 10]} />
                  <Tooltip />
                  <Area type="monotone" dataKey="propensity" stroke={COLORS.purple} fill={COLORS.purple} fillOpacity={0.4} name="Propensity Score" />
                </AreaChart>
              )}
            />
          </ResponsiveContainer>
        </div>
      </div>

      {/* Remaining Potential Chart */}
      <div className="bg-white border-2 border-gray-300 p-6">
        <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Segment Size vs Leads Generated vs Remaining Potential</h3>
        </div>
        <ResponsiveContainer width="100%" height={350}>
          <DataVisualizer
            data={scatterData}
            visualizationType={visualizationType}
            renderArea={() => (
              <AreaChart data={scatterData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="size" stackId="1" stroke={COLORS.primary} fill={COLORS.primary} fillOpacity={0.6} name="Total Size" />
                <Area type="monotone" dataKey="remaining" stackId="2" stroke={COLORS.warning} fill={COLORS.warning} fillOpacity={0.6} name="Remaining Potential" />
              </AreaChart>
            )}
            renderChart={() => (
              <BarChart data={scatterData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="size" fill={COLORS.primary} name="Total Size" />
                <Bar dataKey="remaining" fill={COLORS.warning} name="Remaining Potential" />
              </BarChart>
            )}
            renderLine={() => (
              <LineChart data={scatterData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} fontSize={11} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="size" stroke={COLORS.primary} name="Total Size" />
                <Line type="monotone" dataKey="remaining" stroke={COLORS.warning} name="Remaining Potential" />
              </LineChart>
            )}
            renderPie={() => (
              <PieChart>
                <Tooltip />
                <Legend />
                <Pie data={scatterData} dataKey="size" nameKey="name" cx="50%" cy="50%" outerRadius={120} fill={COLORS.primary} label />
              </PieChart>
            )}
          />
        </ResponsiveContainer>
      </div>

      {/* Segments Table */}
      <div className="bg-white border-2 border-gray-300">
        <div className="bg-gray-100 px-6 py-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Segment Performance Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Segment</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Size</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Leads Gen.</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Penetration</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Propensity</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Conversions</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Conv. Rate</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Remaining</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.map((seg, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{seg.segment_name}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{seg.size.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{seg.leads_generated.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{seg.penetration_rate.toFixed(1)}%</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{seg.avg_propensity.toFixed(1)}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{seg.conversions.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{seg.conversion_rate}%</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{seg.remaining_potential.toLocaleString()}</td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      seg.priority === 'Must Win' ? 'bg-red-100 text-red-800' :
                      seg.priority === 'Must Keep' ? 'bg-green-100 text-green-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {seg.priority}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Contracts Section
const ContractsSection: React.FC<{ data: ContractMetrics; visualizationType: VisualizationType }> = ({ data, visualizationType }) => {
  // Progress percentage
  const progressPercent = data.percent_complete;
  const isOnTrack = data.on_track;

  // Filter monthly data to show only months with data
  const monthlyData = data.by_month.filter(m => m.achieved > 0);

  return (
    <div className="space-y-6">
      {/* Mission Progress Card */}
      <div className="bg-gradient-to-r from-gray-700 to-gray-800 border-2 border-gray-300 p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold text-yellow-500">FY {data.fiscal_year} Mission Progress</h2>
            <p className="text-gray-300 mt-1 text-xs uppercase tracking-wide">Contract Achievement Tracking</p>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 ${
            isOnTrack ? 'bg-green-600' : 'bg-red-600'
          }`}>
            {isOnTrack ? <CheckCircle className="w-5 h-5 text-white" /> : <AlertCircle className="w-5 h-5 text-white" />}
            <span className="font-semibold text-white uppercase tracking-wide text-sm">{isOnTrack ? 'On Track' : 'At Risk'}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm mb-2 text-gray-300">
            <span className="uppercase tracking-wide">Progress</span>
            <span className="font-bold text-yellow-500">{progressPercent.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-900 h-6">
            <div
              className="h-full bg-gradient-to-r from-yellow-600 to-yellow-700 flex items-center justify-center text-xs font-bold text-black uppercase tracking-wide"
              style={{ width: `${progressPercent}%` }}
            >
              {progressPercent > 10 && `${progressPercent.toFixed(1)}%`}
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-4 gap-px bg-gray-300">
          <div className="bg-gray-800 p-4">
            <p className="text-gray-300 text-xs uppercase tracking-wide">Mission Goal</p>
            <p className="text-2xl font-bold text-yellow-500">{data.mission_goal.toLocaleString()}</p>
          </div>
          <div className="bg-gray-800 p-4">
            <p className="text-gray-300 text-xs uppercase tracking-wide">Achieved</p>
            <p className="text-2xl font-bold text-green-400">{data.contracts_achieved.toLocaleString()}</p>
          </div>
          <div className="bg-gray-800 p-4">
            <p className="text-gray-300 text-xs uppercase tracking-wide">Remaining</p>
            <p className="text-2xl font-bold text-yellow-400">{data.remaining.toLocaleString()}</p>
          </div>
          <div className="bg-gray-800 p-4">
            <p className="text-gray-300 text-xs uppercase tracking-wide">Days Left</p>
            <p className="text-2xl font-bold text-yellow-500">{data.days_remaining}</p>
          </div>
        </div>

        {/* Daily Rate Info */}
        <div className="mt-6 grid grid-cols-2 gap-px bg-gray-300">
          <div className="bg-gray-800 p-4">
            <p className="text-gray-300 text-xs uppercase tracking-wide">Current Daily Rate</p>
            <p className="text-xl font-bold text-yellow-500">{data.current_daily_rate.toFixed(1)} contracts/day</p>
          </div>
          <div className="bg-gray-800 p-4">
            <p className="text-gray-300 text-xs uppercase tracking-wide">Required Daily Rate</p>
            <p className="text-xl font-bold text-yellow-500">{data.daily_rate_needed.toFixed(1)} contracts/day</p>
          </div>
        </div>
      </div>

      {/* Monthly Performance Chart */}
      <div className="bg-white border-2 border-gray-300 p-6">
        <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300 flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Monthly Contract Achievement</h3>
          <span className="text-xs text-gray-500 ml-2">Visualization selector only affects the chart below</span>
        </div>
        <ResponsiveContainer width="100%" height={350}>
          <DataVisualizer
            data={monthlyData}
            visualizationType={visualizationType}
            renderArea={() => (
              <AreaChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="goal" stroke={COLORS.warning} fill={COLORS.warning} fillOpacity={0.3} name="Goal" />
                <Area type="monotone" dataKey="achieved" stroke={COLORS.success} fill={COLORS.success} fillOpacity={0.6} name="Achieved" />
              </AreaChart>
            )}
            renderChart={() => (
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="goal" fill={COLORS.warning} name="Goal" />
                <Bar dataKey="achieved" fill={COLORS.success} name="Achieved" />
              </BarChart>
            )}
            renderLine={() => (
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="goal" stroke={COLORS.warning} name="Goal" />
                <Line type="monotone" dataKey="achieved" stroke={COLORS.success} name="Achieved" />
              </LineChart>
            )}
            renderPie={() => (
              <PieChart>
                <Tooltip />
                <Legend />
                <Pie data={monthlyData} dataKey="achieved" nameKey="month" cx="50%" cy="50%" outerRadius={130} fill={COLORS.success} label />
              </PieChart>
            )}
          />
        </ResponsiveContainer>
      </div>

      {/* Component Breakdown */}
      <div className="bg-white border-2 border-gray-300 p-6">
        <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Achievement by Component</h3>
        </div>
        <div className="space-y-4">
          {data.by_component.map((comp, idx) => (
            <div key={idx}>
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium text-gray-700">{comp.component}</span>
                <span className="text-gray-600">
                  {comp.achieved.toLocaleString()} / {comp.goal.toLocaleString()} ({comp.percent.toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-300 h-4">
                <div
                  className={`h-full ${
                    comp.percent >= 80 ? 'bg-green-600' : comp.percent >= 60 ? 'bg-yellow-600' : 'bg-red-600'
                  }`}
                  style={{ width: `${comp.percent}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Monthly Variance Table */}
      <div className="bg-white border-2 border-gray-300">
        <div className="bg-gray-100 px-6 py-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Monthly Performance Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Month</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Goal</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Achieved</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Variance</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.by_month.map((month, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{month.month}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">{month.goal.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">
                    {month.achieved > 0 ? month.achieved.toLocaleString() : '-'}
                  </td>
                  <td className={`px-6 py-4 text-sm text-right font-semibold ${
                    month.variance > 0 ? 'text-green-600' : month.variance < 0 ? 'text-red-600' : 'text-gray-900'
                  }`}>
                    {month.achieved > 0 ? (month.variance > 0 ? '+' : '') + month.variance.toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {month.achieved === 0 ? (
                      <span className="text-gray-400">Pending</span>
                    ) : (
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        month.variance >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {month.variance >= 0 ? 'Met Goal' : 'Below Goal'}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
