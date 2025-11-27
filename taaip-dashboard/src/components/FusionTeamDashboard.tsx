import React, { useState, useEffect } from 'react';
import {
  Users, Target, TrendingUp, Calendar, FileText, CheckSquare,
  AlertCircle, Clock, DollarSign, Award, Map, Briefcase, Shield, Edit, Plus, X, Save,
  MessageSquare, ArrowRight, Link as LinkIcon, Trash2, UserPlus
} from 'lucide-react';

interface FusionTeamMember {
  role: string;
  name: string;
  responsibilities: string[];
  currentTasks: number;
  completedTasks: number;
}

interface TaskComment {
  id: string;
  author: string;
  content: string;
  timestamp: string;
}

interface Task {
  id: string;
  role: string;
  title: string;
  description?: string;
  status: 'not-started' | 'in-progress' | 'completed' | 'blocked' | 'review' | 'approved';
  dueDate: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignee?: string;
  level: number; // 1=Company, 2=Battalion, 3=Brigade
  comments: TaskComment[];
  relatedTasks: string[]; // Array of task IDs
  createdAt: string;
  updatedAt: string;
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
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showTaskDetailModal, setShowTaskDetailModal] = useState(false);
  const [selectedRole, setSelectedRole] = useState('');
  const [editMemberName, setEditMemberName] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  
  // Task editing states
  const [editTaskTitle, setEditTaskTitle] = useState('');
  const [editTaskDescription, setEditTaskDescription] = useState('');
  const [editTaskDueDate, setEditTaskDueDate] = useState('');
  const [editTaskPriority, setEditTaskPriority] = useState<Task['priority']>('medium');
  const [editTaskAssignee, setEditTaskAssignee] = useState('');
  const [editTaskLevel, setEditTaskLevel] = useState(1);
  const [newComment, setNewComment] = useState('');
  const [selectedRelatedTask, setSelectedRelatedTask] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

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

  const handleAssignMember = (role: string) => {
    const member = teamMembers.find(m => m.role === role);
    setSelectedRole(role);
    setEditMemberName(member?.name || '');
    setShowEditModal(true);
  };

  const handleSaveMember = () => {
    setTeamMembers(prev => prev.map(m => 
      m.role === selectedRole ? { ...m, name: editMemberName } : m
    ));
    setShowEditModal(false);
    setSelectedRole('');
    setEditMemberName('');
  };

  const handleUpdateTaskStatus = (taskId: string, newStatus: Task['status']) => {
    setTasks(prev => prev.map(t => 
      t.id === taskId ? { ...t, status: newStatus } : t
    ));
  };

  const handleAddTask = () => {
    const now = new Date().toISOString();
    const newTask: Task = {
      id: `TASK${Date.now()}`,
      role: selectedRole,
      title: 'New Task',
      description: '',
      status: 'not-started',
      dueDate: new Date().toISOString().split('T')[0],
      priority: 'medium',
      assignee: teamMembers.find(m => m.role === selectedRole)?.name || '',
      level: 1,
      comments: [],
      relatedTasks: [],
      createdAt: now,
      updatedAt: now
    };
    setTasks(prev => [...prev, newTask]);
  };

  const handleOpenTaskDetails = (task: Task) => {
    setSelectedTask(task);
    setEditTaskTitle(task.title);
    setEditTaskDescription(task.description || '');
    setEditTaskDueDate(task.dueDate);
    setEditTaskPriority(task.priority);
    setEditTaskAssignee(task.assignee || '');
    setEditTaskLevel(task.level);
    setShowTaskDetailModal(true);
  };

  const handleSaveTaskDetails = () => {
    if (!selectedTask) return;
    
    setTasks(prev => prev.map(t => 
      t.id === selectedTask.id ? {
        ...t,
        title: editTaskTitle,
        description: editTaskDescription,
        dueDate: editTaskDueDate,
        priority: editTaskPriority,
        assignee: editTaskAssignee,
        level: editTaskLevel,
        updatedAt: new Date().toISOString()
      } : t
    ));
    setShowTaskDetailModal(false);
  };

  const handleAddComment = () => {
    if (!selectedTask || !newComment.trim()) return;
    
    const comment: TaskComment = {
      id: `COMMENT${Date.now()}`,
      author: 'Current User', // Replace with actual user
      content: newComment,
      timestamp: new Date().toISOString()
    };
    
    setTasks(prev => prev.map(t => 
      t.id === selectedTask.id ? {
        ...t,
        comments: [...t.comments, comment],
        updatedAt: new Date().toISOString()
      } : t
    ));
    
    setSelectedTask({
      ...selectedTask,
      comments: [...selectedTask.comments, comment]
    });
    
    setNewComment('');
  };

  const handlePushTaskToNextLevel = () => {
    if (!selectedTask || selectedTask.level >= 3) return;
    
    setTasks(prev => prev.map(t => 
      t.id === selectedTask.id ? {
        ...t,
        level: t.level + 1,
        status: 'review' as Task['status'],
        updatedAt: new Date().toISOString()
      } : t
    ));
    
    setSelectedTask({
      ...selectedTask,
      level: selectedTask.level + 1,
      status: 'review'
    });
  };

  const handleReassignTask = (newRole: string) => {
    if (!selectedTask) return;
    
    const newAssignee = teamMembers.find(m => m.role === newRole)?.name || '';
    
    setTasks(prev => prev.map(t => 
      t.id === selectedTask.id ? {
        ...t,
        role: newRole,
        assignee: newAssignee,
        updatedAt: new Date().toISOString()
      } : t
    ));
    
    setSelectedTask({
      ...selectedTask,
      role: newRole,
      assignee: newAssignee
    });
  };

  const handleAddRelatedTask = () => {
    if (!selectedTask || !selectedRelatedTask) return;
    
    setTasks(prev => prev.map(t => 
      t.id === selectedTask.id ? {
        ...t,
        relatedTasks: [...t.relatedTasks, selectedRelatedTask],
        updatedAt: new Date().toISOString()
      } : t
    ));
    
    setSelectedTask({
      ...selectedTask,
      relatedTasks: [...selectedTask.relatedTasks, selectedRelatedTask]
    });
    
    setSelectedRelatedTask('');
  };

  const handleRemoveRelatedTask = (taskId: string) => {
    if (!selectedTask) return;
    
    setTasks(prev => prev.map(t => 
      t.id === selectedTask.id ? {
        ...t,
        relatedTasks: t.relatedTasks.filter(id => id !== taskId),
        updatedAt: new Date().toISOString()
      } : t
    ));
    
    setSelectedTask({
      ...selectedTask,
      relatedTasks: selectedTask.relatedTasks.filter(id => id !== taskId)
    });
  };

  const handleDeleteTask = (taskId: string) => {
    if (confirm('Are you sure you want to delete this task?')) {
      setTasks(prev => prev.filter(t => t.id !== taskId));
      setShowTaskDetailModal(false);
    }
  };

  const getLevelLabel = (level: number) => {
    switch (level) {
      case 1: return 'Company';
      case 2: return 'Battalion';
      case 3: return 'Brigade';
      default: return 'Unknown';
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'not-started': 'bg-gray-100 text-gray-800 border-gray-300',
      'in-progress': 'bg-blue-100 text-blue-800 border-blue-300',
      'completed': 'bg-green-100 text-green-800 border-green-300',
      'blocked': 'bg-red-100 text-red-800 border-red-300',
      'review': 'bg-purple-100 text-purple-800 border-purple-300',
      'approved': 'bg-teal-100 text-teal-800 border-teal-300',
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
                  <div className="flex flex-col items-end gap-2">
                    {member && (
                      <div className="text-right">
                        <p className="text-sm opacity-75">Currently Assigned:</p>
                        <p className="text-xl font-bold">{member.name}</p>
                      </div>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAssignMember(roleKey);
                      }}
                      className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                      title="Edit assignment"
                    >
                      <Edit className="w-4 h-4" />
                      <span className="text-sm font-semibold">Edit</span>
                    </button>
                  </div>
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
                  <div className="pt-6 border-t border-gray-200 space-y-4">
                    <div className="grid grid-cols-3 gap-4">
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
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedRole(roleKey);
                        setShowTaskModal(true);
                      }}
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-3 px-4 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 flex items-center justify-center gap-2"
                    >
                      <CheckSquare className="w-5 h-5" />
                      Manage Tasks & Status Updates
                    </button>
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

      {/* Edit Member Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Assign Team Member</h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Role: {selectedRole}
                </label>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Member Name
                </label>
                <input
                  type="text"
                  value={editMemberName}
                  onChange={(e) => setEditMemberName(e.target.value)}
                  placeholder="e.g., MAJ Smith"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleSaveMember}
                  className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-yellow-700 flex items-center justify-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Save Assignment
                </button>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg font-semibold hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Task Management Modal */}
      {showTaskModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full p-6 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Task Management - {selectedRole}</h3>
              <button
                onClick={() => setShowTaskModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <button
              onClick={handleAddTask}
              className="w-full mb-4 bg-blue-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add New Task
            </button>

            <div className="space-y-3">
              {tasks.filter(t => t.role === selectedRole).length === 0 ? (
                <p className="text-center text-gray-500 py-8">No tasks yet. Click "Add New Task" to get started.</p>
              ) : (
                tasks.filter(t => t.role === selectedRole).map(task => (
                  <div 
                    key={task.id} 
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-white"
                    onClick={() => handleOpenTaskDetails(task)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">{task.title}</h4>
                        {task.description && (
                          <p className="text-sm text-gray-600 mb-2">{task.description.slice(0, 100)}{task.description.length > 100 ? '...' : ''}</p>
                        )}
                      </div>
                      <div className="flex flex-col gap-1 ml-3">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          task.priority === 'critical' ? 'bg-red-600 text-white' :
                          task.priority === 'high' ? 'bg-red-100 text-red-800' :
                          task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {task.priority.toUpperCase()}
                        </span>
                        <span className="px-2 py-1 rounded text-xs font-bold bg-gray-200 text-gray-700">
                          {getLevelLabel(task.level)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>Due: {task.dueDate}</span>
                      </div>
                      {task.assignee && (
                        <div className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          <span>{task.assignee}</span>
                        </div>
                      )}
                      {task.comments.length > 0 && (
                        <div className="flex items-center gap-1">
                          <MessageSquare className="w-4 h-4" />
                          <span>{task.comments.length} comments</span>
                        </div>
                      )}
                      {task.relatedTasks.length > 0 && (
                        <div className="flex items-center gap-1">
                          <LinkIcon className="w-4 h-4" />
                          <span>{task.relatedTasks.length} related</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleUpdateTaskStatus(task.id, 'not-started'); }}
                        className={`flex-1 py-1.5 px-2 rounded text-xs font-semibold transition-colors ${
                          task.status === 'not-started'
                            ? 'bg-gray-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        Not Started
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleUpdateTaskStatus(task.id, 'in-progress'); }}
                        className={`flex-1 py-1.5 px-2 rounded text-xs font-semibold transition-colors ${
                          task.status === 'in-progress'
                            ? 'bg-blue-600 text-white'
                            : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        }`}
                      >
                        In Progress
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleUpdateTaskStatus(task.id, 'review'); }}
                        className={`flex-1 py-1.5 px-2 rounded text-xs font-semibold transition-colors ${
                          task.status === 'review'
                            ? 'bg-purple-600 text-white'
                            : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                        }`}
                      >
                        Review
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleUpdateTaskStatus(task.id, 'completed'); }}
                        className={`flex-1 py-1.5 px-2 rounded text-xs font-semibold transition-colors ${
                          task.status === 'completed'
                            ? 'bg-green-600 text-white'
                            : 'bg-green-100 text-green-700 hover:bg-green-200'
                        }`}
                      >
                        Completed
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleUpdateTaskStatus(task.id, 'blocked'); }}
                        className={`flex-1 py-1.5 px-2 rounded text-xs font-semibold transition-colors ${
                          task.status === 'blocked'
                            ? 'bg-red-600 text-white'
                            : 'bg-red-100 text-red-700 hover:bg-red-200'
                        }`}
                      >
                        Blocked
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Task Detail Modal */}
      {showTaskDetailModal && selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
              <div className="flex-1">
                <input
                  type="text"
                  value={editTaskTitle}
                  onChange={(e) => setEditTaskTitle(e.target.value)}
                  className="text-2xl font-bold text-gray-900 w-full border-b-2 border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none transition-colors px-2 py-1"
                  placeholder="Task Title"
                />
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
                  <span className={`px-3 py-1 rounded-full font-semibold ${getStatusColor(selectedTask.status)}`}>
                    {selectedTask.status.replace('-', ' ').toUpperCase()}
                  </span>
                  <span className="px-3 py-1 rounded-full font-semibold bg-blue-100 text-blue-800">
                    {getLevelLabel(selectedTask.level)}
                  </span>
                  <span>Task ID: {selectedTask.id}</span>
                </div>
              </div>
              <button
                onClick={() => setShowTaskDetailModal(false)}
                className="text-gray-500 hover:text-gray-700 ml-4"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 grid grid-cols-3 gap-6">
              {/* Main Content - Left 2 columns */}
              <div className="col-span-2 space-y-6">
                {/* Description */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                  <textarea
                    value={editTaskDescription}
                    onChange={(e) => setEditTaskDescription(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    placeholder="Add task description..."
                  />
                </div>

                {/* Comments Section */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Comments ({selectedTask.comments.length})
                  </h4>
                  
                  {/* Comment Input */}
                  <div className="mb-4 flex gap-2">
                    <input
                      type="text"
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Add a comment..."
                    />
                    <button
                      onClick={handleAddComment}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add
                    </button>
                  </div>

                  {/* Comments List */}
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {selectedTask.comments.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">No comments yet</p>
                    ) : (
                      selectedTask.comments.map(comment => (
                        <div key={comment.id} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-sm text-gray-900">{comment.author}</span>
                            <span className="text-xs text-gray-500">
                              {new Date(comment.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700">{comment.content}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Related Tasks */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <LinkIcon className="w-5 h-5" />
                    Related Tasks ({selectedTask.relatedTasks.length})
                  </h4>
                  
                  {/* Add Related Task */}
                  <div className="mb-4 flex gap-2">
                    <select
                      value={selectedRelatedTask}
                      onChange={(e) => setSelectedRelatedTask(e.target.value)}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">Select a task...</option>
                      {tasks.filter(t => t.id !== selectedTask.id && !selectedTask.relatedTasks.includes(t.id)).map(task => (
                        <option key={task.id} value={task.id}>
                          {task.title} ({task.role})
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={handleAddRelatedTask}
                      disabled={!selectedRelatedTask}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <LinkIcon className="w-4 h-4" />
                      Link
                    </button>
                  </div>

                  {/* Related Tasks List */}
                  <div className="space-y-2">
                    {selectedTask.relatedTasks.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">No related tasks</p>
                    ) : (
                      selectedTask.relatedTasks.map(taskId => {
                        const relatedTask = tasks.find(t => t.id === taskId);
                        if (!relatedTask) return null;
                        return (
                          <div key={taskId} className="bg-gray-50 rounded-lg p-3 border border-gray-200 flex items-center justify-between">
                            <div className="flex-1">
                              <p className="font-semibold text-sm text-gray-900">{relatedTask.title}</p>
                              <p className="text-xs text-gray-600">{relatedTask.role} • {relatedTask.status}</p>
                            </div>
                            <button
                              onClick={() => handleRemoveRelatedTask(taskId)}
                              className="text-red-600 hover:text-red-800 p-1"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>

              {/* Sidebar - Right column */}
              <div className="space-y-6">
                {/* Task Details */}
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-4">Task Details</h4>
                  
                  <div className="space-y-4">
                    {/* Priority */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">Priority</label>
                      <select
                        value={editTaskPriority}
                        onChange={(e) => setEditTaskPriority(e.target.value as Task['priority'])}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                    </div>

                    {/* Due Date */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">Due Date</label>
                      <input
                        type="date"
                        value={editTaskDueDate}
                        onChange={(e) => setEditTaskDueDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                    </div>

                    {/* Assignee */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">Assignee</label>
                      <input
                        type="text"
                        value={editTaskAssignee}
                        onChange={(e) => setEditTaskAssignee(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        placeholder="Enter name..."
                      />
                    </div>

                    {/* Level */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">Level</label>
                      <select
                        value={editTaskLevel}
                        onChange={(e) => setEditTaskLevel(Number(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      >
                        <option value={1}>Company</option>
                        <option value={2}>Battalion</option>
                        <option value={3}>Brigade</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-3">
                  {/* Reassign Task */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Reassign to Role</label>
                    <select
                      onChange={(e) => e.target.value && handleReassignTask(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      defaultValue=""
                    >
                      <option value="">Select role...</option>
                      {Object.keys(FUSION_ROLES).map(role => (
                        <option key={role} value={role}>{role}</option>
                      ))}
                    </select>
                  </div>

                  {/* Push to Next Level */}
                  <button
                    onClick={handlePushTaskToNextLevel}
                    disabled={selectedTask.level >= 3}
                    className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
                  >
                    <ArrowRight className="w-4 h-4" />
                    Push to {selectedTask.level < 3 ? getLevelLabel(selectedTask.level + 1) : 'Next Level'}
                  </button>

                  {/* Save Changes */}
                  <button
                    onClick={handleSaveTaskDetails}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-blue-700 flex items-center justify-center gap-2 text-sm"
                  >
                    <Save className="w-4 h-4" />
                    Save Changes
                  </button>

                  {/* Delete Task */}
                  <button
                    onClick={() => handleDeleteTask(selectedTask.id)}
                    className="w-full bg-red-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-red-700 flex items-center justify-center gap-2 text-sm"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete Task
                  </button>
                </div>

                {/* Metadata */}
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 text-xs text-gray-600">
                  <p className="mb-1"><strong>Created:</strong> {new Date(selectedTask.createdAt).toLocaleString()}</p>
                  <p><strong>Updated:</strong> {new Date(selectedTask.updatedAt).toLocaleString()}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FusionTeamDashboard;
