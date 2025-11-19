import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, Target, DollarSign, Users, Award,
  Calendar, MapPin, Sparkles, BarChart3, PieChart as PieChartIcon,
  AlertCircle, CheckCircle2, Activity, Zap
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const API_BASE = 'http://localhost:8000';

// Event type colors and icons
const EVENT_TYPE_CONFIG = {
  lead_generating: { color: '#10b981', icon: <Users className="w-4 h-4" />, label: 'Lead Generating' },
  shaping: { color: '#8b5cf6', icon: <Target className="w-4 h-4" />, label: 'Shaping' },
  brand_awareness: { color: '#f59e0b', icon: <Sparkles className="w-4 h-4" />, label: 'Brand Awareness' },
  community_engagement: { color: '#3b82f6', icon: <Activity className="w-4 h-4" />, label: 'Community Engagement' },
  retention: { color: '#ec4899', icon: <Award className="w-4 h-4" />, label: 'Retention' },
  research: { color: '#6b7280', icon: <BarChart3 className="w-4 h-4" />, label: 'Research' }
};

interface EventPerformance {
  event_id: string;
  name: string;
  event_type_category: string;
  location: string;
  start_date: string;
  budget: number;
  status: string;
  rsid: string;
  brigade: string;
  predicted: {
    leads: number;
    conversions: number;
    roi: number;
    cost_per_lead: number;
    confidence: number;
  };
  actual: {
    leads: number;
    conversions: number;
    roi: number;
    cost_per_lead: number;
  };
  variance: {
    leads: number;
    roi: number;
    accuracy: number;
  };
}

