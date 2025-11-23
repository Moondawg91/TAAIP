import React, { useState, useEffect } from 'react';
import {
  Target, Calendar, Users, FileText, CheckSquare, TrendingUp, 
  MapPin, DollarSign, AlertCircle, Clock, ChevronRight, Filter,
  Download, Upload, Eye, Edit, CheckCircle, XCircle
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
            <div className="bg-white rounded-xl shadow-md p-6">
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

            <div className="bg-white rounded-xl shadow-md p-6">
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

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm uppercase font-semibold">Active Events</p>
                  <p className="text-3xl font-bold text-blue-600 mt-2">24</p>
                </div>
                <Calendar className="w-8 h-8 text-blue-600" />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
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
                    <tr key={aar.event_id} className="hover:bg-gray-50">
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
                  <tr className="hover:bg-gray-50">
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
                  <tr className="hover:bg-gray-50">
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
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Target className="w-7 h-7 text-yellow-400" />
              Houston Recruiting BN - Priority Events
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
                <h3 className="font-bold text-yellow-400 mb-2">Youth Career Expo</h3>
                <p className="text-sm text-blue-100">High-impact youth engagement opportunity</p>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
                <h3 className="font-bold text-yellow-400 mb-2">Westbrook HS Career Fair</h3>
                <p className="text-sm text-blue-100">Targeted high school recruitment event</p>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20">
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
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-7 h-7 text-purple-600" />
              TWG Recommendations & Action Items
            </h2>
            <p className="text-gray-600 mb-6">Data-driven recommendations for the Targeting Working Group based on current performance and market intelligence</p>
            
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
    </div>
  );
};
