import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, Target, Calendar, Award, AlertTriangle,
  CheckCircle, Clock, Users, DollarSign, BarChart3, FileText
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { API_BASE } from '../config/api';

interface QuarterMetrics {
  quarter: string;
  fy: number;
  start_date: string;
  end_date: string;
  goals: {
    contracts: number;
    leads: number;
    events: number;
    budget: number;
  };
  actuals: {
    contracts: number;
    leads: number;
    events: number;
    budget_spent: number;
  };
  performance: {
    contract_rate: number;
    lead_conversion: number;
    roi: number;
    event_effectiveness: number;
  };
  status: 'in_progress' | 'completed' | 'upcoming';
}

interface AssessmentInsight {
  category: string;
  trend: 'positive' | 'negative' | 'neutral';
  message: string;
  recommendation: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

interface HistoricalComparison {
  quarter: string;
  contracts: number;
  leads: number;
  roi: number;
}

const QuarterAssessment: React.FC = () => {
  const [selectedFY, setSelectedFY] = useState(2026);
  const [quarterMetrics, setQuarterMetrics] = useState<QuarterMetrics[]>([]);
  const [selectedQuarter, setSelectedQuarter] = useState<QuarterMetrics | null>(null);
  const [insights, setInsights] = useState<AssessmentInsight[]>([]);
  const [historicalData, setHistoricalData] = useState<HistoricalComparison[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadQuarterAssessment();
  }, [selectedFY]);