export const EventPerformanceDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<EventPerformance[]>([]);
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [viewMode, setViewMode] = useState<'summary' | 'detail'>('summary');
  const [selectedEvent, setSelectedEvent] = useState<EventPerformance | null>(null);

  useEffect(() => {
    fetchEventPerformance();
  }, [selectedEventType]);

  const fetchEventPerformance = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedEventType) params.append('event_type', selectedEventType);
      
      const res = await fetch(`${API_BASE}/api/v2/events/performance?${params}`);
      const data = await res.json();
      
      if (data.status === 'ok') {
        setEvents(data.data);
      }
    } catch (error) {
      console.error('Error fetching event performance:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading event performance data...</div>;
  }

  // Calculate summary metrics
  const eventsWithPredictions = events.filter(e => e.predicted.confidence > 0);
  const completedEvents = events.filter(e => e.actual.leads > 0);
  
  const avgPredictionAccuracy = completedEvents.length > 0
    ? (completedEvents.reduce((sum, e) => sum + (e.variance.accuracy || 0), 0) / completedEvents.length) * 100
    : 0;
  
  const totalActualLeads = completedEvents.reduce((sum, e) => sum + e.actual.leads, 0);
  const totalPredictedLeads = eventsWithPredictions.reduce((sum, e) => sum + e.predicted.leads, 0);
  const totalActualROI = completedEvents.reduce((sum, e) => sum + e.actual.roi, 0);

  // Event type distribution
  const eventTypeData = Object.entries(
    events.reduce((acc, e) => {
      acc[e.event_type_category] = (acc[e.event_type_category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([type, count]) => ({
    name: EVENT_TYPE_CONFIG[type as keyof typeof EVENT_TYPE_CONFIG]?.label || type,
    value: count,
    fill: EVENT_TYPE_CONFIG[type as keyof typeof EVENT_TYPE_CONFIG]?.color || '#6b7280'
  }));

  // Prediction accuracy by event type
  const accuracyByType = Object.entries(
    completedEvents.reduce((acc, e) => {
      if (!acc[e.event_type_category]) {
        acc[e.event_type_category] = { total: 0, count: 0 };
      }
      acc[e.event_type_category].total += (e.variance.accuracy || 0);
      acc[e.event_type_category].count += 1;
      return acc;
    }, {} as Record<string, { total: number; count: number }>)
  ).map(([type, data]) => ({
    type: EVENT_TYPE_CONFIG[type as keyof typeof EVENT_TYPE_CONFIG]?.label || type,
    accuracy: (data.total / data.count) * 100
  }));

  // Predicted vs Actual scatter plot data
  const predictionComparisonData = completedEvents.map(e => ({
    predicted: e.predicted.leads,
    actual: e.actual.leads,
    name: e.name
  }));

  const renderSummary = () => (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-4 gap-px bg-gray-300">
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
          <div className="flex items-center justify-between mb-2">
            <Sparkles className="w-8 h-8 text-yellow-500" />
            <span className="text-3xl font-bold text-yellow-500">{eventsWithPredictions.length}</span>
          </div>
          <p className="text-gray-300 text-xs uppercase tracking-wide">Events with Predictions</p>
          <p className="text-xs text-gray-400 mt-1">ML-powered forecasting</p>
        </div>

        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
          <div className="flex items-center justify-between mb-2">
            <Users className="w-8 h-8 text-black" />
            <span className="text-3xl font-bold text-black">{totalActualLeads}</span>
          </div>
          <p className="text-gray-800 text-xs uppercase tracking-wide">Actual Leads Generated</p>
          <p className="text-xs text-gray-900 mt-1">vs {totalPredictedLeads} predicted</p>
        </div>

        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-6">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-8 h-8 text-yellow-500" />
            <span className="text-3xl font-bold text-yellow-500">{avgPredictionAccuracy.toFixed(1)}%</span>
          </div>
          <p className="text-gray-300 text-xs uppercase tracking-wide">Avg Prediction Accuracy</p>
          <p className="text-xs text-gray-400 mt-1">{completedEvents.length} completed events</p>
        </div>

        <div className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 text-black" />
            <span className="text-3xl font-bold text-black">{totalActualROI.toFixed(1)}x</span>
          </div>
          <p className="text-gray-800 text-xs uppercase tracking-wide">Total Actual ROI</p>
          <p className="text-xs text-gray-900 mt-1">From completed events</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Event Type Distribution */}
        <div className="bg-white border-2 border-gray-300 p-6">
          <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
              <PieChartIcon className="w-5 h-5 text-yellow-600" />
              Event Type Distribution
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={eventTypeData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry) => `${entry.name}: ${entry.value}`}
              >
                {eventTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Prediction Accuracy by Type */}
        <div className="bg-white border-2 border-gray-300 p-6">
          <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
              <Target className="w-5 h-5 text-yellow-600" />
              Prediction Accuracy by Event Type
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={accuracyByType}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" angle={-45} textAnchor="end" height={100} />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
              <Bar dataKey="accuracy" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Predicted vs Actual Scatter Plot */}
      {completedEvents.length > 0 && (
        <div className="bg-white border-2 border-gray-300 p-6">
          <div className="bg-gray-100 -m-6 mb-4 p-4 border-b-2 border-gray-300">
            <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-600" />
              Predicted vs Actual Lead Generation
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="predicted" name="Predicted" />
              <YAxis type="number" dataKey="actual" name="Actual" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Legend />
              <Scatter name="Events" data={predictionComparisonData} fill="#3b82f6" />
              {/* Perfect prediction line */}
              <Scatter
                name="Perfect Prediction"
                data={[{ predicted: 0, actual: 0 }, { predicted: 100, actual: 100 }]}
                fill="#10b981"
                line
                shape="cross"
              />
            </ScatterChart>
          </ResponsiveContainer>
          <p className="text-sm text-gray-600 mt-2 text-center">
            Points closer to the green line indicate more accurate predictions
          </p>
        </div>
      )}

      {/* Events List with Filter */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-green-600" />
            Event Performance Details
          </h3>
          <select
            value={selectedEventType}
            onChange={(e) => setSelectedEventType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="">All Event Types</option>
            {Object.entries(EVENT_TYPE_CONFIG).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
            ))}
          </select>
        </div>

        <div className="space-y-4 max-h-[600px] overflow-y-auto">
          {events.map((event) => (
            <div
              key={event.event_id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => { setSelectedEvent(event); setViewMode('detail'); }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg" style={{ 
                      backgroundColor: `${EVENT_TYPE_CONFIG[event.event_type_category as keyof typeof EVENT_TYPE_CONFIG]?.color}20` 
                    }}>
                      {EVENT_TYPE_CONFIG[event.event_type_category as keyof typeof EVENT_TYPE_CONFIG]?.icon}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-800">{event.name}</h4>
                      <p className="text-sm text-gray-600 flex items-center gap-2">
                        <MapPin className="w-3 h-3" />
                        {event.location} • {new Date(event.start_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                    <div>
                      <p className="text-xs text-gray-500">Budget</p>
                      <p className="font-semibold text-gray-800">${event.budget.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Predicted Leads</p>
                      <p className="font-semibold text-blue-600">{event.predicted.leads}</p>
                      <p className="text-xs text-gray-500">{(event.predicted.confidence * 100).toFixed(0)}% confidence</p>
                    </div>
                    {event.actual.leads > 0 && (
                      <>
                        <div>
                          <p className="text-xs text-gray-500">Actual Leads</p>
                          <p className="font-semibold text-green-600">{event.actual.leads}</p>
                          {event.variance.leads !== 0 && (
                            <p className={`text-xs flex items-center gap-1 ${event.variance.leads > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {event.variance.leads > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                              {Math.abs(event.variance.leads).toFixed(1)}% variance
                            </p>
                          )}
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Prediction Accuracy</p>
                          <p className="font-semibold text-purple-600">
                            {((event.variance.accuracy || 0) * 100).toFixed(1)}%
                          </p>
                          {event.variance.accuracy && event.variance.accuracy > 0.8 ? (
                            <p className="text-xs text-green-600 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Excellent
                            </p>
                          ) : (
                            <p className="text-xs text-orange-600 flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" /> Needs tuning
                            </p>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="ml-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    event.status === 'completed' ? 'bg-green-100 text-green-800' :
                    event.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {event.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderDetail = () => {
    if (!selectedEvent) return null;

    return (
      <div className="space-y-6">
        <button
          onClick={() => setViewMode('summary')}
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors"
        >
          ← Back to Summary
        </button>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-800 mb-2">{selectedEvent.name}</h2>
              <p className="text-gray-600 flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                {selectedEvent.location} • {new Date(selectedEvent.start_date).toLocaleDateString()}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-lg" style={{ 
                backgroundColor: `${EVENT_TYPE_CONFIG[selectedEvent.event_type_category as keyof typeof EVENT_TYPE_CONFIG]?.color}20` 
              }}>
                {EVENT_TYPE_CONFIG[selectedEvent.event_type_category as keyof typeof EVENT_TYPE_CONFIG]?.icon}
              </div>
              <div>
                <p className="text-sm text-gray-500">Event Type</p>
                <p className="font-semibold text-gray-800">
                  {EVENT_TYPE_CONFIG[selectedEvent.event_type_category as keyof typeof EVENT_TYPE_CONFIG]?.label}
                </p>
              </div>
            </div>
          </div>

          {/* Prediction vs Actual Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            {/* Predicted Metrics */}
            <div className="border-2 border-blue-200 rounded-xl p-6 bg-blue-50">
              <h3 className="text-lg font-bold text-blue-800 mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                ML Predicted Performance
              </h3>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-blue-700">Predicted Leads</p>
                  <p className="text-3xl font-bold text-blue-900">{selectedEvent.predicted.leads}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-700">Predicted Conversions</p>
                  <p className="text-2xl font-bold text-blue-900">{selectedEvent.predicted.conversions}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-700">Predicted ROI</p>
                  <p className="text-2xl font-bold text-blue-900">{selectedEvent.predicted.roi.toFixed(2)}x</p>
                </div>
                <div>
                  <p className="text-sm text-blue-700">Predicted Cost/Lead</p>
                  <p className="text-2xl font-bold text-blue-900">${selectedEvent.predicted.cost_per_lead.toFixed(2)}</p>
                </div>
                <div className="pt-4 border-t border-blue-300">
                  <p className="text-sm text-blue-700">Confidence Score</p>
                  <p className="text-xl font-bold text-blue-900">{(selectedEvent.predicted.confidence * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>

            {/* Actual Metrics */}
            {selectedEvent.actual.leads > 0 ? (
              <div className="border-2 border-green-200 rounded-xl p-6 bg-green-50">
                <h3 className="text-lg font-bold text-green-800 mb-4 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" />
                  Actual Performance
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-green-700">Actual Leads</p>
                    <p className="text-3xl font-bold text-green-900">{selectedEvent.actual.leads}</p>
                    {selectedEvent.variance.leads !== 0 && (
                      <p className={`text-sm flex items-center gap-1 mt-1 ${
                        selectedEvent.variance.leads > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {selectedEvent.variance.leads > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {Math.abs(selectedEvent.variance.leads).toFixed(1)}% variance
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-green-700">Actual Conversions</p>
                    <p className="text-2xl font-bold text-green-900">{selectedEvent.actual.conversions}</p>
                  </div>
                  <div>
                    <p className="text-sm text-green-700">Actual ROI</p>
                    <p className="text-2xl font-bold text-green-900">{selectedEvent.actual.roi.toFixed(2)}x</p>
                    {selectedEvent.variance.roi !== 0 && (
                      <p className={`text-sm flex items-center gap-1 mt-1 ${
                        selectedEvent.variance.roi > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {selectedEvent.variance.roi > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {Math.abs(selectedEvent.variance.roi).toFixed(1)}% variance
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-green-700">Actual Cost/Lead</p>
                    <p className="text-2xl font-bold text-green-900">${selectedEvent.actual.cost_per_lead.toFixed(2)}</p>
                  </div>
                  <div className="pt-4 border-t border-green-300">
                    <p className="text-sm text-green-700">Prediction Accuracy</p>
                    <p className="text-xl font-bold text-green-900">
                      {((selectedEvent.variance.accuracy || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="border-2 border-gray-200 rounded-xl p-6 bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                  <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 font-medium">Event Not Yet Completed</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Actual results will appear here after the event concludes
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Additional Event Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Budget</p>
              <p className="text-2xl font-bold text-gray-800">${selectedEvent.budget.toLocaleString()}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">RSID</p>
              <p className="text-xl font-semibold text-gray-800">{selectedEvent.rsid || 'N/A'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Brigade</p>
              <p className="text-xl font-semibold text-gray-800">{selectedEvent.brigade || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-purple-600" />
            Event Performance & ML Predictions
          </h1>
          <p className="text-gray-600 mt-1">
            AI-powered event forecasting • Predicted vs Actual analysis • ROI tracking
          </p>
        </div>
      </div>

      {viewMode === 'summary' ? renderSummary() : renderDetail()}
    </div>
  );
};
