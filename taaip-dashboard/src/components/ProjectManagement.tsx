import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { 
  Folder, Calendar, CheckCircle, AlertCircle, Clock, DollarSign, Users, 
  TrendingUp, PlayCircle, PauseCircle, XCircle, RefreshCw, Plus, Edit, 
  Target, Briefcase, ListTodo, Flag, Download
} from 'lucide-react';
import { ProjectEditor } from './ProjectEditor';
import { RSIDFilter } from './RSIDFilter';

const COLORS = {
  planning: '#6366f1',
  in_progress: '#3b82f6',
  at_risk: '#f59e0b',
  blocked: '#ef4444',
  completed: '#10b981',
  on_hold: '#94a3b8',
  canceled: '#64748b',
};

const STATUS_ICONS = {
  planning: <Clock className="w-4 h-4" />,
  in_progress: <PlayCircle className="w-4 h-4" />,
  at_risk: <AlertCircle className="w-4 h-4" />,
  blocked: <XCircle className="w-4 h-4" />,
  completed: <CheckCircle className="w-4 h-4" />,
  on_hold: <PauseCircle className="w-4 h-4" />,
  canceled: <XCircle className="w-4 h-4" />,
};

const TASK_STATUS_COLORS = {
  open: '#3b82f6',
  in_progress: '#f59e0b',
  blocked: '#ef4444',
  completed: '#10b981',
};

interface Project {
  project_id: string;
  name: string;
  status: string;
  start_date: string;
  target_date: string;
  owner_id: string;
  percent_complete: number;
  funding_amount: number;
  spent_amount: number;
  objectives: string;
  risk_level?: string;
  next_milestone?: string;
  blockers?: string;
}

interface Task {
  task_id: string;
  project_id: string;
  title: string;
  description: string;
  assigned_to: string;
  due_date: string;
  status: string;
  priority: string;
  completion_date?: string;
}

interface Milestone {
  milestone_id: string;
  project_id: string;
  name: string;
  target_date: string;
  actual_date?: string;
}

interface DashboardSummary {
  summary: {
    total_projects: number;
    active_projects: number;
    completed_projects: number;
    at_risk_projects: number;
    total_tasks: number;
    completed_tasks: number;
    blocked_tasks: number;
    task_completion_rate: number;
    total_budget: number;
    total_spent: number;
    budget_remaining: number;
    budget_utilization: number;
  };
  recent_projects: Project[];
  status_distribution: Array<{ status: string; count: number }>;
}

interface ProjectDetail {
  project: Project;
  tasks: Task[];
  milestones: Milestone[];
  statistics: {
    total_tasks: number;
    completed_tasks: number;
    in_progress_tasks: number;
    blocked_tasks: number;
    completion_rate: number;
    funding_amount: number;
    spent_amount: number;
    remaining_budget: number;
    budget_utilized: number;
  };
}

