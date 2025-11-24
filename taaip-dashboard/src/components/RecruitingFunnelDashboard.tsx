import React, { useState, useEffect } from 'react';
import { 
  TrendingDown, TrendingUp, Users, UserCheck, FileText, ClipboardCheck, 
  Ship, XCircle, AlertTriangle, Clock, Target, BarChart3, Activity, CheckCircle2, Eye
} from 'lucide-react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, FunnelChart, Funnel,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { UniversalFilter, FilterState } from './UniversalFilter';
import { DynamicDashboard } from './DynamicDashboard';
import { ExportButton } from './ExportButton';
import { API_BASE } from '../config/api';

// Army Recruiting Funnel stage colors
const STAGE_COLORS = {
  lead: '#3b82f6',           // Blue
  prospect: '#8b5cf6',        // Purple
  appointment_made: '#ec4899', // Pink
  appointment_conducted: '#f59e0b', // Amber
  test: '#f97316',            // Orange
  test_pass: '#84cc16',       // Lime
  enlistment: '#10b981',      // Green
  ship: '#059669',            // Emerald
  loss: '#ef4444',            // Red
};

const STAGE_ICONS = {
  lead: <Users className="w-5 h-5" />,
  prospect: <UserCheck className="w-5 h-5" />,
  appointment_made: <FileText className="w-5 h-5" />,
  appointment_conducted: <ClipboardCheck className="w-5 h-5" />,
  test: <Activity className="w-5 h-5" />,
  test_pass: <Target className="w-5 h-5" />,
  enlistment: <CheckCircle2 className="w-5 h-5" />,
  ship: <Ship className="w-5 h-5" />,
  loss: <XCircle className="w-5 h-5" />,
};

const STAGE_LABELS = {
  lead: 'Lead',
  prospect: 'Prospect',
  appointment_made: 'Appointment Made',
  appointment_conducted: 'Appointment Conducted',
  test: 'Test Scheduled',
  test_pass: 'Test Pass',
  enlistment: 'Enlistment',
  ship: 'Ship',
  loss: 'Loss',
};

interface FunnelMetrics {
  funnel_counts: {
    leads: number;
    prospects: number;
    appointments_made: number;
    appointments_conducted: number;
    tests: number;
    test_passes: number;
    enlistments: number;
    ships: number;
    losses: number;
    total_active: number;
    total_leads: number;
  };
  conversion_rates: {
    lead_to_prospect: number;
    prospect_to_appointment: number;
    appointment_made_to_conducted: number;
    appointment_to_test: number;
    test_to_pass: number;
    test_pass_to_enlistment: number;
    enlistment_to_ship: number;
    overall_conversion: number;
  };
  flash_to_bang: {
    avg_lead_to_prospect_days: number;
    avg_prospect_to_appointment_days: number;
    avg_appointment_to_test_days: number;
    avg_test_to_enlistment_days: number;
    avg_lead_to_enlistment_days: number;
    avg_enlistment_to_ship_days: number;
    avg_dep_length_days: number;
  };
  appointment_metrics: {
    no_show_rate: number;
  };
  loss_analysis: {
    total_losses: number;
    loss_rate: number;
    top_loss_reason: string;
  };
}