  const loadQuarterAssessment = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v2/fusion/latest?limit=1000`);
      const payload = response.ok ? await response.json() : { rows: [] };
      const rows = Array.isArray(payload?.rows) ? payload.rows : [];

      const grouped = new Map<string, { fy: number; qtr: string; leads: number; contracts: number }>();
      rows.forEach((r: any) => {
        const fy = Number(r?.fy || selectedFY) || selectedFY;
        const qtr = String(r?.qtr || 'Q4');
        const key = `${fy}-${qtr}`;
        const current = grouped.get(key) || { fy, qtr, leads: 0, contracts: 0 };
        current.leads += Number(r?.total_leads || 0);
        current.contracts += Number(r?.contracts_signed || 0);
        grouped.set(key, current);
      });

      const quarterOrder = ['Q1', 'Q2', 'Q3', 'Q4'];
      const liveMetrics: QuarterMetrics[] = quarterOrder.map((qtr) => {
        const bucket = grouped.get(`${selectedFY}-${qtr}`) || { fy: selectedFY, qtr, leads: 0, contracts: 0 };
        const contractGoal = Math.max(1, Math.round(bucket.contracts * 1.1));
        const leadGoal = Math.max(1, Math.round(bucket.leads * 1.1));
        const leadConversion = bucket.leads > 0 ? (bucket.contracts / bucket.leads) * 100 : 0;
        return {
          quarter: qtr,
          fy: selectedFY,
          start_date: `${selectedFY}-01-01`,
          end_date: `${selectedFY}-03-31`,
          goals: { contracts: contractGoal, leads: leadGoal, events: 0, budget: 0 },
          actuals: { contracts: bucket.contracts, leads: bucket.leads, events: 0, budget_spent: 0 },
          performance: {
            contract_rate: contractGoal > 0 ? (bucket.contracts / contractGoal) * 100 : 0,
            lead_conversion: leadConversion,
            roi: leadConversion / 10,
            event_effectiveness: leadConversion / 5,
          },
          status: qtr === 'Q4' ? 'in_progress' : 'completed',
        };
      });

      setQuarterMetrics(liveMetrics);
      setSelectedQuarter(liveMetrics[3] || liveMetrics[0] || null);
      generateInsights(liveMetrics);

      const historical = Array.from(grouped.values())
        .sort((a, b) => (a.fy - b.fy) || (quarterOrder.indexOf(a.qtr) - quarterOrder.indexOf(b.qtr)))
        .slice(-8)
        .map((v) => ({
          quarter: `FY${String(v.fy).slice(-2)} ${v.qtr}`,
          contracts: v.contracts,
          leads: v.leads,
          roi: v.leads > 0 ? Number(((v.contracts / v.leads) * 10).toFixed(2)) : 0,
        }));
      setHistoricalData(historical);

    } catch (error) {
      console.error('Error loading quarter assessment:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateInsights = (metrics: QuarterMetrics[]) => {
    const generatedInsights: AssessmentInsight[] = [];
    
    metrics.forEach(q => {
      // Contract performance
      if (q.performance.contract_rate < 90) {
        generatedInsights.push({
          category: 'Contracts',
          trend: 'negative',
          message: `${q.quarter} contracts at ${q.performance.contract_rate.toFixed(1)}% of goal`,
          recommendation: 'Increase recruiter engagement and lead follow-up cadence',
          priority: 'high'
        });
      } else if (q.performance.contract_rate > 110) {
        generatedInsights.push({
          category: 'Contracts',
          trend: 'positive',
          message: `${q.quarter} exceeded contract goals by ${(q.performance.contract_rate - 100).toFixed(1)}%`,
          recommendation: 'Replicate successful tactics in underperforming quarters',
          priority: 'low'
        });
      }

      // ROI analysis
      if (q.performance.roi < 2.5) {
        generatedInsights.push({
          category: 'ROI',
          trend: 'negative',
          message: `${q.quarter} ROI below target at ${q.performance.roi.toFixed(2)}`,
          recommendation: 'Review event mix and reduce low-performing event types',
          priority: 'medium'
        });
      }

      // Lead conversion
      if (q.performance.lead_conversion < 13) {
        generatedInsights.push({
          category: 'Lead Conversion',
          trend: 'negative',
          message: `${q.quarter} conversion rate at ${q.performance.lead_conversion.toFixed(1)}%`,
          recommendation: 'Enhance lead qualification process and recruiter training',
          priority: 'high'
        });
      }
    });

    setInsights(generatedInsights);
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'positive') return <TrendingUp className="w-5 h-5 text-green-600" />;
    if (trend === 'negative') return <TrendingDown className="w-5 h-5 text-red-600" />;
    return <Target className="w-5 h-5 text-gray-600" />;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 border-red-500 text-red-800';
      case 'high': return 'bg-orange-100 border-orange-500 text-orange-800';
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      default: return 'bg-blue-100 border-blue-500 text-blue-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
          <p className="mt-4 text-gray-600">Loading quarter assessment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-yellow-500" />
            <div>
              <h1 className="text-2xl font-bold text-white">Quarter Assessment Dashboard</h1>
              <p className="text-gray-300 text-sm">Performance tracking and strategic insights</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <label className="text-white font-semibold">Fiscal Year:</label>
            <select
              value={selectedFY}
              onChange={(e) => setSelectedFY(Number(e.target.value))}
              className="px-4 py-2 border border-gray-600 rounded-lg bg-gray-700 text-white focus:ring-2 focus:ring-yellow-500"
            >
              <option value={2024}>FY 2024</option>
              <option value={2025}>FY 2025</option>
              <option value={2026}>FY 2026</option>
            </select>
          </div>
        </div>
      </div>

      {/* Quarter Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {quarterMetrics.map((quarter) => (
          <div
            key={quarter.quarter}
            onClick={() => setSelectedQuarter(quarter)}
            className={`bg-white rounded-lg shadow-md border-2 p-4 cursor-pointer transition-all hover:shadow-lg ${
              selectedQuarter?.quarter === quarter.quarter
                ? 'border-yellow-500 ring-2 ring-yellow-200'
                : 'border-gray-200'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-lg text-gray-800">{quarter.quarter}</h3>
              {quarter.status === 'completed' ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : quarter.status === 'in_progress' ? (
                <Clock className="w-5 h-5 text-yellow-600" />
              ) : (
                <Calendar className="w-5 h-5 text-gray-400" />
              )}
            </div>
            <div className="text-xs text-gray-500 mb-3">
              {new Date(quarter.start_date).toLocaleDateString()} - {new Date(quarter.end_date).toLocaleDateString()}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Contracts:</span>
                <span className={`font-bold text-sm ${quarter.performance.contract_rate >= 100 ? 'text-green-600' : 'text-red-600'}`}>
                  {quarter.actuals.contracts}/{quarter.goals.contracts}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Leads:</span>
                <span className="font-bold text-sm text-gray-800">
                  {quarter.actuals.leads}/{quarter.goals.leads}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">ROI:</span>
                <span className="font-bold text-sm text-blue-600">
                  {quarter.performance.roi.toFixed(2)}x
                </span>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="flex items-center justify-center">
                <span className={`text-xs font-bold px-2 py-1 rounded ${
                  quarter.performance.contract_rate >= 100 ? 'bg-green-100 text-green-800' :
                  quarter.performance.contract_rate >= 90 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {quarter.performance.contract_rate.toFixed(1)}% of Goal
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed Quarter View */}
      {selectedQuarter && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Performance Metrics */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md border-2 border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Target className="w-6 h-6 text-yellow-600" />
              {selectedQuarter.quarter} FY{selectedFY} Performance Detail
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <Users className="w-6 h-6 text-blue-600 mb-2" />
                <p className="text-xs text-gray-600 mb-1">Contract Rate</p>
                <p className="text-2xl font-bold text-blue-800">{selectedQuarter.performance.contract_rate.toFixed(1)}%</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <TrendingUp className="w-6 h-6 text-green-600 mb-2" />
                <p className="text-xs text-gray-600 mb-1">Lead Conversion</p>
                <p className="text-2xl font-bold text-green-800">{selectedQuarter.performance.lead_conversion.toFixed(1)}%</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <DollarSign className="w-6 h-6 text-purple-600 mb-2" />
                <p className="text-xs text-gray-600 mb-1">ROI</p>
                <p className="text-2xl font-bold text-purple-800">{selectedQuarter.performance.roi.toFixed(2)}x</p>
              </div>
              <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                <Award className="w-6 h-6 text-orange-600 mb-2" />
                <p className="text-xs text-gray-600 mb-1">Event Effectiveness</p>
                <p className="text-2xl font-bold text-orange-800">{selectedQuarter.performance.event_effectiveness.toFixed(2)}</p>
              </div>
            </div>

            {/* Goals vs Actuals Comparison */}
            <div className="mt-6">
              <h3 className="text-lg font-bold text-gray-800 mb-3">Goals vs. Actuals</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart
                  data={[
                    { metric: 'Contracts', Goal: selectedQuarter.goals.contracts, Actual: selectedQuarter.actuals.contracts },
                    { metric: 'Leads', Goal: selectedQuarter.goals.leads, Actual: selectedQuarter.actuals.leads },
                    { metric: 'Events', Goal: selectedQuarter.goals.events, Actual: selectedQuarter.actuals.events }
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Goal" fill="#94a3b8" name="Goal" />
                  <Bar dataKey="Actual" fill="#3b82f6" name="Actual" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Insights & Recommendations */}
          <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
              Key Insights
            </h2>
            <div className="space-y-3">
              {insights.map((insight, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border-l-4 ${getPriorityColor(insight.priority)}`}
                >
                  <div className="flex items-start gap-2 mb-2">
                    {getTrendIcon(insight.trend)}
                    <div className="flex-1">
                      <p className="font-bold text-sm">{insight.category}</p>
                      <p className="text-xs mt-1">{insight.message}</p>
                    </div>
                  </div>
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs font-semibold text-gray-700">Recommendation:</p>
                    <p className="text-xs text-gray-600 mt-1">{insight.recommendation}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Historical Trend */}
      <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-600" />
          Historical Trend Analysis
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={historicalData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="quarter" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="contracts" stroke="#3b82f6" strokeWidth={2} name="Contracts" />
            <Line yAxisId="left" type="monotone" dataKey="leads" stroke="#10b981" strokeWidth={2} name="Leads" />
            <Line yAxisId="right" type="monotone" dataKey="roi" stroke="#f59e0b" strokeWidth={2} name="ROI" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default QuarterAssessment;
