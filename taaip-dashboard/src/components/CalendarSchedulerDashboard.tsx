import React, { useState, useEffect } from 'react';
import { 
  Calendar, Clock, AlertCircle, CheckCircle2,
  FileText, TrendingUp, Target, Plus,
  ChevronLeft, ChevronRight, Filter, Download, RefreshCw
} from 'lucide-react';
import { UniversalFilter, FilterState } from './UniversalFilter';

const API_BASE = 'http://localhost:8000';

// Event type colors
const EVENT_TYPE_COLORS: { [key: string]: string } = {
  event: '#3b82f6',
  marketing: '#8b5cf6',
  meeting: '#ec4899',
  deadline: '#ef4444',
  training: '#f59e0b',
  report_due: '#10b981',
  review: '#06b6d4',
  other: '#6b7280',
};

// Priority colors
const PRIORITY_COLORS: { [key: string]: string } = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#991b1b',
};

// Status colors
const STATUS_COLORS: { [key: string]: string } = {
  scheduled: '#3b82f6',
  in_progress: '#f59e0b',
  completed: '#10b981',
  cancelled: '#6b7280',
  postponed: '#8b5cf6',
};

interface CalendarEvent {
  event_id: string;
  title: string;
  description: string;
  event_type: string;
  start_datetime: string;
  end_datetime: string;
  all_day: boolean;
  location: string;
  status: string;
  priority: string;
  rsid: string;
  brigade: string;
}

interface StatusReport {
  report_id: string;
  report_type: string;
  report_category: string;
  report_period_start: string;
  report_period_end: string;
  generated_date: string;
  status: string;
  summary: string;
  key_metrics: string;
  rsid: string;
}

interface CalendarSummary {
  total_events: number;
  upcoming_events: number;
  overdue_events: number;
  completed_events: number;
  events_by_type: { [key: string]: number };
  events_by_priority: { [key: string]: number };
  events_by_status: { [key: string]: number };
  next_7_days_count: number;
  next_30_days_count: number;
}

