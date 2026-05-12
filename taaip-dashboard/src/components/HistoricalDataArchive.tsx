import React, { useState, useEffect } from 'react';
import {
  Archive, Calendar, Search, Filter, Download, TrendingUp, Award,
  MapPin, Users, DollarSign, BarChart3, FileText, Clock, Target
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';

interface HistoricalEvent {
  event_id: string;
  name: string;
  date: string;
  location: string;
  zipcode: string;
  event_type: string;
  target_audience: string;
  attendance: number;
  leads_generated: number;
  contracts: number;
  budget: number;
  roi: number;
  assets_used: string[];
  effectiveness_score: number;
  lessons_learned: string;
  recommendations: string;
}

interface HistoricalMetrics {
  total_events: number;
  total_leads: number;
  total_contracts: number;
  avg_roi: number;
  best_performing_type: string;
  best_performing_location: string;
}

const HistoricalDataArchive: React.FC = () => {
  const [historicalEvents, setHistoricalEvents] = useState<HistoricalEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<HistoricalEvent[]>([]);
  const [metrics, setMetrics] = useState<HistoricalMetrics | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<HistoricalEvent | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEventType, setFilterEventType] = useState('all');
  const [filterDateRange, setFilterDateRange] = useState('all');
  const [sortBy, setSortBy] = useState<'date' | 'roi' | 'leads' | 'effectiveness'>('date');

  useEffect(() => {
    loadHistoricalData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, filterEventType, filterDateRange, sortBy, historicalEvents]);

  const loadHistoricalData = async () => {
    setLoading(true);
    try {
      // Mock historical data - replace with actual API
      const mockEvents: HistoricalEvent[] = [
        {
          event_id: 'evt_hist_001',
          name: 'Houston Tech Career Fair 2024',
          date: '2024-09-15',
          location: 'Houston, TX',
          zipcode: '77001',
          event_type: 'career_fair',
          target_audience: 'college',
          attendance: 520,
          leads_generated: 47,
          contracts: 6,
          budget: 22000,
          roi: 2.73,
          assets_used: ['Army Experience Center', 'VR Simulator', 'Recruiter Team'],
          effectiveness_score: 8.5,
          lessons_learned: 'VR simulator had highest engagement. Need more technical MOS brochures.',
          recommendations: 'Repeat next year with increased cyber/signal MOS focus'
        },
        {
          event_id: 'evt_hist_002',
          name: 'Dallas Gaming Expo 2024',
          date: '2024-10-20',
          location: 'Dallas, TX',
          zipcode: '75201',
          event_type: 'gaming_event',
          target_audience: 'high_school',
          attendance: 850,
          leads_generated: 38,
          contracts: 5,
          budget: 28000,
          roi: 1.79,
          assets_used: ['Mobile Esports Trailer', 'Digital Campaign'],
          effectiveness_score: 7.2,
          lessons_learned: 'High attendance but lower conversion. Need better lead qualification process.',
          recommendations: 'Add pre-event social media targeting to improve lead quality'
        },
        {
          event_id: 'evt_hist_003',
          name: 'San Antonio Military Appreciation Day',
          date: '2024-11-11',
          location: 'San Antonio, TX',
          zipcode: '78201',
          event_type: 'community_event',
          target_audience: 'general_public',
          attendance: 1200,
          leads_generated: 65,
          contracts: 9,
          budget: 35000,
          roi: 2.57,
          assets_used: ['Black Daggers Parachute Team', 'HMMWV Display', 'Army Band'],
          effectiveness_score: 9.1,
          lessons_learned: 'Parachute demo was major draw. Strong family engagement.',
          recommendations: 'Must-keep event. Request parachute team annually.'
        },
        {
          event_id: 'evt_hist_004',
          name: 'Austin College Virtual Session',
          date: '2024-08-25',
          location: 'Austin, TX (Virtual)',
          zipcode: '78701',
          event_type: 'virtual_event',
          target_audience: 'college',
          attendance: 180,
          leads_generated: 22,
          contracts: 3,
          budget: 5000,
          roi: 6.0,
          assets_used: ['Digital Campaign', 'Virtual Briefing'],
          effectiveness_score: 8.8,
          lessons_learned: 'Very cost-effective. High-quality leads from targeted college audience.',
          recommendations: 'Expand virtual events for college demographic'
        },
        {
          event_id: 'evt_hist_005',
          name: 'Fort Worth High School Career Day',
          date: '2024-05-10',
          location: 'Fort Worth, TX',
          zipcode: '76101',
          event_type: 'career_fair',
          target_audience: 'high_school',
          attendance: 320,
          leads_generated: 28,
          contracts: 4,
          budget: 8000,
          roi: 3.5,
          assets_used: ['Recruiter Team', 'Static Display'],
          effectiveness_score: 7.5,
          lessons_learned: 'Strong recruiter engagement. Limited by lack of interactive assets.',
          recommendations: 'Add VR simulator or vehicle display for next iteration'
        }
      ];

      setHistoricalEvents(mockEvents);

      // Calculate metrics
      const totalLeads = mockEvents.reduce((sum, e) => sum + e.leads_generated, 0);
      const totalContracts = mockEvents.reduce((sum, e) => sum + e.contracts, 0);
      const avgROI = mockEvents.reduce((sum, e) => sum + e.roi, 0) / mockEvents.length;

      // Find best performing
      const eventTypePerformance = mockEvents.reduce((acc, e) => {
        if (!acc[e.event_type]) acc[e.event_type] = { leads: 0, count: 0 };
        acc[e.event_type].leads += e.leads_generated;
        acc[e.event_type].count += 1;
        return acc;
      }, {} as Record<string, { leads: number; count: number }>);

      const bestType = Object.entries(eventTypePerformance).reduce((best, [type, data]) => 
        (data.leads / data.count) > (best.avg || 0) ? { type, avg: data.leads / data.count } : best,
        { type: '', avg: 0 }
      ).type;

      setMetrics({
        total_events: mockEvents.length,
        total_leads: totalLeads,
        total_contracts: totalContracts,
        avg_roi: parseFloat(avgROI.toFixed(2)),
        best_performing_type: bestType,
        best_performing_location: 'San Antonio, TX'
      });

    } catch (error) {
      console.error('Error loading historical data:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...historicalEvents];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(e => 
        e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.location.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Event type filter
    if (filterEventType !== 'all') {
      filtered = filtered.filter(e => e.event_type === filterEventType);
    }

    // Date range filter
    if (filterDateRange !== 'all') {
      const now = new Date();
      const sixMonthsAgo = new Date(now.setMonth(now.getMonth() - 6));
      const oneYearAgo = new Date(now.setMonth(now.getMonth() - 6));
      
      filtered = filtered.filter(e => {
        const eventDate = new Date(e.date);
        if (filterDateRange === '6months') return eventDate >= sixMonthsAgo;
        if (filterDateRange === '1year') return eventDate >= oneYearAgo;
        return true;
      });
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'roi': return b.roi - a.roi;
        case 'leads': return b.leads_generated - a.leads_generated;
        case 'effectiveness': return b.effectiveness_score - a.effectiveness_score;
        case 'date': default: return new Date(b.date).getTime() - new Date(a.date).getTime();
      }
    });

    setFilteredEvents(filtered);
  };

  const exportData = () => {
    // Export to CSV
    const headers = ['Event Name', 'Date', 'Location', 'Type', 'Leads', 'Contracts', 'ROI', 'Effectiveness'];
    const rows = filteredEvents.map(e => [
      e.name, e.date, e.location, e.event_type, e.leads_generated, 
      e.contracts, e.roi, e.effectiveness_score
    ]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `historical_events_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
          <p className="mt-4 text-gray-600">Loading historical data...</p>
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
            <Archive className="w-8 h-8 text-yellow-500" />
            <div>
              <h1 className="text-2xl font-bold text-white">Historical Data Archive</h1>
              <p className="text-gray-300 text-sm">Past events, lessons learned, and performance metrics</p>
            </div>
          </div>
          <button
            onClick={exportData}
            className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-black font-bold rounded-lg flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export Data
          </button>
        </div>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-4">
            <Calendar className="w-6 h-6 text-blue-600 mb-2" />
            <p className="text-xs text-gray-600 mb-1">Total Events</p>
            <p className="text-2xl font-bold text-blue-800">{metrics.total_events}</p>
          </div>
          <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-4">
            <Users className="w-6 h-6 text-green-600 mb-2" />
            <p className="text-xs text-gray-600 mb-1">Total Leads</p>
            <p className="text-2xl font-bold text-green-800">{metrics.total_leads}</p>
          </div>
          <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-4">
            <Target className="w-6 h-6 text-purple-600 mb-2" />
            <p className="text-xs text-gray-600 mb-1">Total Contracts</p>
            <p className="text-2xl font-bold text-purple-800">{metrics.total_contracts}</p>
          </div>
          <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-4">
            <TrendingUp className="w-6 h-6 text-orange-600 mb-2" />
            <p className="text-xs text-gray-600 mb-1">Avg ROI</p>
            <p className="text-2xl font-bold text-orange-800">{metrics.avg_roi}x</p>
          </div>
          <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-4">
            <Award className="w-6 h-6 text-yellow-600 mb-2" />
            <p className="text-xs text-gray-600 mb-1">Best Type</p>
            <p className="text-sm font-bold text-yellow-800">{metrics.best_performing_type.replace('_', ' ')}</p>
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search events or locations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={filterEventType}
            onChange={(e) => setFilterEventType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Event Types</option>
            <option value="career_fair">Career Fair</option>
            <option value="gaming_event">Gaming Event</option>
            <option value="community_event">Community Event</option>
            <option value="virtual_event">Virtual Event</option>
          </select>
          <select
            value={filterDateRange}
            onChange={(e) => setFilterDateRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Time</option>
            <option value="6months">Last 6 Months</option>
            <option value="1year">Last Year</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="date">Sort by Date</option>
            <option value="roi">Sort by ROI</option>
            <option value="leads">Sort by Leads</option>
            <option value="effectiveness">Sort by Effectiveness</option>
          </select>
        </div>
      </div>

      {/* Historical Events List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          {filteredEvents.map((event) => (
            <div
              key={event.event_id}
              onClick={() => setSelectedEvent(event)}
              className={`bg-white rounded-lg shadow-md border-2 p-4 cursor-pointer transition-all hover:shadow-lg ${
                selectedEvent?.event_id === event.event_id
                  ? 'border-yellow-500 ring-2 ring-yellow-200'
                  : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-bold text-gray-800">{event.name}</h3>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(event.date).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {event.location}
                    </span>
                  </div>
                </div>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-bold rounded">
                  {event.event_type.replace('_', ' ')}
                </span>
              </div>
              
              <div className="grid grid-cols-4 gap-2 mt-3 pt-3 border-t border-gray-200">
                <div>
                  <p className="text-xs text-gray-500">Leads</p>
                  <p className="font-bold text-green-700">{event.leads_generated}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Contracts</p>
                  <p className="font-bold text-purple-700">{event.contracts}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">ROI</p>
                  <p className="font-bold text-orange-700">{event.roi.toFixed(2)}x</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Score</p>
                  <p className="font-bold text-blue-700">{event.effectiveness_score}/10</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Event Detail */}
        {selectedEvent && (
          <div className="bg-white rounded-lg shadow-lg border-2 border-yellow-500 p-6 sticky top-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <FileText className="w-6 h-6 text-yellow-600" />
              Event Details
            </h2>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Event Name:</p>
                <p className="text-gray-900">{selectedEvent.name}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-1">Date:</p>
                  <p className="text-gray-900">{new Date(selectedEvent.date).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-1">Location:</p>
                  <p className="text-gray-900">{selectedEvent.location}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-1">Attendance:</p>
                  <p className="text-gray-900">{selectedEvent.attendance}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-1">Budget:</p>
                  <p className="text-gray-900">${selectedEvent.budget.toLocaleString()}</p>
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-1">Assets Used:</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {selectedEvent.assets_used.map((asset, idx) => (
                    <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded">
                      {asset}
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Leads</p>
                  <p className="text-xl font-bold text-green-700">{selectedEvent.leads_generated}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 mb-1">Contracts</p>
                  <p className="text-xl font-bold text-purple-700">{selectedEvent.contracts}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 mb-1">ROI</p>
                  <p className="text-xl font-bold text-orange-700">{selectedEvent.roi.toFixed(2)}x</p>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <p className="text-sm font-semibold text-gray-700 mb-2">Lessons Learned:</p>
                <p className="text-sm text-gray-700 bg-blue-50 p-3 rounded-lg border border-blue-200">
                  {selectedEvent.lessons_learned}
                </p>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Recommendations:</p>
                <p className="text-sm text-gray-700 bg-green-50 p-3 rounded-lg border border-green-200">
                  {selectedEvent.recommendations}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoricalDataArchive;
