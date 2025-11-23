import React, { useState, useEffect } from 'react';
import {
  Users, Target, TrendingUp, Calendar, FileText, CheckSquare,
  AlertCircle, Clock, DollarSign, Award, Map, Briefcase, Shield
} from 'lucide-react';

interface FusionTeamMember {
  role: string;
  name: string;
  responsibilities: string[];
  currentTasks: number;
  completedTasks: number;
}

interface FusionCyclePhase {
  phase: string;
  status: 'pending' | 'in_progress' | 'completed';
  dueDate: string;
  owner: string;
  progress: number;
}

interface PaperworkTracker {
  id: string;
  type: string;
  title: string;
  status: string;
  dueDate: string;
  submittedTo: string;
  owner: string;
}

const FUSION_ROLES = {
  XO: {
    title: 'Executive Officer (XO)',
    icon: <Shield className="w-6 h-6" />,
    color: 'from-gray-700 to-gray-900',
    responsibilities: [
      'Head Fusion Process',
      'Ensure Paperwork/Slides sent to BDE',
      'Track BDE deadlines, backwards planning',
      'Overall coordination and synchronization'
    ]
  },
  '420T': {
    title: '420T Warrant Officer Talent Acquisition Technician',
    icon: <Target className="w-6 h-6" />,
    color: 'from-yellow-600 to-yellow-800',
    responsibilities: [
      'Provide Trend Assessment',
      'QC events prior to BC touchpoint',
      'Manage messaging and audience targeting',
      'Analyze market algorithms and performance metrics'
    ]
  },
  MMA: {
    title: 'Market & Mission Analyst (MMA)',
    icon: <TrendingUp className="w-6 h-6" />,
    color: 'from-blue-600 to-blue-800',
    responsibilities: [
      'Intel/market analysis',
      'Potential contract identification',
      'Per-company information and guidance',
      'Future targeting analysis based on past performance'
    ]
  },
  S3: {
    title: 'S3 Operations',
    icon: <Calendar className="w-6 h-6" />,
    color: 'from-green-600 to-green-800',
    responsibilities: [
      'Track Tiered assets/events',
      'Manage calendar/IPR 30/60/90',
      'TAIR support coordination',
      'Battalion involvement tracking',
      'Track BDE timelines/Taskers'
    ]
  },
  ESS: {
    title: 'Education Services Specialist (ESS)',
    icon: <Award className="w-6 h-6" />,
    color: 'from-purple-600 to-purple-800',
    responsibilities: [
      'Per-company ALRL% tracking',
      'Educational program coordination',
      'Testing and qualification support'
    ]
  },
  APA: {
    title: 'Advertising & Public Affairs (A&PA)',
    icon: <Briefcase className="w-6 h-6" />,
    color: 'from-red-600 to-red-800',
    responsibilities: [
      'Targeted school updates',
      'SRP check status',
      'Review all Company events, COI, Field Surveys',
      'Manage paperwork flow',
      'Track requests through completion',
      'Track budget requests',
      'Present requests to BDE/BLT',
      'EMM (Enterprise Marketing Management) oversight'
    ]
  }
};