export const RecruitingFunnelDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<FunnelMetrics | null>(null);
  const [selectedFY, setSelectedFY] = useState<number>(2025);
  const [filters, setFilters] = useState<FilterState>({ rsid: '', zipcode: '', cbsa: '' });

  useEffect(() => {
    fetchFunnelMetrics();
  }, [selectedFY, filters]);

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  const fetchFunnelMetrics = async () => {
    try {
      const params = new URLSearchParams({ fiscal_year: selectedFY.toString() });
      if (filters.rsid) params.append('rsid', filters.rsid);
      if (filters.zipcode) params.append('zipcode', filters.zipcode);
      if (filters.cbsa) params.append('cbsa', filters.cbsa);
      
      const res = await fetch(`${API_BASE}/api/v2/recruiting-funnel/metrics?${params.toString()}`);
      const data = await res.json();
      if (data.status === 'ok') {
        setMetrics(data.metrics);
      }
    } catch (error) {
      console.error('Error fetching funnel metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !metrics) {
    return <div className="p-8 text-center">Loading recruiting funnel data...</div>;
  }

  // Prepare funnel visualization data - Army recruiting process
  const funnelData = [
    { stage: 'Leads', value: metrics.funnel_counts.leads, fill: STAGE_COLORS.lead },
    { stage: 'Prospects', value: metrics.funnel_counts.prospects, fill: STAGE_COLORS.prospect },
    { stage: 'Appt Made', value: metrics.funnel_counts.appointments_made, fill: STAGE_COLORS.appointment_made },
    { stage: 'Appt Done', value: metrics.funnel_counts.appointments_conducted, fill: STAGE_COLORS.appointment_conducted },
    { stage: 'Test', value: metrics.funnel_counts.tests, fill: STAGE_COLORS.test },
    { stage: 'Test Pass', value: metrics.funnel_counts.test_passes, fill: STAGE_COLORS.test_pass },
    { stage: 'Enlistment', value: metrics.funnel_counts.enlistments, fill: STAGE_COLORS.enlistment },
    { stage: 'Ship', value: metrics.funnel_counts.ships, fill: STAGE_COLORS.ship },
  ];

  // Conversion rates data - Army recruiting process stages
  const conversionData = [
    { stage: 'Lead→Prospect', rate: metrics.conversion_rates.lead_to_prospect },
    { stage: 'Prospect→Appt', rate: metrics.conversion_rates.prospect_to_appointment },
    { stage: 'Appt Made→Done', rate: metrics.conversion_rates.appointment_made_to_conducted },
    { stage: 'Appt→Test', rate: metrics.conversion_rates.appointment_to_test },
    { stage: 'Test→Pass', rate: metrics.conversion_rates.test_to_pass },
    { stage: 'Test Pass→Enlist', rate: metrics.conversion_rates.test_pass_to_enlistment },
    { stage: 'Enlist→Ship', rate: metrics.conversion_rates.enlistment_to_ship },
  ];

  // Identify bottlenecks (conversion rates below 50%)
  const bottlenecks = conversionData.filter(d => d.rate < 50);

  return (
    <div className="space-y-4">
      {/* Header with Filters - Vantage Style */}
      <div className="bg-white border-2 border-gray-300 shadow-sm">
        <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white px-6 py-3 border-b-2 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold uppercase tracking-wider flex items-center gap-3">
                <Activity className="w-6 h-6 text-yellow-500" />
                Recruiting Funnel & Conversion Tracking
              </h1>
              <p className="text-gray-300 text-xs mt-1 uppercase tracking-wide">
                Flash-to-Bang Metrics • Bottleneck Analysis • Contract Pipeline
              </p>
            </div>
            <div className="flex items-center gap-3">
              <UniversalFilter 
                onFilterChange={handleFilterChange}
                showRSID={true}
                showZipcode={true}
                showCBSA={true}
              />
              <ExportButton 
                data={metrics ? [metrics] : []}
                filename="recruiting-funnel-data"
              />
              <select
                value={selectedFY}
                onChange={(e) => setSelectedFY(parseInt(e.target.value))}
                className="px-3 py-2 bg-gray-700 text-white border border-yellow-600 text-sm font-bold"
              >
                <option value={2024}>FY2024</option>
                <option value={2025}>FY2025</option>
                <option value={2026}>FY2026</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Cards - Vantage Style */}
      <div className="grid grid-cols-4 gap-px bg-gray-300">
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <Users className="w-8 h-8 text-yellow-500" />
            <span className="text-3xl font-bold text-yellow-500">{metrics.funnel_counts.total_leads.toLocaleString()}</span>
          </div>
          <p className="text-gray-300 text-sm uppercase tracking-wide">Total Leads</p>
        </div>

        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6 text-black">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-8 h-8" />
            <span className="text-3xl font-bold">{metrics.funnel_counts.enlistments.toLocaleString()}</span>
          </div>
          <p className="text-gray-900 text-sm uppercase tracking-wide">Enlistments</p>
        </div>

        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-8 h-8 text-yellow-500" />
            <span className="text-3xl font-bold text-yellow-500">{metrics.conversion_rates.overall_conversion.toFixed(1)}%</span>
          </div>
          <p className="text-gray-300 text-sm uppercase tracking-wide">Overall Conversion</p>
        </div>

        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6 text-black">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8" />
            <span className="text-3xl font-bold">{Math.round(metrics.flash_to_bang.avg_lead_to_enlistment_days)}</span>
          </div>
          <p className="text-gray-900 text-sm uppercase tracking-wide">Avg Days to Enlistment</p>
        </div>
      </div>

      {/* Bottleneck Alerts */}
      {bottlenecks.length > 0 && (
        <div className="bg-white border-2 border-red-600 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-bold text-red-900 uppercase tracking-wide">Bottlenecks Detected</h3>
              <p className="text-sm text-gray-700 mt-1">
                The following stages have conversion rates below 50%:
              </p>
              <ul className="mt-2 space-y-1">
                {bottlenecks.map((b, idx) => (
                  <li key={idx} className="text-sm text-gray-800 font-medium">
                    • <strong>{b.stage}</strong>: {b.rate.toFixed(1)}% conversion
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Main Funnel Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Funnel Chart */}
        <div className="bg-white border-2 border-gray-300 shadow-sm">
          <div className="bg-gray-100 px-4 py-2 border-b-2 border-gray-300">
            <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Recruiting Funnel</h2>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={funnelData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="stage" />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {funnelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Conversion Rates */}
        <div className="bg-white border-2 border-gray-300 shadow-sm">
          <div className="bg-gray-100 px-4 py-2 border-b-2 border-gray-300">
            <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Conversion Rates by Stage</h2>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={conversionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" angle={-45} textAnchor="end" height={80} />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                <Bar dataKey="rate" fill="#3b82f6" radius={[8, 8, 0, 0]}>
                  {conversionData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.rate < 50 ? '#ef4444' : entry.rate < 70 ? '#f59e0b' : '#10b981'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Flash-to-Bang Metrics */}
      <div className="grid grid-cols-3 gap-px bg-gray-300">
        <div className="bg-white p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gray-800 flex items-center justify-center">
              <Clock className="w-5 h-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{Math.round(metrics.flash_to_bang.avg_lead_to_enlistment_days)}</p>
              <p className="text-xs text-gray-600 uppercase tracking-wide">Days: Lead → Enlistment</p>
            </div>
          </div>
          <div className="h-2 bg-gray-200 overflow-hidden">
            <div 
              className="h-full bg-yellow-600 transition-all" 
              style={{ width: `${Math.min(100, (metrics.flash_to_bang.avg_lead_to_enlistment_days / 180) * 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2 font-medium">Target: &lt;120 days</p>
        </div>

        <div className="bg-white p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gray-800 flex items-center justify-center">
              <Ship className="w-5 h-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{Math.round(metrics.flash_to_bang.avg_enlistment_to_ship_days)}</p>
              <p className="text-xs text-gray-600 uppercase tracking-wide">Days: Enlistment → Ship</p>
            </div>
          </div>
          <div className="h-2 bg-gray-200 overflow-hidden">
            <div 
              className="h-full bg-yellow-600 transition-all" 
              style={{ width: `${Math.min(100, (metrics.flash_to_bang.avg_enlistment_to_ship_days / 240) * 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2 font-medium">Target: &lt;180 days</p>
        </div>

        <div className="bg-white p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gray-800 flex items-center justify-center">
              <Target className="w-5 h-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{Math.round(metrics.conversion_rates.test_to_pass)}%</p>
              <p className="text-xs text-gray-600 uppercase tracking-wide">Test Pass Rate</p>
            </div>
          </div>
          <div className="h-2 bg-gray-200 overflow-hidden">
            <div 
              className="h-full bg-yellow-600 transition-all" 
              style={{ width: `${metrics.conversion_rates.test_to_pass}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2 font-medium">Target: &gt;80%</p>
        </div>
      </div>

      {/* Loss Analysis */}
      <div className="bg-white border-2 border-gray-300 shadow-sm">
        <div className="bg-gray-100 px-4 py-2 border-b-2 border-gray-300">
          <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Loss Analysis</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-gray-600 text-sm font-medium uppercase">Total Losses</span>
                <span className="text-2xl font-bold text-red-600">{metrics.loss_analysis.total_losses.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-gray-600 text-sm font-medium uppercase">Loss Rate</span>
                <span className="text-2xl font-bold text-red-600">{metrics.loss_analysis.loss_rate.toFixed(1)}%</span>
              </div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-gray-600 text-sm font-medium uppercase">Appointment No-Show Rate</span>
                <span className="text-2xl font-bold text-orange-600">{metrics.appointment_metrics.no_show_rate.toFixed(1)}%</span>
              </div>
              <div className="mt-4 p-4 bg-gray-100 border-l-4 border-red-600">
                <p className="text-xs text-gray-700 font-bold uppercase tracking-wide">Top Loss Reason:</p>
                <p className="text-base font-bold text-gray-900 mt-1">{metrics.loss_analysis.top_loss_reason || 'N/A'}</p>
              </div>
            </div>
            <div>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Enlisted', value: metrics.funnel_counts.enlistments, fill: '#10b981' },
                    { name: 'Lost', value: metrics.loss_analysis.total_losses, fill: '#ef4444' },
                    { name: 'In Progress', value: metrics.funnel_counts.total_active, fill: '#6b7280' },
                  ]}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        </div>
      </div>

      {/* Smart Visuals - Auto Generated */}
      <div className="bg-white border-2 border-gray-300 rounded-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b-2 border-gray-300 bg-gray-100">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <Eye className="w-4 h-4 text-blue-600" /> Smart Visuals (Funnel Data)
          </h3>
          <span className="text-xs text-gray-500">Source /api/v2/recruiting-funnel/metrics</span>
        </div>
        <DynamicDashboard dataType="leads" />
      </div>
    </div>
  );
};
