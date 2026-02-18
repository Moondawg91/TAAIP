import React, { useState, useEffect } from 'react';
import {
  Target, Calendar, Users, FileText, CheckSquare, TrendingUp, 
  MapPin, DollarSign, AlertCircle, Clock, ChevronRight, Filter,
  Download, Upload, Eye, Edit, CheckCircle, XCircle, Plus, Save, X
} from 'lucide-react';

interface TWGMeeting {
  meeting_id: string;
  date: string;
  quarter: string;
  status: 'scheduled' | 'in_progress' | 'completed';
  xo_chair: string;
  attendees: {
    xo: boolean;
    tawo: boolean;
    s2_mma: boolean;
    s3: boolean;
    s4: boolean;
    ess: boolean;
    apa: boolean;
    co_leadership: string[];
  };
  agenda_items: AgendaItem[];
}

interface AgendaItem {
  id: string;
  section: string;
  presenter: string;
  status: 'pending' | 'in_progress' | 'completed';
  notes?: string;
}

interface AARReport {
  event_id: string;
  event_name: string;
  date: string;
  status: 'complete' | 'incomplete' | 'overdue';
  due_date: string;
  hours_since_event: number;
  submitted_by?: string;
}

interface TargetingPhase {
  phase: 'Q-1' | 'Q+0' | 'Q+1' | 'Q+2' | 'Q+3' | 'Q+4';
  name: string;
  description: string;
  events: TargetEvent[];
}

interface TargetEvent {
  event_id: string;
  name: string;
  date: string;
  location: string;
  type: 'event_targeting' | 'geographic_targeting';
  target_audience: string;
  zipcode?: string;
  school?: string;
  expected_leads: number;
  budget: number;
  status: string;
  priority: 'must_keep' | 'must_win' | 'standard';
}

interface MarketingBudget {
  fy: number;
  total_budget: number;
  allocated: number;
  spent: number;
  remaining: number;
  by_quarter: {
    q1: number;
    q2: number;
    q3: number;
    q4: number;
  };
}