export const ProjectManagement: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'dashboard' | 'list' | 'detail'>('dashboard');
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [editingProject, setEditingProject] = useState<string | null>(null);
  const [filterRSID, setFilterRSID] = useState<string | null>(null);
  
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectDetail, setProjectDetail] = useState<ProjectDetail | null>(null);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v2/projects/dashboard/summary');
      const data = await res.json();
      if (data.status === 'ok') {
        setDashboardData(data);
      } else {
        console.error('Dashboard API returned error:', data);
      }
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      // Set empty dashboard data so page isn't stuck loading
      setDashboardData({
        summary: {
          total_projects: 0,
          active_projects: 0,
          completed_projects: 0,
          at_risk_projects: 0,
          total_tasks: 0,
          completed_tasks: 0,
          blocked_tasks: 0,
          task_completion_rate: 0,
          total_budget: 0,
          total_spent: 0,
          budget_remaining: 0,
          budget_utilization: 0,
        },
        recent_projects: [],
        status_distribution: []
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v2/projects');
      const data = await res.json();
      if (data.status === 'ok') {
        setProjects(data.projects);
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

  const fetchProjectDetail = async (projectId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v2/projects/${projectId}`);
      const data = await res.json();
      if (data.status === 'ok') {
        setProjectDetail(data);
      }
    } catch (error) {
      console.error('Error fetching project detail:', error);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchProjectDetail(selectedProject);
    }
  }, [selectedProject]);

  const handleProjectClick = (projectId: string) => {
    setSelectedProject(projectId);
    setView('detail');
  };

  const handleBackToDashboard = () => {
    setView('dashboard');
    setSelectedProject(null);
    setProjectDetail(null);
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedProject(null);
    setProjectDetail(null);
  };

  // Debug: Always show something
  console.log('ProjectManagement render:', { loading, dashboardData: !!dashboardData, view });

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-96 bg-white rounded-lg shadow p-8">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-lg text-gray-600">Loading project data...</span>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-96 bg-white rounded-lg shadow p-8">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-800 mb-2">No Data Available</h2>
          <p className="text-gray-600 mb-4">Unable to load project dashboard data.</p>
          <button
            onClick={fetchDashboard}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Briefcase className="w-8 h-8 text-blue-600" />
            Project Management
          </h1>
          <p className="text-gray-600 mt-1">
            Track events, marketing campaigns, and initiatives from start to finish
          </p>
        </div>
        <div className="flex gap-3">
          <RSIDFilter 
            onFilterChange={(rsid, level) => {
              setFilterRSID(rsid);
              // Refresh data with filter
              fetchDashboard();
              fetchProjects();
            }}
            currentRSID={filterRSID}
          />
          {view !== 'dashboard' && (
            <button
              onClick={handleBackToDashboard}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Dashboard
            </button>
          )}
          {view !== 'list' && (
            <button
              onClick={() => setView('list')}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              All Projects
            </button>
          )}
          <button
            onClick={() => {
              fetchDashboard();
              fetchProjects();
              if (selectedProject) fetchProjectDetail(selectedProject);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => window.open(`http://localhost:8000/api/v2/export/projects?rsid=${filterRSID || ''}`, '_blank')}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Views */}
      {view === 'dashboard' && dashboardData && (
        <DashboardView data={dashboardData} onProjectClick={handleProjectClick} />
      )}
      {view === 'list' && (
        <ProjectListView projects={projects} onProjectClick={handleProjectClick} />
      )}
      {view === 'detail' && projectDetail && (
        <ProjectDetailView 
          data={projectDetail} 
          onBack={handleBackToList}
          onEdit={() => setEditingProject(selectedProject)}
        />
      )}

      {/* Editor Modal */}
      {editingProject && (
        <ProjectEditor
          projectId={editingProject}
          onClose={() => {
            setEditingProject(null);
            // Refresh data after editing
            fetchDashboard();
            fetchProjects();
            if (selectedProject) fetchProjectDetail(selectedProject);
          }}
        />
      )}
    </div>
  );
};

// Dashboard View
const DashboardView: React.FC<{ data: DashboardSummary; onProjectClick: (id: string) => void }> = ({ data, onProjectClick }) => {
  const { summary, recent_projects, status_distribution } = data;

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg" title="Total number of projects across all statuses">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Total Projects</p>
              <p className="text-3xl font-bold mt-1">{summary.total_projects}</p>
            </div>
            <Folder className="w-12 h-12 text-blue-200 opacity-50" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg" title="Projects currently in progress or planning phase">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Active Projects</p>
              <p className="text-3xl font-bold mt-1">{summary.active_projects}</p>
            </div>
            <PlayCircle className="w-12 h-12 text-green-200 opacity-50" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg" title="Projects with identified risks or behind schedule">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm">At Risk</p>
              <p className="text-3xl font-bold mt-1">{summary.at_risk_projects}</p>
            </div>
            <AlertCircle className="w-12 h-12 text-orange-200 opacity-50" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg" title="Projects that have been successfully finished">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Completed</p>
              <p className="text-3xl font-bold mt-1">{summary.completed_projects}</p>
            </div>
            <CheckCircle className="w-12 h-12 text-purple-200 opacity-50" />
          </div>
        </div>
      </div>

      {/* Task & Budget Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Statistics */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2" title="Summary of all tasks across all projects">
            <ListTodo className="w-5 h-5 text-blue-600" />
            Task Overview
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600" title="Total number of tasks in all projects">Total Tasks</span>
              <span className="text-2xl font-bold text-gray-800">{summary.total_tasks}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600" title="Tasks that have been finished">Completed</span>
              <span className="text-xl font-semibold text-green-600">{summary.completed_tasks}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600" title="Tasks that are stuck or waiting on dependencies">Blocked</span>
              <span className="text-xl font-semibold text-red-600">{summary.blocked_tasks}</span>
            </div>
            <div className="pt-4 border-t border-gray-200">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600" title="Percentage of all tasks that have been completed">Completion Rate</span>
                <span className="font-semibold">{summary.task_completion_rate}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all"
                  style={{ width: `${summary.task_completion_rate}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Budget Statistics */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2" title="Financial summary across all projects">
            <DollarSign className="w-5 h-5 text-green-600" />
            Budget Overview
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600" title="Total funding allocated across all projects">Total Budget</span>
              <span className="text-2xl font-bold text-gray-800">${summary.total_budget.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600" title="Total amount spent across all projects">Spent</span>
              <span className="text-xl font-semibold text-blue-600">${summary.total_spent.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Remaining</span>
              <span className="text-xl font-semibold text-green-600">${summary.budget_remaining.toLocaleString()}</span>
            </div>
            <div className="pt-4 border-t border-gray-200">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Budget Utilization</span>
                <span className="font-semibold">{summary.budget_utilization}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${
                    summary.budget_utilization > 90 ? 'bg-red-500' :
                    summary.budget_utilization > 75 ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`}
                  style={{ width: `${summary.budget_utilization}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Projects by Status */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Projects by Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={status_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ status, count }) => `${status}: ${count}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {status_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.status as keyof typeof COLORS] || '#94a3b8'} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Project Progress */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Projects Progress</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={recent_projects.slice(0, 5)} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} unit="%" />
              <YAxis dataKey="name" type="category" width={120} fontSize={11} />
              <Tooltip />
              <Bar dataKey="percent_complete" fill="#3b82f6" name="Progress %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Projects Table */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-800">Recent Projects</h3>
          <button
            onClick={() => {}}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            View All →
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase" title="Project name and identifier">Project</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase" title="Current project status">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase" title="Overall completion percentage">Progress</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase" title="Total allocated funding">Budget</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase" title="Amount of budget spent">Spent</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase" title="Project start and target completion dates">Timeline</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {recent_projects.map((project) => (
                <tr key={project.project_id} className="hover:bg-gray-50 cursor-pointer" onClick={() => onProjectClick(project.project_id)}>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{project.name}</td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs font-semibold rounded-full"
                      style={{
                        backgroundColor: (COLORS[project.status as keyof typeof COLORS] || '#94a3b8') + '20',
                        color: COLORS[project.status as keyof typeof COLORS] || '#94a3b8',
                      }}
                    >
                      {STATUS_ICONS[project.status as keyof typeof STATUS_ICONS]}
                      {project.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${project.percent_complete || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{project.percent_complete || 0}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">
                    ${(project.funding_amount || 0).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-right text-gray-900">
                    ${(project.spent_amount || 0).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(project.start_date).toLocaleDateString()} - {new Date(project.target_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onProjectClick(project.project_id);
                      }}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Project List View
const ProjectListView: React.FC<{ projects: Project[]; onProjectClick: (id: string) => void }> = ({ projects, onProjectClick }) => {
  const [filter, setFilter] = useState<string>('all');
  
  const filteredProjects = filter === 'all' 
    ? projects 
    : projects.filter(p => p.status === filter);

  return (
    <div className="space-y-4">
      {/* Filter Buttons */}
      <div className="flex gap-2 flex-wrap">
        {['all', 'planning', 'in_progress', 'at_risk', 'blocked', 'completed', 'on_hold', 'canceled'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              filter === status
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status === 'all' ? 'All Projects' : status.replace('_', ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredProjects.map((project) => (
          <div
            key={project.project_id}
            onClick={() => onProjectClick(project.project_id)}
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-xl transition-all cursor-pointer border-l-4"
            style={{ borderLeftColor: COLORS[project.status as keyof typeof COLORS] || '#94a3b8' }}
          >
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-semibold text-gray-800 line-clamp-2">{project.name}</h3>
              <span
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-full"
                style={{
                  backgroundColor: (COLORS[project.status as keyof typeof COLORS] || '#94a3b8') + '20',
                  color: COLORS[project.status as keyof typeof COLORS] || '#94a3b8',
                }}
              >
                {STATUS_ICONS[project.status as keyof typeof STATUS_ICONS]}
              </span>
            </div>
            
            <p className="text-sm text-gray-600 mb-4 line-clamp-2">{project.objectives}</p>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Progress</span>
                <span className="font-semibold">{project.percent_complete || 0}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${project.percent_complete || 0}%` }}
                />
              </div>
              
              <div className="flex justify-between text-sm pt-2">
                <span className="text-gray-500">Budget</span>
                <span className="font-semibold text-green-600">
                  ${(project.spent_amount || 0).toLocaleString()} / ${(project.funding_amount || 0).toLocaleString()}
                </span>
              </div>
              
              <div className="flex justify-between text-sm pt-2">
                <span className="text-gray-500">Due</span>
                <span className="font-semibold text-gray-700">
                  {new Date(project.target_date).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Project Detail View
const ProjectDetailView: React.FC<{ data: ProjectDetail; onBack: () => void; onEdit: () => void }> = ({ data, onBack, onEdit }) => {
  const { project, tasks, milestones, statistics } = data;

  // Calculate days until deadline
  const daysUntilDeadline = Math.ceil(
    (new Date(project.target_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  );

  // Prepare task status data for chart
  const taskStatusData = [
    { status: 'Open', count: tasks.filter(t => t.status === 'open').length, color: TASK_STATUS_COLORS.open },
    { status: 'In Progress', count: tasks.filter(t => t.status === 'in_progress').length, color: TASK_STATUS_COLORS.in_progress },
    { status: 'Blocked', count: tasks.filter(t => t.status === 'blocked').length, color: TASK_STATUS_COLORS.blocked },
    { status: 'Completed', count: tasks.filter(t => t.status === 'completed').length, color: TASK_STATUS_COLORS.completed },
  ].filter(item => item.count > 0);

  return (
    <div className="space-y-6">
      {/* Project Header */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">{project.name}</h2>
            <p className="text-gray-600">{project.objectives}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onEdit}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Edit className="w-4 h-4" />
              Edit Project
            </button>
            <span
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-full"
              style={{
                backgroundColor: (COLORS[project.status as keyof typeof COLORS] || '#94a3b8') + '20',
                color: COLORS[project.status as keyof typeof COLORS] || '#94a3b8',
              }}
            >
              {STATUS_ICONS[project.status as keyof typeof STATUS_ICONS]}
              {project.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="flex items-center gap-3">
            <Briefcase className="w-8 h-8 text-purple-500" />
            <div>
              <p className="text-xs text-gray-500" title="Project Reference ID - Unique identifier for this project">PRID</p>
              <p className="text-sm font-semibold font-mono">{project.project_id}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Calendar className="w-8 h-8 text-blue-500" />
            <div>
              <p className="text-xs text-gray-500" title="Date when project was initiated">Start Date</p>
              <p className="text-sm font-semibold">{new Date(project.start_date).toLocaleDateString()}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Flag className="w-8 h-8 text-orange-500" />
            <div>
              <p className="text-xs text-gray-500" title="Expected completion date for this project">Target Date</p>
              <p className="text-sm font-semibold">{new Date(project.target_date).toLocaleDateString()}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Clock className="w-8 h-8 text-purple-500" />
            <div>
              <p className="text-xs text-gray-500" title="Number of days until target completion">Days Remaining</p>
              <p className={`text-sm font-semibold ${daysUntilDeadline < 0 ? 'text-red-600' : 'text-gray-800'}`}>
                {daysUntilDeadline} days
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div className="flex items-center gap-3">
            <Users className="w-8 h-8 text-green-500" />
            <div>
              <p className="text-xs text-gray-500" title="Project Owner DOD ID - Department of Defense Identification Number">Owner DODID</p>
              <p className="text-sm font-semibold font-mono">{project.owner_id}</p>
            </div>
          </div>
          
          {project.risk_level && (
            <div className="flex items-center gap-3">
              <AlertCircle className="w-8 h-8 text-red-500" />
              <div>
                <p className="text-xs text-gray-500" title="Current risk assessment level for project completion">Risk Level</p>
                <p className="text-sm font-semibold uppercase">{project.risk_level}</p>
              </div>
            </div>
          )}
          
          {project.next_milestone && (
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-indigo-500" />
              <div>
                <p className="text-xs text-gray-500" title="Next upcoming milestone or deliverable">Next Milestone</p>
                <p className="text-sm font-semibold">{project.next_milestone}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Progress & Budget Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2" title="Overall project completion metrics and task breakdown">
            <Target className="w-5 h-5 text-blue-600" />
            Project Progress
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600" title="Percentage of project work completed">Overall Completion</span>
                <span className="font-bold text-gray-800">{project.percent_complete || 0}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-gradient-to-r from-blue-500 to-green-500 h-4 rounded-full transition-all"
                  style={{ width: `${project.percent_complete || 0}%` }}
                />
              </div>
            </div>
            
            <div className="pt-4 border-t border-gray-200 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600" title="Total number of tasks in this project">Total Tasks</span>
                <span className="font-semibold">{statistics.total_tasks}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600" title="Tasks that have been finished">Completed</span>
                <span className="font-semibold text-green-600">{statistics.completed_tasks}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600" title="Tasks currently being worked on">In Progress</span>
                <span className="font-semibold text-blue-600">{statistics.in_progress_tasks}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600" title="Tasks that are stuck or waiting on dependencies">Blocked</span>
                <span className="font-semibold text-red-600">{statistics.blocked_tasks}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2" title="Financial tracking including budget allocation, spending, and burn rate">
            <DollarSign className="w-5 h-5 text-green-600" />
            Budget Tracking
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600" title="Percentage of total budget that has been spent">Budget Utilization</span>
                <span className="font-bold text-gray-800">{statistics.budget_utilized}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className={`h-4 rounded-full transition-all ${
                    statistics.budget_utilized > 90 ? 'bg-red-500' :
                    statistics.budget_utilized > 75 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${statistics.budget_utilized}%` }}
                />
              </div>
            </div>
            
            <div className="pt-4 border-t border-gray-200 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600" title="Total funding allocated for this project">Total Budget</span>
                <span className="font-semibold text-gray-800">${statistics.funding_amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600" title="Amount of budget that has been spent">Spent</span>
                <span className="font-semibold text-blue-600">${statistics.spent_amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600" title="Amount of budget still available">Remaining</span>
                <span className="font-semibold text-green-600">${statistics.remaining_budget.toLocaleString()}</span>
              </div>
              <div className="flex justify-between pt-2 border-t">
                <span className="text-gray-600 font-medium" title="Average daily spending rate since project start">Burn Rate</span>
                <span className="font-semibold text-purple-600">
                  ${Math.round(statistics.spent_amount / ((Date.now() - new Date(project.start_date).getTime()) / (1000 * 60 * 60 * 24))).toLocaleString()}/day
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tasks and Milestones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Status Chart */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4" title="Visual breakdown of task statuses across the project">Task Status Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={taskStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ status, count }) => `${status}: ${count}`}
                outerRadius={70}
                fill="#8884d8"
                dataKey="count"
              >
                {taskStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Milestones Timeline */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2" title="Key project milestones and their completion status">
            <Flag className="w-5 h-5 text-orange-600" />
            Milestones ({milestones.length})
          </h3>
          <div className="space-y-3 max-h-48 overflow-y-auto">
            {milestones.length === 0 ? (
              <p className="text-gray-500 text-sm">No milestones defined</p>
            ) : (
              milestones.map((milestone) => (
                <div key={milestone.milestone_id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`w-2 h-2 rounded-full mt-2 ${milestone.actual_date ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">{milestone.name}</p>
                    <p className="text-xs text-gray-500">
                      Target: {new Date(milestone.target_date).toLocaleDateString()}
                      {milestone.actual_date && ` | Completed: ${new Date(milestone.actual_date).toLocaleDateString()}`}
                    </p>
                  </div>
                  {milestone.actual_date && <CheckCircle className="w-5 h-5 text-green-500" />}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2" title="Detailed task list with assignments, status, priority, and due dates">
            <ListTodo className="w-5 h-5 text-blue-600" />
            Tasks ({tasks.length})
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase" title="Task name and description">Task</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase" title="DOD ID of person assigned to this task">Assigned To (DODID)</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase" title="Current status of the task">Status</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase" title="Urgency level of the task">Priority</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase" title="Date when task should be completed">Due Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tasks.map((task) => (
                <tr key={task.task_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <p className="text-sm font-medium text-gray-900">{task.title}</p>
                    {task.description && <p className="text-xs text-gray-500 mt-1 line-clamp-1">{task.description}</p>}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-mono">{task.assigned_to || 'Unassigned'}</td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
                      style={{
                        backgroundColor: (TASK_STATUS_COLORS[task.status as keyof typeof TASK_STATUS_COLORS] || '#94a3b8') + '20',
                        color: TASK_STATUS_COLORS[task.status as keyof typeof TASK_STATUS_COLORS] || '#94a3b8',
                      }}
                    >
                      {task.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        task.priority === 'high' ? 'bg-red-100 text-red-800' :
                        task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {task.priority || 'normal'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Blockers/Risks */}
      {project.blockers && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-2 flex items-center gap-2" title="Current issues, blockers, or risks that may impact project success">
            <AlertCircle className="w-5 h-5" />
            Blockers & Risks
          </h3>
          <p className="text-red-700">{project.blockers}</p>
        </div>
      )}
    </div>
  );
};