export const FusionTeamDashboard: React.FC = () => {
  const [activeView, setActiveView] = useState<'overview' | 'cycle' | 'paperwork' | 'calendar' | 'roles'>('overview');
  const [teamMembers, setTeamMembers] = useState<FusionTeamMember[]>([]);
  const [cyclePhases, setCyclePhases] = useState<FusionCyclePhase[]>([]);
  const [paperwork, setPaperwork] = useState<PaperworkTracker[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFusionData();
  }, []);

  const fetchFusionData = async () => {
    setLoading(true);
    try {
      // Mock data for now - replace with actual API calls
      setTeamMembers([
        {
          role: 'XO',
          name: 'MAJ Smith',
          responsibilities: FUSION_ROLES.XO.responsibilities,
          currentTasks: 8,
          completedTasks: 42
        },
        {
          role: '420T',
          name: 'SGT Johnson',
          responsibilities: FUSION_ROLES['420T'].responsibilities,
          currentTasks: 12,
          completedTasks: 156
        },
        {
          role: 'MMA',
          name: 'SPC Davis',
          responsibilities: FUSION_ROLES.MMA.responsibilities,
          currentTasks: 6,
          completedTasks: 89
        },
        {
          role: 'S3',
          name: 'CPT Williams',
          responsibilities: FUSION_ROLES.S3.responsibilities,
          currentTasks: 15,
          completedTasks: 203
        },
        {
          role: 'ESS',
          name: 'SSG Brown',
          responsibilities: FUSION_ROLES.ESS.responsibilities,
          currentTasks: 4,
          completedTasks: 67
        },
        {
          role: 'APA',
          name: 'SGT Garcia',
          responsibilities: FUSION_ROLES.APA.responsibilities,
          currentTasks: 11,
          completedTasks: 134
        }
      ]);

      setCyclePhases([
        {
          phase: 'Plan - Mission Analysis',
          status: 'completed',
          dueDate: '2025-11-15',
          owner: 'MMA',
          progress: 100
        },
        {
          phase: 'Schedule - Event Coordination',
          status: 'completed',
          dueDate: '2025-11-18',
          owner: 'S3',
          progress: 100
        },
        {
          phase: 'Access - Market Targeting',
          status: 'in_progress',
          dueDate: '2025-11-22',
          owner: '420T',
          progress: 65
        },
        {
          phase: 'Evaluate - Performance Review',
          status: 'pending',
          dueDate: '2025-11-30',
          owner: 'XO',
          progress: 0
        }
      ]);

      setPaperwork([
        {
          id: 'PW001',
          type: 'Event Request',
          title: 'Q1 Career Fair - Houston',
          status: 'pending_bde',
          dueDate: '2025-11-25',
          submittedTo: '1st BDE',
          owner: 'A&PA'
        },
        {
          id: 'PW002',
          type: 'Budget Request',
          title: 'Marketing Campaign FY26 Q2',
          status: 'in_review',
          dueDate: '2025-11-20',
          submittedTo: 'BLT',
          owner: 'A&PA'
        },
        {
          id: 'PW003',
          type: 'After Action Review',
          title: 'College Fair Series - November',
          status: 'overdue',
          dueDate: '2025-11-18',
          submittedTo: '1st BDE',
          owner: '420T'
        },
        {
          id: 'PW004',
          type: 'Targeting Brief',
          title: 'High Payoff Segment Analysis',
          status: 'draft',
          dueDate: '2025-11-28',
          submittedTo: 'XO',
          owner: 'MMA'
        }
      ]);

    } catch (error) {
      console.error('Error fetching fusion data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'completed': 'bg-green-100 text-green-800 border-green-300',
      'in_progress': 'bg-blue-100 text-blue-800 border-blue-300',
      'pending': 'bg-gray-100 text-gray-800 border-gray-300',
      'pending_bde': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'in_review': 'bg-purple-100 text-purple-800 border-purple-300',
      'overdue': 'bg-red-100 text-red-800 border-red-300',
      'draft': 'bg-gray-100 text-gray-600 border-gray-300'
    };
    return colors[status] || colors.pending;
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Fusion Team Structure */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Users className="w-6 h-6 mr-2 text-yellow-600" />
          Fusion Team Structure
        </h3>
        <p className="text-gray-600 mb-6">
          The Fusion Team integrates multiple functional areas to plan, schedule, access, evaluate marketing and event scheduling,
          lead capturing, and recruiting funnel tracking for optimal talent acquisition operations.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teamMembers.map((member) => {
            const roleConfig = FUSION_ROLES[member.role as keyof typeof FUSION_ROLES];
            return (
              <button
                key={member.role}
                onClick={() => setActiveView('roles')}
                className="bg-gradient-to-br from-gray-50 to-white border-2 border-gray-200 rounded-lg p-4 hover:shadow-lg hover:border-yellow-500 transition-all text-left cursor-pointer"
                title="Click to view detailed role assignments"
              >
                <div className={`bg-gradient-to-r ${roleConfig.color} text-white rounded-lg p-3 mb-3`}>
                  <div className="flex items-center justify-between">
                    {roleConfig.icon}
                    <span className="text-sm font-bold">{member.role}</span>
                  </div>
                  <h4 className="text-lg font-bold mt-2">{roleConfig.title}</h4>
                  <p className="text-sm opacity-90">{member.name}</p>
                </div>
                
                <div className="space-y-2 mb-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Current Tasks:</span>
                    <span className="font-semibold text-blue-600">{member.currentTasks}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Completed:</span>
                    <span className="font-semibold text-green-600">{member.completedTasks}</span>
                  </div>
                </div>

                <div className="border-t pt-3">
                  <p className="text-xs font-semibold text-gray-700 mb-2">Key Responsibilities:</p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    {member.responsibilities.slice(0, 3).map((resp, idx) => (
                      <li key={idx} className="flex items-start">
                        <CheckSquare className="w-3 h-3 mr-1 mt-0.5 text-green-600 flex-shrink-0" />
                        <span>{resp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Active Tasks</p>
              <p className="text-3xl font-bold">{teamMembers.reduce((acc, m) => acc + m.currentTasks, 0)}</p>
            </div>
            <Target className="w-12 h-12 opacity-50" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Completed Tasks</p>
              <p className="text-3xl font-bold">{teamMembers.reduce((acc, m) => acc + m.completedTasks, 0)}</p>
            </div>
            <CheckSquare className="w-12 h-12 opacity-50" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Pending Paperwork</p>
              <p className="text-3xl font-bold">{paperwork.filter(p => p.status !== 'completed').length}</p>
            </div>
            <FileText className="w-12 h-12 opacity-50" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-red-500 to-red-600 text-white rounded-lg p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Overdue Items</p>
              <p className="text-3xl font-bold">{paperwork.filter(p => p.status === 'overdue').length}</p>
            </div>
            <AlertCircle className="w-12 h-12 opacity-50" />
          </div>
        </div>
      </div>
    </div>
  );

  const renderCycle = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Fusion Cycle Phases</h3>
      <p className="text-gray-600 mb-6">
        The Fusion Team operates on a continuous cycle: <strong>Plan → Schedule → Access → Evaluate</strong>
      </p>
      
      <div className="space-y-4">
        {cyclePhases.map((phase, idx) => (
          <div key={idx} className="border-2 border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  phase.status === 'completed' ? 'bg-green-100 text-green-600' :
                  phase.status === 'in_progress' ? 'bg-blue-100 text-blue-600' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {phase.status === 'completed' ? <CheckSquare className="w-5 h-5" /> :
                   phase.status === 'in_progress' ? <Clock className="w-5 h-5" /> :
                   <Calendar className="w-5 h-5" />}
                </div>
                <div>
                  <h4 className="font-bold text-gray-800">{phase.phase}</h4>
                  <p className="text-sm text-gray-600">Owner: {phase.owner} • Due: {phase.dueDate}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(phase.status)}`}>
                {phase.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            
            <div className="mt-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Progress</span>
                <span className="font-semibold">{phase.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    phase.progress === 100 ? 'bg-green-500' :
                    phase.progress > 0 ? 'bg-blue-500' : 'bg-gray-400'
                  }`}
                  style={{ width: `${phase.progress}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderPaperwork = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Paperwork Tracker</h3>
      <p className="text-gray-600 mb-6">
        Track BDE deadlines, submission status, and backwards planning milestones
      </p>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b-2 border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Type</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Title</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Owner</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Submitted To</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Due Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {paperwork.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono text-gray-800">{item.id}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{item.type}</td>
                <td className="px-4 py-3 text-sm font-medium text-gray-800">{item.title}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{item.owner}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{item.submittedTo}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{item.dueDate}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${getStatusColor(item.status)}`}>
                    {item.status.replace('_', ' ').toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderCalendar = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Long Range Event Calendar</h3>
      <p className="text-gray-600 mb-6">
        S3 manages the long-range event calendar with IPR 30/60/90 day planning cycles
      </p>
      
      <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 text-center">
        <Calendar className="w-16 h-16 mx-auto text-blue-600 mb-4" />
        <p className="text-gray-700">
          Integrated with Calendar & Scheduler Dashboard
        </p>
        <p className="text-sm text-gray-600 mt-2">
          Navigate to <strong>Operations → Calendar & Scheduler</strong> for full event planning
        </p>
      </div>
    </div>
  );

  const renderTeamRoles = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-yellow-600 to-yellow-700 text-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-2 flex items-center">
          <Users className="w-8 h-8 mr-3" />
          Team Role Assignments & Responsibilities
        </h2>
        <p className="text-yellow-100">Detailed breakdown of each Fusion Team role with full responsibilities and coordination requirements</p>
      </div>

      {/* Detailed Role Cards */}
      <div className="space-y-6">
        {Object.entries(FUSION_ROLES).map(([roleKey, roleConfig]) => {
          const member = teamMembers.find(m => m.role === roleKey);
          return (
            <div key={roleKey} className="bg-white rounded-lg shadow-md border-2 border-gray-200 overflow-hidden">
              <div className={`bg-gradient-to-r ${roleConfig.color} text-white p-6`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-white/20 rounded-full p-3">
                      {roleConfig.icon}
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold">{roleConfig.title}</h3>
                      <p className="text-sm opacity-90">Role: {roleKey}</p>
                    </div>
                  </div>
                  {member && (
                    <div className="text-right">
                      <p className="text-sm opacity-75">Currently Assigned:</p>
                      <p className="text-xl font-bold">{member.name}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-6">
                <div className="mb-6">
                  <h4 className="text-lg font-bold text-gray-800 mb-3 flex items-center">
                    <CheckSquare className="w-5 h-5 mr-2 text-green-600" />
                    Complete Responsibilities
                  </h4>
                  <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {roleConfig.responsibilities.map((resp, idx) => (
                      <li key={idx} className="flex items-start bg-gray-50 p-3 rounded border border-gray-200">
                        <span className="bg-yellow-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mr-3 flex-shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="text-sm text-gray-700">{resp}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {member && (
                  <div className="grid grid-cols-3 gap-4 pt-6 border-t border-gray-200">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-blue-600">{member.currentTasks}</p>
                      <p className="text-sm text-gray-600">Current Tasks</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-600">{member.completedTasks}</p>
                      <p className="text-sm text-gray-600">Completed Tasks</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-purple-600">
                        {member.completedTasks > 0 ? Math.round((member.completedTasks / (member.completedTasks + member.currentTasks)) * 100) : 0}%
                      </p>
                      <p className="text-sm text-gray-600">Completion Rate</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-yellow-50 border-l-4 border-yellow-600 p-6 rounded">
        <h4 className="font-bold text-yellow-900 mb-2 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          Team Coordination Note
        </h4>
        <p className="text-sm text-yellow-800">
          All Fusion Team members work in close coordination. The XO leads the process and ensures all deadlines are met.
          Regular touchpoints should be scheduled to maintain synchronization across all functional areas.
        </p>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Fusion Team data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center">
          <Users className="w-8 h-8 mr-3 text-yellow-600" />
          Fusion Team Operations Dashboard
        </h1>
        <p className="text-gray-600 mt-2">
          Multifunctional coordination hub for Planning, Scheduling, Accessing, and Evaluating talent acquisition operations
        </p>
      </div>

      {/* View Tabs */}
      <div className="bg-white rounded-lg shadow-md mb-6">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveView('overview')}
            className={`px-6 py-3 font-semibold transition-colors ${
              activeView === 'overview'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Team Overview
          </button>
          <button
            onClick={() => setActiveView('cycle')}
            className={`px-6 py-3 font-semibold transition-colors ${
              activeView === 'cycle'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Fusion Cycle
          </button>
          <button
            onClick={() => setActiveView('paperwork')}
            className={`px-6 py-3 font-semibold transition-colors ${
              activeView === 'paperwork'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Paperwork Tracker
          </button>
          <button
            onClick={() => setActiveView('calendar')}
            className={`px-6 py-3 font-semibold transition-colors ${
              activeView === 'calendar'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Event Calendar
          </button>
          <button
            onClick={() => setActiveView('roles')}
            className={`px-6 py-3 font-semibold transition-colors ${
              activeView === 'roles'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Team Role Assignments
          </button>
        </div>
      </div>

      {/* Content */}
      {activeView === 'overview' && renderOverview()}
      {activeView === 'cycle' && renderCycle()}
      {activeView === 'paperwork' && renderPaperwork()}
      {activeView === 'calendar' && renderCalendar()}
      {activeView === 'roles' && renderTeamRoles()}
    </div>
  );
};

export default FusionTeamDashboard;
