import React, { useState, useMemo } from 'react';
import {
  ArrowLeft, CheckSquare, AlertCircle, Clock, Calendar, Filter, Search, TrendingUp
} from 'lucide-react';

interface Task {
  id: string;
  role: string;
  title: string;
  description?: string;
  status: 'not-started' | 'in-progress' | 'completed' | 'blocked' | 'review' | 'approved';
  dueDate: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignee?: string;
  level: number;
  comments?: any[];
  relatedTasks?: string[];
  createdAt?: string;
  updatedAt?: string;
}

interface DueTasksPageProps {
  role: string;
  tasks: Task[];
  onBack: () => void;
  teamMembers: any[];
}

const DueTasksPage: React.FC<DueTasksPageProps> = ({ role, tasks, onBack, teamMembers }) => {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterPriority, setFilterPriority] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'dueDate' | 'priority' | 'status'>('dueDate');

  const roleTasks = useMemo(() => {
    return tasks.filter(t => t.role === role);
  }, [tasks, role]);

  const filteredTasks = useMemo(() => {
    let result = [...roleTasks];

    if (filterStatus !== 'all') {
      result = result.filter(t => t.status === filterStatus);
    }

    if (filterPriority !== 'all') {
      result = result.filter(t => t.priority === filterPriority);
    }

    if (searchTerm) {
      result = result.filter(t =>
        t.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (t.description && t.description.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Sort tasks
    result.sort((a, b) => {
      if (sortBy === 'dueDate') {
        return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
      } else if (sortBy === 'priority') {
        const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        return priorityOrder[a.priority as keyof typeof priorityOrder] - 
               priorityOrder[b.priority as keyof typeof priorityOrder];
      } else {
        const statusOrder = { 
          'not-started': 0, 'blocked': 1, 'in-progress': 2, 
          'review': 3, 'approved': 4, 'completed': 5 
        };
        return (statusOrder[a.status as keyof typeof statusOrder] || 0) - 
               (statusOrder[b.status as keyof typeof statusOrder] || 0);
      }
    });

    return result;
  }, [roleTasks, filterStatus, filterPriority, searchTerm, sortBy]);

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'not-started': 'bg-gray-100 text-gray-800 border-gray-300',
      'in-progress': 'bg-blue-100 text-blue-800 border-blue-300',
      'completed': 'bg-green-100 text-green-800 border-green-300',
      'blocked': 'bg-red-100 text-red-800 border-red-300',
      'review': 'bg-purple-100 text-purple-800 border-purple-300',
      'approved': 'bg-teal-100 text-teal-800 border-teal-300'
    };
    return colors[status] || colors['not-started'];
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      'critical': 'text-red-700 bg-red-50 border-red-200',
      'high': 'text-orange-700 bg-orange-50 border-orange-200',
      'medium': 'text-yellow-700 bg-yellow-50 border-yellow-200',
      'low': 'text-green-700 bg-green-50 border-green-200'
    };
    return colors[priority] || colors['low'];
  };

  const isOverdue = (dueDate: string) => {
    return new Date(dueDate) < new Date() && dueDate !== '';
  };

  const member = teamMembers.find(m => m.role === role);

  const stats = {
    total: roleTasks.length,
    completed: roleTasks.filter(t => t.status === 'completed').length,
    inProgress: roleTasks.filter(t => t.status === 'in-progress').length,
    blocked: roleTasks.filter(t => t.status === 'blocked').length,
    overdue: roleTasks.filter(t => isOverdue(t.dueDate) && t.status !== 'completed').length
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Dashboard
            </button>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              {role} - Due Tasks & Status
            </h1>
            {member && (
              <p className="text-gray-600">
                Assigned to: <span className="font-semibold">{member.name}</span>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm font-semibold uppercase">Total Tasks</p>
            <p className="text-3xl font-bold text-blue-600">{stats.total}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
            <p className="text-gray-600 text-sm font-semibold uppercase">Completed</p>
            <p className="text-3xl font-bold text-green-600">{stats.completed}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
            <p className="text-gray-600 text-sm font-semibold uppercase">In Progress</p>
            <p className="text-3xl font-bold text-yellow-600">{stats.inProgress}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
            <p className="text-gray-600 text-sm font-semibold uppercase">Blocked</p>
            <p className="text-3xl font-bold text-red-600">{stats.blocked}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
            <p className="text-gray-600 text-sm font-semibold uppercase">Overdue</p>
            <p className="text-3xl font-bold text-orange-600">{stats.overdue}</p>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <Search className="w-4 h-4 inline mr-2" />
                Search Tasks
              </label>
              <input
                type="text"
                placeholder="Search by title or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Filter Status */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <Filter className="w-4 h-4 inline mr-2" />
                Status
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value="not-started">Not Started</option>
                <option value="in-progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="blocked">Blocked</option>
                <option value="review">Review</option>
                <option value="approved">Approved</option>
              </select>
            </div>

            {/* Filter Priority */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <TrendingUp className="w-4 h-4 inline mr-2" />
                Priority
              </label>
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Priorities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'dueDate' | 'priority' | 'status')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="dueDate">Due Date</option>
                <option value="priority">Priority</option>
                <option value="status">Status</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tasks List */}
        <div className="space-y-4">
          {filteredTasks.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <CheckSquare className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-600 text-lg font-semibold">No tasks found</p>
              <p className="text-gray-500 mt-2">
                {roleTasks.length === 0
                  ? `No tasks assigned to ${role}`
                  : 'Try adjusting your filters'}
              </p>
            </div>
          ) : (
            filteredTasks.map((task) => (
              <div
                key={task.id}
                className={`bg-white rounded-lg shadow p-6 border-l-4 transition-all hover:shadow-lg ${
                  isOverdue(task.dueDate) && task.status !== 'completed'
                    ? 'border-l-red-500 bg-red-50'
                    : 'border-l-blue-500'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {task.status === 'completed' && (
                        <CheckSquare className="w-5 h-5 text-green-600" />
                      )}
                      {isOverdue(task.dueDate) && task.status !== 'completed' && (
                        <AlertCircle className="w-5 h-5 text-red-600" />
                      )}
                      {task.status === 'blocked' && (
                        <AlertCircle className="w-5 h-5 text-red-600" />
                      )}
                      <h3 className="text-lg font-bold text-gray-800">{task.title}</h3>
                    </div>
                    {task.description && (
                      <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                  {/* Priority */}
                  <div>
                    <p className="text-xs text-gray-600 uppercase font-semibold mb-1">Priority</p>
                    <div className={`px-3 py-1 rounded border text-sm font-semibold inline-block ${getPriorityColor(task.priority)}`}>
                      {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                    </div>
                  </div>

                  {/* Due Date */}
                  <div>
                    <p className="text-xs text-gray-600 uppercase font-semibold mb-1">Due Date</p>
                    <div className={`flex items-center gap-1 text-sm font-semibold ${
                      isOverdue(task.dueDate) && task.status !== 'completed'
                        ? 'text-red-700'
                        : 'text-gray-700'
                    }`}>
                      <Calendar className="w-4 h-4" />
                      {new Date(task.dueDate).toLocaleDateString()}
                      {isOverdue(task.dueDate) && task.status !== 'completed' && (
                        <span className="text-red-600 font-bold ml-1">(OVERDUE)</span>
                      )}
                    </div>
                  </div>

                  {/* Assignee */}
                  {task.assignee && (
                    <div>
                      <p className="text-xs text-gray-600 uppercase font-semibold mb-1">Assignee</p>
                      <p className="text-sm font-semibold text-gray-700">{task.assignee}</p>
                    </div>
                  )}

                  {/* Level */}
                  <div>
                    <p className="text-xs text-gray-600 uppercase font-semibold mb-1">Level</p>
                    <p className="text-sm font-semibold text-gray-700">
                      {task.level === 1 ? 'Company' : task.level === 2 ? 'Battalion' : 'Brigade'}
                    </p>
                  </div>
                </div>

                {/* Progress indicator for in-progress tasks */}
                {task.status === 'in-progress' && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center gap-2 text-xs">
                      <Clock className="w-4 h-4 text-blue-600" />
                      <span className="text-gray-600">In Progress</span>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default DueTasksPage;
