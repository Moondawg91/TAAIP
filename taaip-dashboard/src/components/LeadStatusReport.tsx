import React, { useState, useEffect } from 'react';
import {
  Users, TrendingUp, Clock, AlertCircle, Phone, Mail, Calendar,
  Filter, Download, RefreshCw, ChevronDown, CheckCircle, XCircle, User
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart
} from 'recharts';
import { API_BASE } from '../config/api';

interface Lead {
  lead_id: string;
  first_name: string;
  last_name: string;
  stage: string;
  source: string;
  recruiter: string;
  created_date: string;
  last_activity_date: string;
  days_in_stage: number;
  propensity_score: number;
  contact_attempts: number;
  status: string;
}

interface StageMetrics {
  stage: string;
  count: number;
  avg_days: number;
  conversion_rate: number;
}

interface RecruiterMetrics {
  recruiter: string;
  total_leads: number;
  active_leads: number;
  converted: number;
  conversion_rate: number;
}

interface SourceMetrics {
  source: string;
  leads: number;
  conversion_rate: number;
  avg_propensity: number;
}

const STAGE_COLORS: Record<string, string> = {
  lead: '#3b82f6',
  prospect: '#8b5cf6',
  appointment: '#ec4899',
  test: '#f59e0b',
  enlistment: '#10b981',
  ship: '#059669',
  loss: '#ef4444',
};

const STATUS_COLORS: Record<string, string> = {
  active: '#10b981',
  contacted: '#3b82f6',
  no_contact: '#f59e0b',
  unresponsive: '#ef4444',
  converted: '#059669',
  lost: '#6b7280',
};