export const CalendarSchedulerDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [reports, setReports] = useState<StatusReport[]>([]);
  const [summary, setSummary] = useState<CalendarSummary | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<'calendar' | 'list' | 'reports' | 'quarterly'>('calendar');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterPriority, setFilterPriority] = useState<string>('all');
  const [creatingProject, setCreatingProject] = useState<string | null>(null);
  const [selectedFiscalYear, setSelectedFiscalYear] = useState<number>(new Date().getFullYear());

  useEffect(() => {
    fetchCalendarData();
    fetchReports();
  }, [selectedDate]);

  const fetchCalendarData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/calendar/events`);
      const data = await res.json();
      if (data.status === 'ok') {
        setEvents(data.events || []);
        setSummary(data.summary);
      }
    } catch (error) {
      console.error('Error fetching calendar data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/calendar/reports`);
      const data = await res.json();
      if (data.status === 'ok') {
        setReports(data.reports || []);
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
    }
  };

  const generateReport = async (reportType: string, category: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/calendar/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_type: reportType, report_category: category }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        fetchReports();
      }
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  const createProjectFromEvent = async (calendarEventId: string) => {
    setCreatingProject(calendarEventId);
    try {
      const res = await fetch(`${API_BASE}/api/v2/calendar/events/${calendarEventId}/create-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (data.status === 'ok') {
        alert(`✅ Project created successfully!\n\nProject ID: ${data.project_id}\n${data.tasks_created} tasks created\n\nGo to Project Management to view details.`);
      } else {
        alert(`⚠️ ${data.message}`);
      }
    } catch (error) {
      console.error('Error creating project:', error);
      alert('Failed to create project from event');
    } finally {
      setCreatingProject(null);
    }
  };

  // Quarterly Projection View
  const renderQuarterlyView = () => {
    // Define fiscal quarters (Oct-Dec, Jan-Mar, Apr-Jun, Jul-Sep)
    const fiscalQuarters = [
      { name: 'Q1', label: 'Q1 (Oct-Dec)', months: [10, 11, 12], startMonth: 9, endMonth: 11 },
      { name: 'Q2', label: 'Q2 (Jan-Mar)', months: [1, 2, 3], startMonth: 0, endMonth: 2 },
      { name: 'Q3', label: 'Q3 (Apr-Jun)', months: [4, 5, 6], startMonth: 3, endMonth: 5 },
      { name: 'Q4', label: 'Q4 (Jul-Sep)', months: [7, 8, 9], startMonth: 6, endMonth: 8 },
    ];

    // Helper to check if date is in quarter
    const isInQuarter = (dateStr: string, quarter: typeof fiscalQuarters[0]) => {
      const date = new Date(dateStr);
      const month = date.getMonth();
      const year = date.getFullYear();
      
      if (quarter.name === 'Q1') {
        return (month >= 9 && year === selectedFiscalYear - 1) || (month <= 11 && year === selectedFiscalYear);
      }
      return month >= quarter.startMonth && month <= quarter.endMonth && year === selectedFiscalYear;
    };

    // Calculate quarter metrics
    const quarterMetrics = fiscalQuarters.map(quarter => {
      const quarterEvents = events.filter(e => isInQuarter(e.start_datetime, quarter));
      
      const byType = {
        event: quarterEvents.filter(e => e.event_type === 'event').length,
        marketing: quarterEvents.filter(e => e.event_type === 'marketing').length,
        meeting: quarterEvents.filter(e => e.event_type === 'meeting').length,
        training: quarterEvents.filter(e => e.event_type === 'training').length,
        deadline: quarterEvents.filter(e => e.event_type === 'deadline').length,
        report_due: quarterEvents.filter(e => e.event_type === 'report_due').length,
      };

      const byStatus = {
        scheduled: quarterEvents.filter(e => e.status === 'scheduled').length,
        in_progress: quarterEvents.filter(e => e.status === 'in_progress').length,
        completed: quarterEvents.filter(e => e.status === 'completed').length,
        cancelled: quarterEvents.filter(e => e.status === 'cancelled').length,
        postponed: quarterEvents.filter(e => e.status === 'postponed').length,
      };

      const byPriority = {
        critical: quarterEvents.filter(e => e.priority === 'critical').length,
        high: quarterEvents.filter(e => e.priority === 'high').length,
        medium: quarterEvents.filter(e => e.priority === 'medium').length,
        low: quarterEvents.filter(e => e.priority === 'low').length,
      };

      const completionRate = quarterEvents.length > 0 
        ? ((byStatus.completed / quarterEvents.length) * 100).toFixed(1)
        : '0.0';

      return {
        quarter,
        total: quarterEvents.length,
        byType,
        byStatus,
        byPriority,
        completionRate,
        events: quarterEvents,
      };
    });

    return (
      <div className="space-y-6">
        {/* Fiscal Year Selector */}
        <div className="flex items-center justify-between bg-white border-2 border-gray-300 p-4">
          <div>
            <h2 className="text-lg font-bold text-gray-800 uppercase tracking-wide">Quarterly Projection</h2>
            <p className="text-sm text-gray-600 mt-1">Events, Marketing, and Activities by Quarter</p>
          </div>
          <select
            value={selectedFiscalYear}
            onChange={(e) => setSelectedFiscalYear(Number(e.target.value))}
            className="px-4 py-2 border-2 border-gray-300 font-medium text-gray-800 uppercase"
          >
            <option value={new Date().getFullYear() - 1}>FY {new Date().getFullYear() - 1}</option>
            <option value={new Date().getFullYear()}>FY {new Date().getFullYear()}</option>
            <option value={new Date().getFullYear() + 1}>FY {new Date().getFullYear() + 1}</option>
          </select>
        </div>

        {/* Quarter Overview Cards */}
        <div className="grid grid-cols-4 gap-px bg-gray-300">
          {quarterMetrics.map((qm, idx) => (
            <div 
              key={qm.quarter.name}
              className={`p-6 ${idx % 2 === 0 ? 'bg-gradient-to-br from-gray-700 to-gray-800' : 'bg-gradient-to-br from-yellow-600 to-yellow-700'}`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-sm font-bold uppercase tracking-wide ${idx % 2 === 0 ? 'text-gray-300' : 'text-gray-800'}`}>
                  {qm.quarter.label}
                </h3>
                <span className={`text-3xl font-bold ${idx % 2 === 0 ? 'text-yellow-500' : 'text-black'}`}>
                  {qm.total}
                </span>
              </div>
              <div className={`text-xs uppercase tracking-wide ${idx % 2 === 0 ? 'text-gray-400' : 'text-gray-900'}`}>
                {qm.completionRate}% Complete
              </div>
              <div className="mt-3 h-2 bg-gray-900 w-full">
                <div
                  className={`h-full ${idx % 2 === 0 ? 'bg-yellow-500' : 'bg-black'}`}
                  style={{ width: `${qm.completionRate}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Detailed Quarter Breakdown */}
        {quarterMetrics.map((qm) => (
          <div key={qm.quarter.name} className="bg-white border-2 border-gray-300">
            <div className="bg-gray-100 px-6 py-4 border-b-2 border-gray-300">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide">
                  {qm.quarter.label} - {selectedFiscalYear} Detail
                </h3>
                <span className="text-sm font-bold text-gray-600">
                  {qm.total} Total Activities
                </span>
              </div>
            </div>

            <div className="p-6">
              {/* Status Distribution */}
              <div className="mb-6">
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">Status Breakdown</h4>
                <div className="grid grid-cols-5 gap-3">
                  {Object.entries(qm.byStatus).map(([status, count]) => (
                    <div key={status} className="border-2 border-gray-300 p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: STATUS_COLORS[status] }}
                        />
                        <span className="text-xl font-bold text-gray-800">{count}</span>
                      </div>
                      <p className="text-xs text-gray-600 uppercase tracking-wide">
                        {status.replace('_', ' ')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Type Distribution */}
              <div className="mb-6">
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">Activity Type Breakdown</h4>
                <div className="grid grid-cols-6 gap-3">
                  {Object.entries(qm.byType).map(([type, count]) => (
                    <div key={type} className="border-2 border-gray-300 p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: EVENT_TYPE_COLORS[type] }}
                        />
                        <span className="text-xl font-bold text-gray-800">{count}</span>
                      </div>
                      <p className="text-xs text-gray-600 uppercase tracking-wide">
                        {type.replace('_', ' ')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Priority Distribution */}
              <div className="mb-6">
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">Priority Levels</h4>
                <div className="grid grid-cols-4 gap-3">
                  {Object.entries(qm.byPriority).map(([priority, count]) => (
                    <div key={priority} className="border-2 border-gray-300 p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div
                          className="w-3 h-3"
                          style={{ backgroundColor: PRIORITY_COLORS[priority] }}
                        />
                        <span className="text-xl font-bold text-gray-800">{count}</span>
                      </div>
                      <p className="text-xs text-gray-600 uppercase tracking-wide">{priority}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Event Timeline for Quarter */}
              {qm.events.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wide mb-3">
                    Upcoming & Recent Activities ({qm.events.length})
                  </h4>
                  <div className="space-y-2">
                    {qm.events.slice(0, 8).map((event) => (
                      <div
                        key={event.event_id}
                        className="flex items-center justify-between p-3 border border-gray-200 hover:border-gray-400 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <div
                            className="w-1 h-12"
                            style={{ backgroundColor: EVENT_TYPE_COLORS[event.event_type] }}
                          />
                          <div className="flex-1">
                            <h5 className="font-semibold text-gray-800 text-sm">{event.title}</h5>
                            <div className="flex items-center gap-4 mt-1 text-xs text-gray-600">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(event.start_datetime).toLocaleDateString()}
                              </span>
                              <span className="uppercase tracking-wide">{event.event_type}</span>
                              {event.location && (
                                <span className="flex items-center gap-1">
                                  <Target className="w-3 h-3" />
                                  {event.location}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span
                            className="px-2 py-1 text-xs font-bold uppercase tracking-wide"
                            style={{
                              backgroundColor: PRIORITY_COLORS[event.priority] + '20',
                              color: PRIORITY_COLORS[event.priority],
                              border: `1px solid ${PRIORITY_COLORS[event.priority]}`,
                            }}
                          >
                            {event.priority}
                          </span>
                          <span
                            className="px-2 py-1 text-xs font-bold uppercase tracking-wide"
                            style={{
                              backgroundColor: STATUS_COLORS[event.status] + '20',
                              color: STATUS_COLORS[event.status],
                              border: `1px solid ${STATUS_COLORS[event.status]}`,
                            }}
                          >
                            {event.status}
                          </span>
                        </div>
                      </div>
                    ))}
                    {qm.events.length > 8 && (
                      <div className="text-center py-2 text-sm text-gray-600">
                        + {qm.events.length - 8} more activities this quarter
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return <div className="p-8 text-center">Loading calendar data...</div>;
  }

  const filteredEvents = events.filter((e) => {
    if (filterType !== 'all' && e.event_type !== filterType) return false;
    if (filterPriority !== 'all' && e.priority !== filterPriority) return false;
    return true;
  });

  // Calendar view helpers
  const currentMonth = selectedDate.getMonth();
  const currentYear = selectedDate.getFullYear();
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
  const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0);
  const daysInMonth = lastDayOfMonth.getDate();
  const startDayOfWeek = firstDayOfMonth.getDay();

  const calendarDays: (number | null)[] = [];
  for (let i = 0; i < startDayOfWeek; i++) {
    calendarDays.push(null);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(day);
  }

  const getEventsForDay = (day: number) => {
    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return filteredEvents.filter((e) => e.start_datetime.startsWith(dateStr));
  };

  const renderCalendarView = () => (
    <div className="bg-white rounded-xl shadow-md p-6">
      {/* Calendar Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          {selectedDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedDate(new Date(currentYear, currentMonth - 1, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => setSelectedDate(new Date())}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg"
          >
            Today
          </button>
          <button
            onClick={() => setSelectedDate(new Date(currentYear, currentMonth + 1, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div key={day} className="text-center font-semibold text-gray-600 py-2">
            {day}
          </div>
        ))}
        {calendarDays.map((day, idx) => {
          if (day === null) {
            return <div key={`empty-${idx}`} className="aspect-square" />;
          }
          const dayEvents = getEventsForDay(day);
          const isToday =
            day === new Date().getDate() &&
            currentMonth === new Date().getMonth() &&
            currentYear === new Date().getFullYear();

          return (
            <div
              key={day}
              className={`aspect-square border rounded-lg p-2 ${
                isToday ? 'bg-blue-50 border-blue-300' : 'border-gray-200'
              }`}
            >
              <div className={`text-sm font-medium mb-1 ${isToday ? 'text-blue-600' : 'text-gray-700'}`}>
                {day}
              </div>
              <div className="space-y-1">
                {dayEvents.slice(0, 3).map((event) => (
                  <div
                    key={event.event_id}
                    className="text-xs truncate px-1 py-0.5 rounded"
                    style={{ backgroundColor: EVENT_TYPE_COLORS[event.event_type] + '20' }}
                    title={event.title}
                  >
                    {event.title}
                  </div>
                ))}
                {dayEvents.length > 3 && (
                  <div className="text-xs text-gray-500">+{dayEvents.length - 3} more</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderListView = () => (
    <div className="space-y-4">
      {filteredEvents.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-8 text-center text-gray-500">
          No events found matching your filters
        </div>
      ) : (
        filteredEvents.map((event) => (
          <div key={event.event_id} className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: EVENT_TYPE_COLORS[event.event_type] }}
                  />
                  <h3 className="text-lg font-semibold text-gray-800">{event.title}</h3>
                  <span
                    className="px-2 py-1 text-xs font-medium rounded-full"
                    style={{
                      backgroundColor: PRIORITY_COLORS[event.priority] + '20',
                      color: PRIORITY_COLORS[event.priority],
                    }}
                  >
                    {event.priority}
                  </span>
                  <span
                    className="px-2 py-1 text-xs font-medium rounded-full"
                    style={{
                      backgroundColor: STATUS_COLORS[event.status] + '20',
                      color: STATUS_COLORS[event.status],
                    }}
                  >
                    {event.status}
                  </span>
                </div>
                <p className="text-gray-600 mb-3">{event.description}</p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2 text-gray-700">
                    <Clock className="w-4 h-4" />
                    {new Date(event.start_datetime).toLocaleString()}
                  </div>
                  {event.location && (
                    <div className="flex items-center gap-2 text-gray-700">
                      <Target className="w-4 h-4" />
                      {event.location}
                    </div>
                  )}
                  {event.rsid && (
                    <div className="text-gray-700">
                      <strong>RSID:</strong> {event.rsid}
                    </div>
                  )}
                  {event.brigade && (
                    <div className="text-gray-700">
                      <strong>Brigade:</strong> {event.brigade}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => createProjectFromEvent(event.event_id)}
                  disabled={creatingProject === event.event_id}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Create a project in Project Management from this calendar event"
                >
                  <Plus className="w-4 h-4" />
                  {creatingProject === event.event_id ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );

  const renderReportsView = () => (
    <div className="space-y-6">
      {/* Report Generation */}
      <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
        <h2 className="text-2xl font-bold mb-4">Generate Status Report</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {['daily', 'weekly', 'monthly', 'quarterly'].map((type) => (
            <button
              key={type}
              onClick={() => generateReport(type, 'overall')}
              className="px-4 py-3 bg-white/20 hover:bg-white/30 rounded-lg font-medium transition-colors"
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Recent Reports */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">Recent Status Reports</h2>
          <button
            onClick={fetchReports}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
        <div className="space-y-3">
          {reports.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No reports generated yet</p>
          ) : (
            reports.map((report) => (
              <div
                key={report.report_id}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <FileText className="w-5 h-5 text-blue-600" />
                      <h3 className="font-semibold text-gray-800">
                        {report.report_type.toUpperCase()} - {report.report_category}
                      </h3>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          report.status === 'completed'
                            ? 'bg-green-100 text-green-700'
                            : report.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {report.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{report.summary}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>
                        Period: {new Date(report.report_period_start).toLocaleDateString()} -{' '}
                        {new Date(report.report_period_end).toLocaleDateString()}
                      </span>
                      <span>Generated: {new Date(report.generated_date).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <button className="p-2 hover:bg-gray-200 rounded-lg">
                    <Download className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Calendar className="w-8 h-8 text-blue-600" />
            Calendar & Status Reports
          </h1>
          <p className="text-gray-600 mt-1">
            Schedule events • Track deadlines • Automate reports
          </p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Plus className="w-5 h-5" />
          New Event
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <Calendar className="w-8 h-8" />
              <span className="text-2xl font-bold">{summary.total_events}</span>
            </div>
            <p className="text-blue-100">Total Events</p>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-8 h-8" />
              <span className="text-2xl font-bold">{summary.upcoming_events}</span>
            </div>
            <p className="text-green-100">Upcoming Events</p>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle2 className="w-8 h-8" />
              <span className="text-2xl font-bold">{summary.completed_events}</span>
            </div>
            <p className="text-purple-100">Completed</p>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <AlertCircle className="w-8 h-8" />
              <span className="text-2xl font-bold">{summary.overdue_events}</span>
            </div>
            <p className="text-orange-100">Overdue</p>
          </div>
        </div>
      )}

      {/* View Mode Tabs */}
      <div className="flex items-center gap-4 border-b border-gray-200">
        <button
          onClick={() => setViewMode('calendar')}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === 'calendar'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Calendar View
        </button>
        <button
          onClick={() => setViewMode('list')}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === 'list'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          List View
        </button>
        <button
          onClick={() => setViewMode('quarterly')}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === 'quarterly'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Quarterly Projection
        </button>
        <button
          onClick={() => setViewMode('reports')}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === 'reports'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Status Reports
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          >
            <option value="all">All Types</option>
            <option value="event">Events</option>
            <option value="marketing">Marketing</option>
            <option value="meeting">Meetings</option>
            <option value="deadline">Deadlines</option>
            <option value="training">Training</option>
            <option value="report_due">Reports Due</option>
          </select>
        </div>
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg"
        >
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Content based on view mode */}
      {viewMode === 'calendar' && renderCalendarView()}
      {viewMode === 'list' && renderListView()}
      {viewMode === 'quarterly' && renderQuarterlyView()}
      {viewMode === 'reports' && renderReportsView()}
    </div>
  );
};
