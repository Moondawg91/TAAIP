import React, { useState, useEffect } from 'react';
import {
  MapPin, TrendingUp, TrendingDown, Users, Award, Target,
  BarChart3, Activity, AlertTriangle, CheckCircle2, Minus
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

const API_BASE = 'http://localhost:8000';

interface G2Zone {
  zone_id: string;
  zone_name: string;
  geographic_area: string;
  population: number;
  military_age_population: number;
  current_quarter: string;
  lead_count: number;
  qualified_leads: number;
  conversion_count: number;
  enlistment_count: number;
  qualification_rate: number;
  conversion_rate: number;
  enlistment_rate: number;
  avg_lead_quality_score: number;
  avg_days_to_conversion: number;
  top_lead_source: string;
  top_mos: string;
  market_penetration_rate: number;
  competitive_index: number;
  trend_direction: 'up' | 'down' | 'stable';
  rsid: string;
  brigade: string;
}

interface ZoneSummary {
  total_zones: number;
  total_leads: number;
  total_qualified: number;
  total_enlistments: number;
  avg_qualification_rate: number;
  avg_conversion_rate: number;
  avg_penetration: number;
  zones_trending_up: number;
  zones_trending_down: number;
}

const TREND_CONFIG = {
  up: { color: '#10b981', icon: <TrendingUp className="w-5 h-5" />, label: 'Trending Up' },
  down: { color: '#ef4444', icon: <TrendingDown className="w-5 h-5" />, label: 'Trending Down' },
  stable: { color: '#6b7280', icon: <Minus className="w-5 h-5" />, label: 'Stable' }
};

export const G2ZonePerformanceDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [zones, setZones] = useState<G2Zone[]>([]);
  const [summary, setSummary] = useState<ZoneSummary | null>(null);
  const [selectedZone, setSelectedZone] = useState<G2Zone | null>(null);
  const [trendFilter, setTrendFilter] = useState<string>('');

  useEffect(() => {
    Promise.all([fetchZones(), fetchSummary()]).finally(() => setLoading(false));
  }, [trendFilter]);

  const fetchZones = async () => {
    try {
      const params = new URLSearchParams();
      if (trendFilter) params.append('trend', trendFilter);
      
      const res = await fetch(`${API_BASE}/api/v2/g2-zones?${params}`);
      const data = await res.json();
      
      if (data.status === 'ok') {
        setZones(data.data);
      }
    } catch (error) {
      console.error('Error fetching G2 zones:', error);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/g2-zones/summary`);
      const data = await res.json();
      
      if (data.status === 'ok') {
        setSummary(data.summary);
      }
    } catch (error) {
      console.error('Error fetching zone summary:', error);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading G2 Zone performance data...</div>;
  }

  // Prepare chart data
  const topZonesData = zones.slice(0, 10).map(z => ({
    name: z.zone_name,
    leads: z.lead_count,
    qualified: z.qualified_leads,
    enlistments: z.enlistment_count,
    conversion_rate: z.conversion_rate * 100
  }));

  // Market penetration comparison
  const penetrationData = zones.map(z => ({
    zone: z.zone_name.substring(0, 15),
    penetration: z.market_penetration_rate * 100,
    competitive: z.competitive_index * 100
  }));

  // Performance radar for selected zone
  const getRadarData = (zone: G2Zone) => [
    { metric: 'Lead Volume', value: Math.min(100, (zone.lead_count / 500) * 100) },
    { metric: 'Qualification Rate', value: zone.qualification_rate * 100 },
    { metric: 'Conversion Rate', value: zone.conversion_rate * 100 },
    { metric: 'Enlistment Rate', value: zone.enlistment_rate * 100 },
    { metric: 'Market Penetration', value: zone.market_penetration_rate * 100 },
    { metric: 'Lead Quality', value: zone.avg_lead_quality_score }
  ];

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <MapPin className="w-8 h-8 text-blue-600" />
            G2 Zone Lead Performance
          </h1>
          <p className="text-gray-600 mt-1">
            Geographic Zone Analysis • Market Intelligence • Competitive Positioning
          </p>
        </div>
        <select
          value={trendFilter}
          onChange={(e) => setTrendFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="">All Trends</option>
          <option value="up">Trending Up</option>
          <option value="down">Trending Down</option>
          <option value="stable">Stable</option>
        </select>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-4 gap-px bg-gray-300">
          <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
            <div className="flex items-center justify-between mb-2">
              <MapPin className="w-8 h-8 text-yellow-500" />
              <span className="text-3xl font-bold text-yellow-500">{summary.total_zones}</span>
            </div>
            <p className="text-gray-300 text-xs uppercase tracking-wide">Total G2 Zones</p>
            <p className="text-xs text-gray-400 mt-1">Geographic coverage areas</p>
          </div>

          <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-8 h-8 text-black" />
              <span className="text-3xl font-bold text-black">{summary.total_leads.toLocaleString()}</span>
            </div>
            <p className="text-gray-800 text-xs uppercase tracking-wide">Total Leads</p>
            <p className="text-xs text-gray-900 mt-1">{summary.total_qualified.toLocaleString()} qualified</p>
          </div>

          <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
            <div className="flex items-center justify-between mb-2">
              <Award className="w-8 h-8 text-yellow-500" />
              <span className="text-3xl font-bold text-yellow-500">{summary.total_enlistments.toLocaleString()}</span>
            </div>
            <p className="text-gray-300 text-xs uppercase tracking-wide">Total Enlistments</p>
            <p className="text-xs text-gray-400 mt-1">
              {(summary.avg_conversion_rate * 100).toFixed(1)}% avg conversion
            </p>
          </div>

          <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-8 h-8 text-black" />
              <span className="text-2xl font-bold text-black">
                <TrendingUp className="w-8 h-8 inline" /> {summary.zones_trending_up} / 
                <TrendingDown className="w-8 h-8 inline" /> {summary.zones_trending_down}
              </span>
            </div>
            <p className="text-gray-800 text-xs uppercase tracking-wide">Zone Trends</p>
            <p className="text-xs text-gray-900 mt-1">Performance momentum</p>
          </div>
        </div>
      )}

      {/* Top Performing Zones Chart */}
      <div className="bg-white border-2 border-gray-300 p-6">
        <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
          <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-yellow-600" />
            Top 10 Zones by Lead Volume
          </h2>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={topZonesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="leads" fill="#3b82f6" name="Total Leads" />
            <Bar yAxisId="left" dataKey="qualified" fill="#8b5cf6" name="Qualified Leads" />
            <Bar yAxisId="left" dataKey="enlistments" fill="#10b981" name="Enlistments" />
            <Bar yAxisId="right" dataKey="conversion_rate" fill="#f59e0b" name="Conversion %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Market Penetration vs Competitive Index */}
      <div className="bg-white border-2 border-gray-300 p-6">
        <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
          <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <Target className="w-5 h-5 text-yellow-600" />
            Market Penetration & Competitive Positioning
          </h2>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={penetrationData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="zone" angle={-45} textAnchor="end" height={100} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="penetration" 
              stroke="#3b82f6" 
              strokeWidth={2}
              name="Market Penetration %"
              dot={{ r: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="competitive" 
              stroke="#ef4444" 
              strokeWidth={2}
              name="Competitive Index %"
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-sm text-gray-600 mt-4 text-center">
          Higher market penetration + lower competitive index = optimal recruiting environment
        </p>
      </div>

      {/* Zone Details Grid */}
      <div className="bg-white border-2 border-gray-300 p-6">
        <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
          <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Zone Details</h2>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {zones.map((zone) => (
            <div
              key={zone.zone_id}
              className={`border-2 p-6 cursor-pointer transition-all ${
                selectedZone?.zone_id === zone.zone_id
                  ? 'border-yellow-600 bg-yellow-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onClick={() => setSelectedZone(zone)}
            >
              {/* Zone Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-600" />
                    {zone.zone_name}
                  </h3>
                  <p className="text-sm text-gray-600">{zone.geographic_area}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Population: {zone.population.toLocaleString()} (
                    {zone.military_age_population.toLocaleString()} military age)
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <div 
                    className="p-2 rounded-lg"
                    style={{ backgroundColor: `${TREND_CONFIG[zone.trend_direction].color}20` }}
                  >
                    {TREND_CONFIG[zone.trend_direction].icon}
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-700">Leads</p>
                  <p className="text-xl font-bold text-blue-900">{zone.lead_count}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <p className="text-xs text-green-700">Qualified</p>
                  <p className="text-xl font-bold text-green-900">{zone.qualified_leads}</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-3">
                  <p className="text-xs text-purple-700">Enlistments</p>
                  <p className="text-xl font-bold text-purple-900">{zone.enlistment_count}</p>
                </div>
              </div>

              {/* Performance Rates */}
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Qualification Rate</span>
                    <span className="font-semibold">{(zone.qualification_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 transition-all"
                      style={{ width: `${zone.qualification_rate * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Conversion Rate</span>
                    <span className="font-semibold">{(zone.conversion_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-green-500 transition-all"
                      style={{ width: `${zone.conversion_rate * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Market Penetration</span>
                    <span className="font-semibold">{(zone.market_penetration_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-purple-500 transition-all"
                      style={{ width: `${zone.market_penetration_rate * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-500">Top Lead Source</p>
                  <p className="font-semibold text-gray-800">{zone.top_lead_source}</p>
                </div>
                <div>
                  <p className="text-gray-500">Top MOS</p>
                  <p className="font-semibold text-gray-800">{zone.top_mos}</p>
                </div>
                <div>
                  <p className="text-gray-500">Avg Quality Score</p>
                  <p className="font-semibold text-gray-800">{zone.avg_lead_quality_score.toFixed(1)}/100</p>
                </div>
                <div>
                  <p className="text-gray-500">Avg Days to Convert</p>
                  <p className="font-semibold text-gray-800">{Math.round(zone.avg_days_to_conversion)} days</p>
                </div>
              </div>

              {/* Brigade/RSID */}
              <div className="mt-3 pt-3 border-t border-gray-200 flex justify-between text-xs text-gray-500">
                <span>Brigade: <strong>{zone.brigade || 'N/A'}</strong></span>
                <span>RSID: <strong>{zone.rsid || 'N/A'}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Zone Radar Chart */}
      {selectedZone && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            Performance Radar: {selectedZone.zone_name}
          </h2>
          <ResponsiveContainer width="100%" height={500}>
            <RadarChart data={getRadarData(selectedZone)}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" />
              <PolarRadiusAxis domain={[0, 100]} />
              <Radar
                name={selectedZone.zone_name}
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};