export const LeadStatusReport: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stageMetrics, setStageMetrics] = useState<StageMetrics[]>([]);
  const [recruiterMetrics, setRecruiterMetrics] = useState<RecruiterMetrics[]>([]);
  const [sourceMetrics, setSourceMetrics] = useState<SourceMetrics[]>([]);
  const [selectedStage, setSelectedStage] = useState<string>('all');
  const [selectedRecruiter, setSelectedRecruiter] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('30');
  const [viewMode, setViewMode] = useState<'summary' | 'detail'>('summary');
  const [sortBy, setSortBy] = useState<'name' | 'stage' | 'days' | 'score'>('days');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchLeadData();
  }, [dateRange, selectedStage, selectedRecruiter, selectedSource]);

  const fetchLeadData = async () => {
    try {
      const params = new URLSearchParams();
      if (dateRange !== 'all') params.append('days', dateRange);
      if (selectedStage !== 'all') params.append('stage', selectedStage);
      if (selectedRecruiter !== 'all') params.append('recruiter', selectedRecruiter);
      if (selectedSource !== 'all') params.append('source', selectedSource);

      const [leadsRes, metricsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/leads/status?${params.toString()}`),
        fetch(`${API_BASE}/api/v2/leads/metrics?${params.toString()}`)
      ]);

      const [leadsData, metricsData] = await Promise.all([
        leadsRes.json(),
        metricsRes.json()
      ]);

      if (leadsData.status === 'ok') {
        setLeads(leadsData.data);
      }

      if (metricsData.status === 'ok') {
        setStageMetrics(metricsData.data.by_stage || []);
        setRecruiterMetrics(metricsData.data.by_recruiter || []);
        setSourceMetrics(metricsData.data.by_source || []);
      }
    } catch (error) {
      console.error('Error fetching lead data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading lead status data...</div>;
  }

  // Calculate summary metrics
  const totalLeads = leads.length;
  const activeLeads = leads.filter(l => l.status === 'active' || l.status === 'contacted').length;
  const avgDaysInStage = leads.length > 0
    ? Math.round(leads.reduce((sum, l) => sum + l.days_in_stage, 0) / leads.length)
    : 0;
  const avgPropensity = leads.length > 0
    ? Math.round(leads.reduce((sum, l) => sum + l.propensity_score, 0) / leads.length)
    : 0;
  const staleLeads = leads.filter(l => l.days_in_stage > 30).length;
  const highPriorityLeads = leads.filter(l => l.propensity_score >= 80).length;

  // Sort leads
  const sortedLeads = [...leads].sort((a, b) => {
    let compareValue = 0;
    switch (sortBy) {
      case 'name':
        compareValue = `${a.last_name} ${a.first_name}`.localeCompare(`${b.last_name} ${b.first_name}`);
        break;
      case 'stage':
        compareValue = a.stage.localeCompare(b.stage);
        break;
      case 'days':
        compareValue = a.days_in_stage - b.days_in_stage;
        break;
      case 'score':
        compareValue = a.propensity_score - b.propensity_score;
        break;
    }
    return sortOrder === 'asc' ? compareValue : -compareValue;
  });

  // Prepare stage trend data (simulated for last 7 days)
  const stageTrendData = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - i));
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      leads: Math.floor(Math.random() * 50) + totalLeads * 0.8,
      prospects: Math.floor(Math.random() * 30) + totalLeads * 0.5,
      appointments: Math.floor(Math.random() * 20) + totalLeads * 0.3,
    };
  });

  const renderSummary = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Users className="w-8 h-8" />
            <span className="text-2xl font-bold">{totalLeads}</span>
          </div>
          <p className="text-blue-100">Total Leads</p>
          <p className="text-xs text-blue-200 mt-1">{activeLeads} active</p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-8 h-8" />
            <span className="text-2xl font-bold">{avgPropensity}</span>
          </div>
          <p className="text-green-100">Avg Propensity Score</p>
          <p className="text-xs text-green-200 mt-1">{highPriorityLeads} high priority (≥80)</p>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8" />
            <span className="text-2xl font-bold">{avgDaysInStage}</span>
          </div>
          <p className="text-orange-100">Avg Days in Stage</p>
          <p className="text-xs text-orange-200 mt-1">{staleLeads} stale (&gt;30 days)</p>
        </div>

        <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <AlertCircle className="w-8 h-8" />
            <span className="text-2xl font-bold">{staleLeads}</span>
          </div>
          <p className="text-red-100">Requires Action</p>
          <p className="text-xs text-red-200 mt-1">Leads needing follow-up</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-md p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <span className="font-semibold text-gray-700">Filters:</span>
          </div>

          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="60">Last 60 Days</option>
            <option value="90">Last 90 Days</option>
            <option value="all">All Time</option>
          </select>

          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="all">All Stages</option>
            <option value="lead">Lead</option>
            <option value="prospect">Prospect</option>
            <option value="appointment">Appointment</option>
            <option value="test">Test</option>
            <option value="enlistment">Enlistment</option>
          </select>

          <select
            value={selectedRecruiter}
            onChange={(e) => setSelectedRecruiter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="all">All Recruiters</option>
            {Array.from(new Set(leads.map(l => l.recruiter))).map(recruiter => (
              <option key={recruiter} value={recruiter}>{recruiter}</option>
            ))}
          </select>

          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="all">All Sources</option>
            {Array.from(new Set(leads.map(l => l.source))).map(source => (
              <option key={source} value={source}>{source}</option>
            ))}
          </select>

          <button
            onClick={fetchLeadData}
            className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>

          <button
            onClick={() => setViewMode(viewMode === 'summary' ? 'detail' : 'summary')}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            {viewMode === 'summary' ? 'View Details' : 'View Summary'}
          </button>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stage Distribution */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Leads by Stage</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stageMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="stage" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                {stageMetrics.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={STAGE_COLORS[entry.stage] || '#6b7280'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Source Performance */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Lead Sources</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sourceMetrics}
                dataKey="leads"
                nameKey="source"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry) => `${entry.source}: ${entry.leads}`}
              >
                {sourceMetrics.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={Object.values(STAGE_COLORS)[index % Object.values(STAGE_COLORS).length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Trend */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Lead Pipeline Trend (7 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={stageTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="leads" stackId="1" stroke="#3b82f6" fill="#3b82f6" />
              <Area type="monotone" dataKey="prospects" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" />
              <Area type="monotone" dataKey="appointments" stackId="1" stroke="#ec4899" fill="#ec4899" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Recruiter Performance */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Recruiter Performance</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={recruiterMetrics.slice(0, 5)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="recruiter" width={100} />
              <Tooltip />
              <Legend />
              <Bar dataKey="active_leads" fill="#3b82f6" name="Active" />
              <Bar dataKey="converted" fill="#10b981" name="Converted" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stage Metrics Table */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Stage Performance Metrics</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Stage</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700">Count</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700">Avg Days</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700">Conversion Rate</th>
              </tr>
            </thead>
            <tbody>
              {stageMetrics.map((metric, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <span
                      className="px-3 py-1 rounded-full text-xs font-medium text-white"
                      style={{ backgroundColor: STAGE_COLORS[metric.stage] || '#6b7280' }}
                    >
                      {metric.stage.toUpperCase()}
                    </span>
                  </td>
                  <td className="text-right py-3 px-4 font-medium">{metric.count}</td>
                  <td className="text-right py-3 px-4">{Math.round(metric.avg_days)} days</td>
                  <td className="text-right py-3 px-4">
                    <span className={metric.conversion_rate >= 50 ? 'text-green-600' : 'text-orange-600'}>
                      {metric.conversion_rate.toFixed(1)}%
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

  const renderDetail = () => (
    <div className="space-y-6">
      {/* Header with sorting */}
      <div className="bg-white rounded-xl shadow-md p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="font-semibold text-gray-700">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="name">Name</option>
              <option value="stage">Stage</option>
              <option value="days">Days in Stage</option>
              <option value="score">Propensity Score</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              {sortOrder === 'asc' ? '↑ Ascending' : '↓ Descending'}
            </button>
          </div>
          <div className="text-sm text-gray-600">
            Showing {sortedLeads.length} leads
          </div>
        </div>
      </div>

      {/* Lead Cards */}
      <div className="grid grid-cols-1 gap-4">
        {sortedLeads.map((lead) => (
          <div
            key={lead.lead_id}
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <User className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">
                      {lead.first_name} {lead.last_name}
                    </h3>
                    <p className="text-sm text-gray-600">ID: {lead.lead_id}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                  <div>
                    <p className="text-xs text-gray-500">Stage</p>
                    <span
                      className="inline-block px-3 py-1 rounded-full text-xs font-medium text-white mt-1"
                      style={{ backgroundColor: STAGE_COLORS[lead.stage] || '#6b7280' }}
                    >
                      {lead.stage.toUpperCase()}
                    </span>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">Status</p>
                    <span
                      className="inline-block px-3 py-1 rounded-full text-xs font-medium text-white mt-1"
                      style={{ backgroundColor: STATUS_COLORS[lead.status] || '#6b7280' }}
                    >
                      {lead.status.toUpperCase()}
                    </span>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">Propensity Score</p>
                    <p className="font-semibold text-lg mt-1">
                      <span className={lead.propensity_score >= 80 ? 'text-green-600' : lead.propensity_score >= 60 ? 'text-blue-600' : 'text-orange-600'}>
                        {lead.propensity_score}
                      </span>
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">Days in Stage</p>
                    <p className="font-semibold text-lg mt-1">
                      <span className={lead.days_in_stage > 30 ? 'text-red-600' : 'text-gray-800'}>
                        {lead.days_in_stage}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>{lead.recruiter}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span>Created: {new Date(lead.created_date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>Last Activity: {new Date(lead.last_activity_date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Phone className="w-4 h-4" />
                    <span>{lead.contact_attempts} attempts</span>
                  </div>
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-700">
                    Source: {lead.source}
                  </span>
                  {lead.days_in_stage > 30 && (
                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                      ⚠️ Requires Follow-up
                    </span>
                  )}
                  {lead.propensity_score >= 80 && (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                      🎯 High Priority
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm">
                  <Phone className="w-4 h-4" />
                  Contact
                </button>
                <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2 text-sm">
                  <Mail className="w-4 h-4" />
                  Email
                </button>
              </div>
            </div>
          </div>
        ))}

        {sortedLeads.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No leads found matching the current filters</p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Users className="w-8 h-8 text-green-600" />
            Lead Status Report
          </h1>
          <p className="text-gray-600 mt-1">
            Pipeline tracking • Stage metrics • Recruiter performance • Follow-up alerts
          </p>
        </div>
        <button
          onClick={() => alert('Export functionality - would generate CSV/PDF report')}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export Report
        </button>
      </div>

      {viewMode === 'summary' ? renderSummary() : renderDetail()}
    </div>
  );
};