export const TargetingWorkingGroup: React.FC = () => {
  const [currentMeeting, setCurrentMeeting] = useState<TWGMeeting | null>(null);
  const [aarReports, setAARReports] = useState<AARReport[]>([]);
  const [targetingPhases, setTargetingPhases] = useState<TargetingPhase[]>([]);
  const [marketingBudget, setMarketingBudget] = useState<MarketingBudget | null>(null);
  const [selectedQuarter, setSelectedQuarter] = useState<string>('Q+0');
  const [viewMode, setViewMode] = useState<'dashboard' | 'agenda' | 'sync-matrix' | 'intel' | 'recommendations'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [showAddEventModal, setShowAddEventModal] = useState(false);
  const [showAddRecommendationModal, setShowAddRecommendationModal] = useState(false);
  
  // Detail modal states
  const [showAARDetailModal, setShowAARDetailModal] = useState(false);
  const [showBudgetDetailModal, setShowBudgetDetailModal] = useState(false);
  const [showEventsDetailModal, setShowEventsDetailModal] = useState(false);
  const [showTargetsDetailModal, setShowTargetsDetailModal] = useState(false);
  const [showAgendaDetailModal, setShowAgendaDetailModal] = useState(false);
  const [selectedAgendaItem, setSelectedAgendaItem] = useState<AgendaItem | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TargetEvent | null>(null);
  
  const [newEvent, setNewEvent] = useState<Partial<TargetEvent>>({
    name: '',
    date: '',
    location: '',
    type: 'event_targeting',
    target_audience: '',
    expected_leads: 0,
    budget: 0,
    status: 'planned',
    priority: 'standard'
  });

  useEffect(() => {
    loadTWGData();
  }, []);

  const loadTWGData = async () => {
    setLoading(true);
    try {
      // Load TWG meeting data, AAR reports, targeting phases, budget
      // Mock data for now
      setCurrentMeeting({
        meeting_id: 'twg_2025_01',
        date: '2025-01-03',
        quarter: 'Q2 FY25',
        status: 'scheduled',
        xo_chair: 'MAJ Smith',
        attendees: {
          xo: true,
          tawo: true,
          s2_mma: true,
          s3: true,
          s4: true,
          ess: true,
          apa: true,
          co_leadership: ['CPT Johnson', 'CPT Williams', 'CPT Davis']
        },
        agenda_items: [
          {
            id: 'agenda_1',
            section: 'Previous QTR Overview',
            presenter: 'S2',
            status: 'pending'
          },
          {
            id: 'agenda_2',
            section: 'AAR Due Dates Review',
            presenter: 'XO',
            status: 'pending'
          },
          {
            id: 'agenda_3',
            section: 'MEB Approved Asset Schedule',
            presenter: 'S3',
            status: 'pending'
          },
          {
            id: 'agenda_4',
            section: 'FY Marketing Budget',
            presenter: 'AP&A',
            status: 'pending'
          },
          {
            id: 'agenda_5',
            section: 'Commander Guidance',
            presenter: 'TAWO',
            status: 'pending'
          },
          {
            id: 'agenda_6',
            section: 'Intel Update',
            presenter: 'S2, ESS, A&PA, CO CDRs',
            status: 'pending'
          },
          {
            id: 'agenda_7',
            section: 'Assess (Q-1) - Last Quarter Metrics',
            presenter: 'S2/MMA',
            status: 'pending'
          },
          {
            id: 'agenda_8',
            section: 'Execute (Q+0) - Current Quarter Events',
            presenter: 'S3',
            status: 'pending'
          },
          {
            id: 'agenda_9',
            section: 'Review (Q+1) - Next Quarter Planning',
            presenter: 'TAWO',
            status: 'pending'
          },
          {
            id: 'agenda_10',
            section: 'Validate (Q+2) - Resources & Assets',
            presenter: 'S3/S4',
            status: 'pending'
          },
          {
            id: 'agenda_11',
            section: 'Approve (Q+3) - Future Quarter Authorization',
            presenter: 'XO',
            status: 'pending'
          },
          {
            id: 'agenda_12',
            section: 'S2/MMA Brief - High Payoff Areas',
            presenter: 'S2/MMA',
            status: 'pending'
          },
          {
            id: 'agenda_13',
            section: 'Company Slides & Strategy',
            presenter: 'CO Leadership',
            status: 'pending'
          },
          {
            id: 'agenda_14',
            section: 'Guidance (Q+4) - Long Range Planning',
            presenter: 'TAWO',
            status: 'pending'
          }
        ]
      });

      setAARReports([
        {
          event_id: 'evt_001',
          event_name: 'College Football Game - State University',
          date: '2024-11-15',
          status: 'complete',
          due_date: '2024-11-18',
          hours_since_event: 72,
          submitted_by: 'SSG Martinez'
        },
        {
          event_id: 'evt_002',
          event_name: 'High School Career Fair',
          date: '2024-11-16',
          status: 'incomplete',
          due_date: '2024-11-19',
          hours_since_event: 68
        },
        {
          event_id: 'evt_003',
          event_name: 'Community Outreach Event',
          date: '2024-11-12',
          status: 'overdue',
          due_date: '2024-11-15',
          hours_since_event: 168
        }
      ]);

      setMarketingBudget({
        fy: 2025,
        total_budget: 850000,
        allocated: 720000,
        spent: 520000,
        remaining: 330000,
        by_quarter: {
          q1: 210000,
          q2: 215000,
          q3: 220000,
          q4: 205000
        }
      });

    } catch (error) {
      console.error('Error loading TWG data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Detail modal handlers
  const handleAARClick = () => {
    setShowAARDetailModal(true);
  };

  const handleBudgetClick = () => {
    setShowBudgetDetailModal(true);
  };

  const handleEventsClick = () => {
    setShowEventsDetailModal(true);
  };

  const handleTargetsClick = () => {
    setShowTargetsDetailModal(true);
  };

  const handleAgendaItemClick = (item: AgendaItem) => {
    setSelectedAgendaItem(item);
    setShowAgendaDetailModal(true);
  };

  const handleEventClick = (event: TargetEvent) => {
    setSelectedEvent(event);
    setShowAddEventModal(true);
    setNewEvent(event);
  };

  const handleAddEvent = () => {
    const event: TargetEvent = {
      event_id: `EVT${Date.now()}`,
      name: newEvent.name || 'New Event',
      date: newEvent.date || new Date().toISOString().split('T')[0],
      location: newEvent.location || '',
      type: newEvent.type || 'event_targeting',
      target_audience: newEvent.target_audience || '',
      expected_leads: newEvent.expected_leads || 0,
      budget: newEvent.budget || 0,
      status: newEvent.status || 'planned',
      priority: newEvent.priority || 'standard'
    };
    
    setTargetingPhases(prev => {
      const phases = [...prev];
      const currentPhase = phases.find(p => p.phase === 'Q+0');
      if (currentPhase) {
        currentPhase.events.push(event);
      }
      return phases;
    });
    
    setShowAddEventModal(false);
    setSelectedEvent(null);
    setNewEvent({
      name: '',
      date: '',
      location: '',
      type: 'event_targeting',
      target_audience: '',
      expected_leads: 0,
      budget: 0,
      status: 'planned',
      priority: 'standard'
    });
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      complete: 'bg-green-100 text-green-800',
      incomplete: 'bg-yellow-100 text-yellow-800',
      overdue: 'bg-red-100 text-red-800',
      scheduled: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-orange-100 text-orange-800',
      completed: 'bg-green-100 text-green-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      must_keep: 'bg-red-100 text-red-800 border-2 border-red-600',
      must_win: 'bg-orange-100 text-orange-800 border-2 border-orange-600',
      standard: 'bg-blue-100 text-blue-800'
    };
    const labels = {
      must_keep: 'MUST KEEP',
      must_win: 'MUST WIN',
      standard: 'STANDARD'
    };
    return { color: colors[priority as keyof typeof colors], label: labels[priority as keyof typeof labels] };
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-xl shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold uppercase tracking-wider flex items-center gap-3">
              <Target className="w-8 h-8 text-yellow-500" />
              Targeting Working Group (TWG)
            </h1>
            <p className="text-gray-300 mt-2">XO-Chaired Monthly Coordination | MDMP Targeting Strategy</p>
            <div className="flex items-center gap-6 mt-3 text-sm">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-yellow-500" />
                <span>Next Meeting: First Friday | 90 Minutes | MS Teams</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-yellow-500" />
                <span>Duration: 90 Minutes</span>
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setViewMode('dashboard')}
              className={`px-4 py-2 rounded-lg font-semibold ${
                viewMode === 'dashboard' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-white hover:bg-gray-600'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setViewMode('agenda')}
              className={`px-4 py-2 rounded-lg font-semibold ${
                viewMode === 'agenda' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-white hover:bg-gray-600'
              }`}
            >
              Agenda
            </button>
            <button
              onClick={() => setViewMode('sync-matrix')}
              className={`px-4 py-2 rounded-lg font-semibold ${
                viewMode === 'sync-matrix' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-white hover:bg-gray-600'
              }`}
            >
              Sync Matrix
            </button>
            <button
              onClick={() => setViewMode('intel')}
              className={`px-4 py-2 rounded-lg font-semibold ${
                viewMode === 'intel' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-white hover:bg-gray-600'
              }`}
            >
              Intel Brief
            </button>
            <button
              onClick={() => setViewMode('recommendations')}
              className={`px-4 py-2 rounded-lg font-semibold ${
                viewMode === 'recommendations' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-white hover:bg-gray-600'
              }`}
            >
              Recommendations
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard View */}
      {viewMode === 'dashboard' && (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div 
              onClick={handleAARClick}
              className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm uppercase font-semibold">AAR Overdue</p>
                  <p className="text-3xl font-bold text-red-600 mt-2">
                    {aarReports.filter(r => r.status === 'overdue').length}
                  </p>
                </div>
                <AlertCircle className="w-8 h-8 text-red-600" />
              </div>
            </div>

            <div 
              onClick={handleBudgetClick}
              className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm uppercase font-semibold">Budget Remaining</p>
                  <p className="text-3xl font-bold text-green-600 mt-2">
                    ${marketingBudget ? (marketingBudget.remaining / 1000).toFixed(0) : 0}K
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-green-600" />
              </div>
            </div>

            <div 
              onClick={handleEventsClick}
              className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm uppercase font-semibold">Active Events</p>
                  <p className="text-3xl font-bold text-blue-600 mt-2">24</p>
                </div>
                <Calendar className="w-8 h-8 text-blue-600" />
              </div>
            </div>

            <div 
              onClick={handleTargetsClick}
              className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm uppercase font-semibold">Must Win Targets</p>
                  <p className="text-3xl font-bold text-orange-600 mt-2">8</p>
                </div>
                <Target className="w-8 h-8 text-orange-600" />
              </div>
            </div>
          </div>

          {/* AAR Status */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="bg-gray-100 px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <FileText className="w-6 h-6" />
                AAR Due Dates / Status (72hrs Post-Event)
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Event</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Event Date</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Due Date</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Hours Since</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Submitted By</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {aarReports.map((aar) => (
                    <tr 
                      key={aar.event_id} 
                      onClick={() => handleAARClick()}
                      className="hover:bg-gray-50 cursor-pointer"
                    >
                      <td className="px-6 py-4 font-semibold text-gray-900">{aar.event_name}</td>
                      <td className="px-6 py-4 text-gray-600">{aar.date}</td>
                      <td className="px-6 py-4 text-gray-600">{aar.due_date}</td>
                      <td className="px-6 py-4">
                        <span className={`font-semibold ${aar.hours_since_event > 72 ? 'text-red-600' : 'text-gray-900'}`}>
                          {aar.hours_since_event}h
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(aar.status)}`}>
                          {aar.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-600">{aar.submitted_by || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Marketing Budget */}
          {marketingBudget && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <DollarSign className="w-6 h-6" />
                FY {marketingBudget.fy} Marketing Budget
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-blue-600 text-sm font-semibold">Total Budget</p>
                  <p className="text-2xl font-bold text-blue-900 mt-2">
                    ${(marketingBudget.total_budget / 1000).toFixed(0)}K
                  </p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-green-600 text-sm font-semibold">Allocated</p>
                  <p className="text-2xl font-bold text-green-900 mt-2">
                    ${(marketingBudget.allocated / 1000).toFixed(0)}K
                  </p>
                </div>
                <div className="bg-red-50 rounded-lg p-4">
                  <p className="text-red-600 text-sm font-semibold">Spent</p>
                  <p className="text-2xl font-bold text-red-900 mt-2">
                    ${(marketingBudget.spent / 1000).toFixed(0)}K
                  </p>
                </div>
                <div className="bg-yellow-50 rounded-lg p-4">
                  <p className="text-yellow-600 text-sm font-semibold">Remaining</p>
                  <p className="text-2xl font-bold text-yellow-900 mt-2">
                    ${(marketingBudget.remaining / 1000).toFixed(0)}K
                  </p>
                </div>
              </div>
              <div className="mt-4 bg-gray-100 rounded-lg p-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">Quarterly Allocation</p>
                <div className="grid grid-cols-4 gap-2">
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Q1</p>
                    <p className="font-bold text-gray-900">${(marketingBudget.by_quarter.q1 / 1000).toFixed(0)}K</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Q2</p>
                    <p className="font-bold text-gray-900">${(marketingBudget.by_quarter.q2 / 1000).toFixed(0)}K</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Q3</p>
                    <p className="font-bold text-gray-900">${(marketingBudget.by_quarter.q3 / 1000).toFixed(0)}K</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Q4</p>
                    <p className="font-bold text-gray-900">${(marketingBudget.by_quarter.q4 / 1000).toFixed(0)}K</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Agenda View */}
      {viewMode === 'agenda' && currentMeeting && (
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="bg-gray-100 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">TWG Meeting Agenda</h2>
            <p className="text-sm text-gray-600 mt-1">
              {currentMeeting.date} | {currentMeeting.quarter} | Chaired by: {currentMeeting.xo_chair}
            </p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {currentMeeting.agenda_items.map((item, index) => (
                <div key={item.id} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-500 text-black rounded-full flex items-center justify-center font-bold">
                      {index + 1}
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 text-lg">{item.section}</h3>
                    <p className="text-sm text-gray-600 mt-1">Presenter: {item.presenter}</p>
                    {item.section.includes('Assess') && (
                      <p className="text-sm text-gray-700 mt-2 italic">Review last quarter's event metrics and performance</p>
                    )}
                    {item.section.includes('Execute') && (
                      <p className="text-sm text-gray-700 mt-2 italic">Target Sync Matrix displaying current quarter events with dynamic requests</p>
                    )}
                    {item.section.includes('Review (Q+1)') && (
                      <p className="text-sm text-gray-700 mt-2 italic">Target Sync Matrix for events one quarter out</p>
                    )}
                    {item.section.includes('Validate (Q+2)') && (
                      <p className="text-sm text-gray-700 mt-2 italic">Target Sync Matrix validation for assets, funding, and resources two quarters out</p>
                    )}
                    {item.section.includes('Approve (Q+3)') && (
                      <p className="text-sm text-gray-700 mt-2 italic">Authorization and approval for events three quarters out</p>
                    )}
                    {item.section.includes('S2/MMA Brief') && (
                      <p className="text-sm text-gray-700 mt-2 italic">High payoff zip codes and high payoff segments analysis</p>
                    )}
                    {item.section.includes('Company Slides') && (
                      <p className="text-sm text-gray-700 mt-2 italic">
                        <strong>Company Slides utilize D3A methodology</strong> to clearly present specific intelligence, ensuring information accurately reflects ground observations. This deliberate presentation helps BN leadership grasp the real-time operational picture.<br/><br/>
                        <strong>Q+3 D3A Framework (Approve Phase):</strong><br/>
                        • <strong>Decide:</strong> Identify future strategic targets. <em>(Q+3 target segments and specific target audience)</em><br/>
                        • <strong>Detect:</strong> Identify the operational landscape and opportunities. <em>(Q+3 events, schools, COIs (Centers of Influence), and other key elements)</em><br/>
                        • <strong>Deliver:</strong> Outline required resources for execution. <em>(Q+3 resource needs including personnel, assets, PPI/RPI, and funding)</em><br/>
                        • <strong>Assess:</strong> Provide the initial plan for measuring effectiveness. <em>(Initial assessment plans for Q+3 operations)</em><br/><br/>
                        Includes crucial tasks of <strong>recommending necessary changes and updating the synchronization matrix</strong> to reflect latest decisions.
                      </p>
                    )}
                    {item.section.includes('Guidance (Q+4)') && (
                      <p className="text-sm text-gray-700 mt-2 italic">Assess market intelligence, events, and marketing strategy proposals</p>
                    )}
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(item.status)}`}>
                    {item.status.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>

            {/* Mandatory Attendees */}
            <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-600 rounded">
              <h3 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Mandatory Attendees
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>XO (Chair)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>TAWO</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>S2 (MMA)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>S3</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>S4</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>ESS</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>A&PA Chief</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>CO Leadership</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sync Matrix View */}
      {viewMode === 'sync-matrix' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Target Synchronization Matrix</h2>
              <div className="flex gap-2">
                {['Q-1', 'Q+0', 'Q+1', 'Q+2', 'Q+3', 'Q+4'].map((q) => (
                  <button
                    key={q}
                    onClick={() => setSelectedQuarter(q)}
                    className={`px-3 py-1 rounded-lg font-semibold text-sm ${
                      selectedQuarter === q
                        ? 'bg-yellow-500 text-black'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded mb-6">
              <h3 className="font-bold text-blue-900 mb-2">
                {selectedQuarter === 'Q-1' && 'ASSESS: Last Quarter Review'}
                {selectedQuarter === 'Q+0' && 'EXECUTE: Current Quarter Events'}
                {selectedQuarter === 'Q+1' && 'REVIEW: Next Quarter Planning'}
                {selectedQuarter === 'Q+2' && 'VALIDATE: Resource Confirmation'}
                {selectedQuarter === 'Q+3' && 'APPROVE: Future Authorization'}
                {selectedQuarter === 'Q+4' && 'GUIDANCE: Long-Range Strategy'}
              </h3>
              <p className="text-sm text-blue-800">
                {selectedQuarter === 'Q-1' && 'Review last quarter\'s event metrics, outcomes, and lessons learned'}
                {selectedQuarter === 'Q+0' && 'Dynamic request tracking for events currently in execution'}
                {selectedQuarter === 'Q+1' && 'Planning and coordination for events one quarter out'}
                {selectedQuarter === 'Q+2' && 'Validate assets, funding, and resources for events two quarters out'}
                {selectedQuarter === 'Q+3' && 'Approve and authorize events three quarters in advance'}
                {selectedQuarter === 'Q+4' && 'Assess market intelligence and propose marketing strategy'}
              </p>
            </div>

            {/* Targeting Types Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="bg-purple-50 border-l-4 border-purple-600 p-4 rounded">
                <h3 className="font-bold text-purple-900 mb-2 flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Event Targeting
                </h3>
                <p className="text-sm text-purple-800">
                  Best events with quality leads - people genuinely interested. Track via sync matrix: 
                  event coverage, learnings, effectiveness optimization.
                </p>
              </div>
              <div className="bg-green-50 border-l-4 border-green-600 p-4 rounded">
                <h3 className="font-bold text-green-900 mb-2 flex items-center gap-2">
                  <MapPin className="w-5 h-5" />
                  Geographic Targeting
                </h3>
                <p className="text-sm text-green-800">
                  Exact schools, neighborhoods, platforms for max potential. Identify "Must Keep/Must Win" 
                  areas - top performers and conquest targets.
                </p>
              </div>
            </div>

            {/* Sample Events Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase">Event</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase">Location</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase">Priority</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase">Expected Leads</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase">Budget</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr 
                    onClick={() => handleEventClick({
                      event_id: 'EVT001',
                      name: 'State University Football Game',
                      date: '2025-02-15',
                      location: 'University Stadium',
                      type: 'event_targeting',
                      target_audience: 'College students, families',
                      expected_leads: 45,
                      budget: 12500,
                      status: 'planned',
                      priority: 'must_win'
                    })}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-4 py-3 font-semibold text-gray-900">State University Football Game</td>
                    <td className="px-4 py-3 text-gray-600">2025-02-15</td>
                    <td className="px-4 py-3 text-gray-600">University Stadium</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-semibold">
                        Event Targeting
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${getPriorityBadge('must_win').color}`}>
                        {getPriorityBadge('must_win').label}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-semibold text-blue-600">45</td>
                    <td className="px-4 py-3 font-semibold text-green-600">$12,500</td>
                  </tr>
                  <tr 
                    onClick={() => handleEventClick({
                      event_id: 'EVT002',
                      name: 'Lincoln High School Visit',
                      date: '2025-02-20',
                      location: 'Lincoln HS (ZIP: 28301)',
                      type: 'geographic_targeting',
                      target_audience: 'High school students',
                      expected_leads: 30,
                      budget: 3200,
                      status: 'planned',
                      priority: 'must_keep'
                    })}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="px-4 py-3 font-semibold text-gray-900">Lincoln High School Visit</td>
                    <td className="px-4 py-3 text-gray-600">2025-02-20</td>
                    <td className="px-4 py-3 text-gray-600">Lincoln HS (ZIP: 28301)</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                        Geographic Targeting
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${getPriorityBadge('must_keep').color}`}>
                        {getPriorityBadge('must_keep').label}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-semibold text-blue-600">30</td>
                    <td className="px-4 py-3 font-semibold text-green-600">$3,200</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Intel Brief View */}
      {viewMode === 'intel' && (
        <div className="space-y-6">
          {/* Houston BN Focus Events */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Target className="w-7 h-7 text-yellow-400" />
                Houston Recruiting BN - Priority Events
              </h2>
              <button
                onClick={() => setShowAddEventModal(true)}
                className="bg-yellow-500 text-black px-4 py-2 rounded-lg font-semibold hover:bg-yellow-400 flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Add Event
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div 
                onClick={() => handleEventClick({
                  event_id: 'EVT_EXPO',
                  name: 'Youth Career Expo',
                  date: '2025-03-10',
                  location: 'Houston Convention Center',
                  type: 'event_targeting',
                  target_audience: 'High school and college students',
                  expected_leads: 120,
                  budget: 15000,
                  status: 'planned',
                  priority: 'must_win'
                })}
                className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20 cursor-pointer hover:bg-white/20 transition-colors"
              >
                <h3 className="font-bold text-yellow-400 mb-2">Youth Career Expo</h3>
                <p className="text-sm text-blue-100">High-impact youth engagement opportunity</p>
              </div>
              <div 
                onClick={() => handleEventClick({
                  event_id: 'EVT_WESTBROOK',
                  name: 'Westbrook HS Career Fair',
                  date: '2025-03-18',
                  location: 'Westbrook High School',
                  type: 'geographic_targeting',
                  target_audience: 'High school seniors',
                  expected_leads: 65,
                  budget: 4500,
                  status: 'planned',
                  priority: 'must_keep'
                })}
                className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20 cursor-pointer hover:bg-white/20 transition-colors"
              >
                <h3 className="font-bold text-yellow-400 mb-2">Westbrook HS Career Fair</h3>
                <p className="text-sm text-blue-100">Targeted high school recruitment event</p>
              </div>
              <div 
                onClick={() => handleEventClick({
                  event_id: 'EVT_RODEO',
                  name: 'Walker County Fair & Rodeo',
                  date: '2025-04-05',
                  location: 'Walker County Fairgrounds',
                  type: 'event_targeting',
                  target_audience: 'Community families',
                  expected_leads: 90,
                  budget: 8500,
                  status: 'planned',
                  priority: 'standard'
                })}
                className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20 cursor-pointer hover:bg-white/20 transition-colors"
              >
                <h3 className="font-bold text-yellow-400 mb-2">Walker County Fair & Rodeo</h3>
                <p className="text-sm text-blue-100">Community engagement - Exhibit space</p>
              </div>
            </div>
          </div>

          {/* Phase Breakdown */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="w-7 h-7 text-blue-600" />
              Phase Breakdown (Q-1 to Q+4)
            </h2>
            <p className="text-gray-600 mb-6">Process structured across calendar quarters, each with corresponding primary action</p>
            
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-4 py-3 text-left font-bold text-gray-800 border">Phase</th>
                    <th className="px-4 py-3 text-left font-bold text-gray-800 border">Months</th>
                    <th className="px-4 py-3 text-left font-bold text-gray-800 border">Primary Action</th>
                    <th className="px-4 py-3 text-left font-bold text-gray-800 border">Key Tasks</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="bg-gray-50">
                    <td className="px-4 py-3 font-bold border">Q-1</td>
                    <td className="px-4 py-3 border"><span className="text-gray-500">JAN FEB MAR</span></td>
                    <td className="px-4 py-3 font-bold text-blue-700 border">Assess</td>
                    <td className="px-4 py-3 text-sm border">
                      • Previous QTR Event Assessment<br/>
                      • Key takeaways<br/>
                      • Review AAR<br/>
                      • Qual/Quantitative Analysis
                    </td>
                  </tr>
                  <tr className="bg-gray-900 text-white">
                    <td className="px-4 py-3 font-bold border border-gray-700">Q+0</td>
                    <td className="px-4 py-3 border border-gray-700">APR MAY JUN</td>
                    <td className="px-4 py-3 font-bold text-yellow-400 border border-gray-700">Execute</td>
                    <td className="px-4 py-3 text-sm border border-gray-700">
                      • Approve/Deny Dynamic Target Request
                    </td>
                  </tr>
                  <tr className="bg-green-50">
                    <td className="px-4 py-3 font-bold border">Q+1</td>
                    <td className="px-4 py-3 border"><span className="text-green-700">JUL AUG SEP</span></td>
                    <td className="px-4 py-3 font-bold text-green-700 border">Review</td>
                    <td className="px-4 py-3 text-sm border">
                      • Review Q+1 events<br/>
                      • Identify issues<br/>
                      • Propose changes as required
                    </td>
                  </tr>
                  <tr className="bg-yellow-50">
                    <td className="px-4 py-3 font-bold border">Q+2</td>
                    <td className="px-4 py-3 border"><span className="text-yellow-700">OCT NOV DEC</span></td>
                    <td className="px-4 py-3 font-bold text-yellow-700 border">Validate</td>
                    <td className="px-4 py-3 text-sm border">
                      • Validate Q+2 events, RFIs<br/>
                      • Validate resources<br/>
                      • Refine coordinating instructions
                    </td>
                  </tr>
                  <tr className="bg-red-50">
                    <td className="px-4 py-3 font-bold border">Q+3</td>
                    <td className="px-4 py-3 border"><span className="text-red-700">JAN FEB MAR</span></td>
                    <td className="px-4 py-3 font-bold text-red-700 border">Approve</td>
                    <td className="px-4 py-3 text-sm border">
                      • Approve/Deny target nomination<br/>
                      • Recommend changes<br/>
                      • Update Synch Matrix
                    </td>
                  </tr>
                  <tr className="bg-blue-50">
                    <td className="px-4 py-3 font-bold border">Q+4</td>
                    <td className="px-4 py-3 border"><span className="text-blue-700">APR MAY JUN</span></td>
                    <td className="px-4 py-3 font-bold text-blue-700 border">Guidance</td>
                    <td className="px-4 py-3 text-sm border">
                      • Q+4 Intel update<br/>
                      • Propose Q+4 events and targeting guidance for CDR Approval
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Targeting Process Workflow */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <TrendingUp className="w-7 h-7 text-purple-600" />
              Targeting Process Workflow
            </h2>
            <p className="text-gray-600 mb-6">Central cycle: <strong className="text-purple-700">DECIDE → DETECT → DELIVER → ASSESS</strong></p>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* TWG */}
              <div className="bg-gradient-to-br from-purple-50 to-white border-2 border-purple-300 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-purple-600 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold">1</div>
                  <div>
                    <h3 className="font-bold text-lg text-purple-900">TARGETING WORKING GROUP (TWG)</h3>
                    <p className="text-sm text-purple-700">Feeds into: <strong>Decide Phase</strong></p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Input:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Commander's guidance</li>
                      <li>• Market analysis (HP segments and Zips)</li>
                      <li>• School analysis & access data</li>
                      <li>• Sync matrix</li>
                      <li>• COI/CP identification</li>
                      <li>• Resource & funding analysis</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Output:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Companies draft nominations (events, COIs, assets, TAIR)</li>
                      <li>• Messaging themes</li>
                      <li>• Draft CONOPs</li>
                      <li>• Refined list of potential HP segments, Zips, schools</li>
                    </ul>
                  </div>
                  <div className="bg-purple-100 rounded p-2 mt-3">
                    <p className="text-xs font-bold text-purple-900">Definition: Where we build & nominate</p>
                  </div>
                </div>
              </div>

              {/* TDB */}
              <div className="bg-gradient-to-br from-blue-50 to-white border-2 border-blue-300 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold">2</div>
                  <div>
                    <h3 className="font-bold text-lg text-blue-900">TARGETING DECISION BOARD (TDB)</h3>
                    <p className="text-sm text-blue-700">Feeds into: <strong>Detect Phase</strong></p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Input:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Nominations from TWG</li>
                      <li>• Initial CONOPs</li>
                      <li>• Updated IPOE / Market Analysis</li>
                      <li>• Resource and Funding Requirements</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Output:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Approved nominations</li>
                      <li>• Approved resources</li>
                      <li>• Tasking for companies and staff sections</li>
                      <li>• Sync Matrix</li>
                    </ul>
                  </div>
                  <div className="bg-blue-100 rounded p-2 mt-3">
                    <p className="text-xs font-bold text-blue-900">Definition: Where we approve</p>
                  </div>
                </div>
              </div>

              {/* TARGETING SYNC */}
              <div className="bg-gradient-to-br from-green-50 to-white border-2 border-green-300 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-green-600 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold">3</div>
                  <div>
                    <h3 className="font-bold text-lg text-green-900">TARGETING SYNC</h3>
                    <p className="text-sm text-green-700">Feeds into: <strong>Deliver Phase</strong></p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Input:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Approved events and CONOPs</li>
                      <li>• Market analysis updates</li>
                      <li>• Fusion cell validation and coordination</li>
                      <li>• Xchecks with NCOICs and SCs</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Output:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Refined CONOPs (Rehearsals, responsibilities)</li>
                      <li>• BN sync matrix update</li>
                      <li>• Updated BN calendar with approved events</li>
                      <li>• MACs assigned to event (verified)</li>
                    </ul>
                  </div>
                  <div className="bg-green-100 rounded p-2 mt-3">
                    <p className="text-xs font-bold text-green-900">Definition: Where we refine & finalize execution</p>
                  </div>
                </div>
              </div>

              {/* ASSESSMENT WG */}
              <div className="bg-gradient-to-br from-orange-50 to-white border-2 border-orange-300 rounded-lg p-5">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-orange-600 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold">4</div>
                  <div>
                    <h3 className="font-bold text-lg text-orange-900">TARGETING ASSESSMENT WG</h3>
                    <p className="text-sm text-orange-700">Feeds into: <strong>Assess Phase</strong></p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Input:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• Company After Action Reviews</li>
                      <li>• ROI metrics (Impressions, engagement, leads)</li>
                      <li>• RZ data</li>
                      <li>• EMM data</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-800 mb-1">Output:</p>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• ROI rollups</li>
                      <li>• Lessons learned & best practices</li>
                      <li>• Identified shortfalls and recommendations</li>
                      <li>• Adjusted targeting guidance for next TWG cycle</li>
                    </ul>
                  </div>
                  <div className="bg-orange-100 rounded p-2 mt-3">
                    <p className="text-xs font-bold text-orange-900">Definition: Where we measure performance</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations View */}
      {viewMode === 'recommendations' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <TrendingUp className="w-7 h-7 text-purple-600" />
                  TWG Recommendations & Action Items
                </h2>
                <p className="text-gray-600 mt-2">Data-driven recommendations for the Targeting Working Group based on current performance and market intelligence</p>
              </div>
              <button
                onClick={() => setShowAddRecommendationModal(true)}
                className="bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Add Recommendation
              </button>
            </div>
            
            {/* Strategic Recommendations */}
            <div className="space-y-4 mb-6">
              <div className="bg-gradient-to-r from-red-50 to-white border-l-4 border-red-600 p-5 rounded-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-bold text-red-900 text-lg mb-2">Critical: AAR Compliance</h3>
                    <p className="text-red-800 mb-3">3 events have overdue AARs. Immediate action required to maintain 72-hour submission standard.</p>
                    <div className="bg-white rounded p-3 border border-red-200">
                      <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• Send automated reminder to responsible personnel</li>
                        <li>• Escalate to company leadership if not submitted within 24hrs</li>
                        <li>• Implement pre-event AAR template distribution</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-orange-50 to-white border-l-4 border-orange-600 p-5 rounded-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <DollarSign className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-bold text-orange-900 text-lg mb-2">High Priority: Budget Reallocation</h3>
                    <p className="text-orange-800 mb-3">Q3 budget execution below target (62%). Recommend reallocating $125K to high-performing event types.</p>
                    <div className="bg-white rounded p-3 border border-orange-200">
                      <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• Shift funds from low-ROI static displays to virtual events (6.0x ROI)</li>
                        <li>• Increase Tier 1 asset allocation for Must-Win targets</li>
                        <li>• Accelerate Q4 event approvals to prevent end-of-year rush</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-blue-50 to-white border-l-4 border-blue-600 p-5 rounded-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <Target className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-bold text-blue-900 text-lg mb-2">Asset Optimization: Replicate Success</h3>
                    <p className="text-blue-800 mb-3">Historical data shows VR Simulator + Experience Center combo generates 38% more leads than either alone.</p>
                    <div className="bg-white rounded p-3 border border-blue-200">
                      <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• Schedule VR + Experience Center for all Must-Win college events in Q+2</li>
                        <li>• Request additional VR units from Brigade for high-attendance events</li>
                        <li>• Train recruiters on optimal VR demo techniques</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-green-50 to-white border-l-4 border-green-600 p-5 rounded-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <MapPin className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-bold text-green-900 text-lg mb-2">Geographic Focus: Expand Winning Territories</h3>
                    <p className="text-green-800 mb-3">San Antonio zip codes (78201-78210) show 9.1 effectiveness score. Houston underperforming at 7.2.</p>
                    <div className="bg-white rounded p-3 border border-green-200">
                      <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• Increase San Antonio event frequency from 3 to 5 per quarter</li>
                        <li>• Analyze Houston event mix - shift from gaming to career fairs</li>
                        <li>• Replicate San Antonio playbook (parachute demo + band) in other metros</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-purple-50 to-white border-l-4 border-purple-600 p-5 rounded-lg shadow-sm">
                <div className="flex items-start gap-3">
                  <Users className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-bold text-purple-900 text-lg mb-2">Audience Targeting: College Virtual Events</h3>
                    <p className="text-purple-800 mb-3">Virtual events show highest ROI (6.0x) and 14.4% conversion for college demographic.</p>
                    <div className="bg-white rounded p-3 border border-purple-200">
                      <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• Launch monthly virtual sessions with top 10 universities</li>
                        <li>• Partner with college career centers for integrated campaigns</li>
                        <li>• Develop cyber/signal MOS-focused virtual content for STEM majors</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Next Meeting Prep */}
            <div className="bg-yellow-50 border-2 border-yellow-500 rounded-lg p-5">
              <h3 className="font-bold text-yellow-900 text-lg mb-3 flex items-center gap-2">
                <CheckSquare className="w-6 h-6" />
                Action Items for Next TWG Meeting
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded p-3 border border-yellow-300">
                  <p className="font-semibold text-sm text-gray-800 mb-2">XO / TAWO:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>✓ Review budget reallocation proposal ($125K shift)</li>
                    <li>✓ Approve San Antonio event expansion plan</li>
                    <li>✓ Authorize additional VR unit request to Brigade</li>
                  </ul>
                </div>
                <div className="bg-white rounded p-3 border border-yellow-300">
                  <p className="font-semibold text-sm text-gray-800 mb-2">S3 / S4:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>✓ Coordinate VR + Experience Center schedules for Q+2</li>
                    <li>✓ Validate asset availability for Must-Win events</li>
                    <li>✓ Prepare budget execution brief for XO</li>
                  </ul>
                </div>
                <div className="bg-white rounded p-3 border border-yellow-300">
                  <p className="font-semibold text-sm text-gray-800 mb-2">S2 / MMA:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>✓ Deep-dive Houston underperformance analysis</li>
                    <li>✓ Update high-payoff zip code list with San Antonio data</li>
                    <li>✓ Recommend college virtual event target schools</li>
                  </ul>
                </div>
                <div className="bg-white rounded p-3 border border-yellow-300">
                  <p className="font-semibold text-sm text-gray-800 mb-2">CO Leadership:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>✓ Submit overdue AARs within 24 hours</li>
                    <li>✓ Implement AAR pre-distribution SOP</li>
                    <li>✓ Provide feedback on virtual event pilot results</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto"></div>
            <p className="text-gray-900 mt-4">Loading TWG data...</p>
          </div>
        </div>
      )}

      {/* Add Event Modal */}
      {showAddEventModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Add New Event</h3>
              <button onClick={() => setShowAddEventModal(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Event Name</label>
                <input
                  type="text"
                  value={newEvent.name}
                  onChange={(e) => setNewEvent({...newEvent, name: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., College Career Fair"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Date</label>
                  <input
                    type="date"
                    value={newEvent.date}
                    onChange={(e) => setNewEvent({...newEvent, date: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Location</label>
                  <input
                    type="text"
                    value={newEvent.location}
                    onChange={(e) => setNewEvent({...newEvent, location: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="City, State"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Type</label>
                  <select
                    value={newEvent.type}
                    onChange={(e) => setNewEvent({...newEvent, type: e.target.value as any})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="event_targeting">Event Targeting</option>
                    <option value="geographic_targeting">Geographic Targeting</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Priority</label>
                  <select
                    value={newEvent.priority}
                    onChange={(e) => setNewEvent({...newEvent, priority: e.target.value as any})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="standard">Standard</option>
                    <option value="must_win">Must Win</option>
                    <option value="must_keep">Must Keep</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Target Audience</label>
                <input
                  type="text"
                  value={newEvent.target_audience}
                  onChange={(e) => setNewEvent({...newEvent, target_audience: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., College Students, High School Seniors"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Expected Leads</label>
                  <input
                    type="number"
                    value={newEvent.expected_leads}
                    onChange={(e) => setNewEvent({...newEvent, expected_leads: parseInt(e.target.value) || 0})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Budget ($)</label>
                  <input
                    type="number"
                    value={newEvent.budget}
                    onChange={(e) => setNewEvent({...newEvent, budget: parseInt(e.target.value) || 0})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleAddEvent}
                  className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 flex items-center justify-center gap-2"
                >
                  <Save className="w-5 h-5" />
                  Save Event
                </button>
                <button
                  onClick={() => setShowAddEventModal(false)}
                  className="flex-1 bg-gray-200 text-gray-700 py-3 px-4 rounded-lg font-semibold hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Recommendation Modal */}
      {showAddRecommendationModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Add TWG Recommendation</h3>
              <button onClick={() => setShowAddRecommendationModal(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Priority Level</label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
                  <option>Critical</option>
                  <option>High Priority</option>
                  <option>Medium Priority</option>
                  <option>Information Only</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Recommendation Title</label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g., Increase Digital Advertising Budget"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                <textarea
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Detailed description of the recommendation and supporting data..."
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Recommended Actions</label>
                <textarea
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="List specific action items (one per line)..."
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  className="flex-1 bg-purple-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-purple-700 flex items-center justify-center gap-2"
                  onClick={() => setShowAddRecommendationModal(false)}
                >
                  <Save className="w-5 h-5" />
                  Save Recommendation
                </button>
                <button
                  onClick={() => setShowAddRecommendationModal(false)}
                  className="flex-1 bg-gray-200 text-gray-700 py-3 px-4 rounded-lg font-semibold hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AAR Detail Modal */}
      {showAARDetailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <FileText className="w-6 h-6 text-red-600" />
                AAR Reports - Overdue Events
              </h3>
              <button onClick={() => setShowAARDetailModal(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6">
              <div className="bg-red-50 border-l-4 border-red-600 p-4 mb-6">
                <p className="text-red-800 font-semibold">
                  {aarReports.filter(r => r.status === 'overdue').length} AAR reports are overdue (past 72-hour deadline)
                </p>
              </div>
              
              <div className="space-y-4">
                {aarReports.filter(r => r.status === 'overdue').map((aar) => (
                  <div key={aar.event_id} className="border rounded-lg p-4 bg-gray-50">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-bold text-lg text-gray-900">{aar.event_name}</h4>
                        <p className="text-sm text-gray-600">Event Date: {aar.date}</p>
                      </div>
                      <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-bold">
                        {aar.hours_since_event}h OVERDUE
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <span className="text-gray-500">Due Date:</span>
                        <span className="ml-2 font-semibold">{aar.due_date}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Status:</span>
                        <span className="ml-2 font-semibold text-red-600">Overdue</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 flex items-center gap-2">
                        <Upload className="w-4 h-4" />
                        Submit AAR
                      </button>
                      <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300">
                        View Event Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Budget Detail Modal */}
      {showBudgetDetailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <DollarSign className="w-6 h-6 text-green-600" />
                Marketing Budget Breakdown
              </h3>
              <button onClick={() => setShowBudgetDetailModal(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6">
              {marketingBudget && (
                <>
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Total Budget</p>
                      <p className="text-2xl font-bold text-blue-600">${(marketingBudget.total_budget / 1000).toFixed(0)}K</p>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Spent</p>
                      <p className="text-2xl font-bold text-orange-600">${(marketingBudget.spent / 1000).toFixed(0)}K</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Remaining</p>
                      <p className="text-2xl font-bold text-green-600">${(marketingBudget.remaining / 1000).toFixed(0)}K</p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Utilization</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {((marketingBudget.spent / marketingBudget.total_budget) * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  <h4 className="text-lg font-bold text-gray-900 mb-3">Quarterly Breakdown</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Quarter</th>
                          <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Allocated</th>
                          <th className="px-4 py-3 text-left text-sm font-bold text-gray-700">Budget Percentage</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {Object.entries(marketingBudget.by_quarter).map(([quarter, amount]) => (
                          <tr key={quarter} className="hover:bg-gray-50">
                            <td className="px-4 py-3 font-semibold">{quarter.toUpperCase()}</td>
                            <td className="px-4 py-3">${(amount as number).toLocaleString()}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="flex-1 bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{width: `${((amount as number) / marketingBudget.total_budget * 100)}%`}}
                                  />
                                </div>
                                <span className="text-sm font-semibold">
                                  {(((amount as number) / marketingBudget.total_budget) * 100).toFixed(0)}%
                                </span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Events Detail Modal */}
      {showEventsDetailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Calendar className="w-6 h-6 text-blue-600" />
                Active Events Overview
              </h3>
              <button onClick={() => setShowEventsDetailModal(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <button
                  onClick={() => setShowAddEventModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 flex items-center gap-2"
                >
                  <Plus className="w-5 h-5" />
                  Add New Event
                </button>
              </div>
              
              <div className="grid gap-4">
                {targetingPhases.flatMap(phase => phase.events).map((event) => (
                  <div 
                    key={event.event_id} 
                    onClick={() => handleEventClick(event)}
                    className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="font-bold text-lg text-gray-900">{event.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{event.location}</p>
                      </div>
                      <div className="flex gap-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          event.type === 'event_targeting' 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {event.type === 'event_targeting' ? 'Event' : 'Geographic'}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          event.priority === 'must_win' ? 'bg-orange-100 text-orange-800' :
                          event.priority === 'must_keep' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {event.priority?.replace('_', ' ').toUpperCase() || 'STANDARD'}
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Date:</span>
                        <span className="ml-2 font-semibold">{event.date}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Expected Leads:</span>
                        <span className="ml-2 font-semibold text-blue-600">{event.expected_leads}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Budget:</span>
                        <span className="ml-2 font-semibold text-green-600">${event.budget.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Status:</span>
                        <span className={`ml-2 font-semibold ${
                          event.status === 'completed' ? 'text-green-600' :
                          event.status === 'in_progress' ? 'text-blue-600' :
                          'text-gray-600'
                        }`}>
                          {event.status?.replace('_', ' ').toUpperCase() || 'PLANNED'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Targets Detail Modal */}
      {showTargetsDetailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Target className="w-6 h-6 text-orange-600" />
                Must Win & Must Keep Targets
              </h3>
              <button onClick={() => setShowTargetsDetailModal(false)} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div className="bg-orange-50 border-l-4 border-orange-600 p-4 rounded">
                  <h4 className="font-bold text-orange-900 mb-2">Must Win Targets (8)</h4>
                  <p className="text-sm text-orange-800 mb-3">
                    High-potential areas where we currently have low market share but significant opportunity.
                  </p>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-orange-600" />
                      <span className="font-semibold">Downtown Houston (77002)</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-orange-600" />
                      <span className="font-semibold">Pearland (77584)</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-orange-600" />
                      <span className="font-semibold">Katy (77494)</span>
                    </li>
                    <li className="text-gray-500">+ 5 more locations</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                  <h4 className="font-bold text-blue-900 mb-2">Must Keep Targets (12)</h4>
                  <p className="text-sm text-blue-800 mb-3">
                    Strong-performing areas where we need to maintain presence and prevent competitor encroachment.
                  </p>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold">Spring (77373)</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold">Cypress (77433)</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold">League City (77573)</span>
                    </li>
                    <li className="text-gray-500">+ 9 more locations</li>
                  </ul>
                </div>
              </div>

              <div className="bg-gray-100 p-4 rounded-lg">
                <h4 className="font-bold text-gray-900 mb-2">Strategic Insights</h4>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li>• <strong>Must Win</strong> areas receive aggressive event targeting and increased ad spend</li>
                  <li>• <strong>Must Keep</strong> areas maintain consistent presence through geographic targeting</li>
                  <li>• Target classification reviewed quarterly based on market intelligence and performance data</li>
                  <li>• Sync Matrix tracks all targeting efforts across Must Win/Must Keep designations</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
