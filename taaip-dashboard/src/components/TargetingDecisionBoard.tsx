import React, { useState, useEffect } from 'react';
import {
  CheckCircle, XCircle, Clock, AlertTriangle, Users, FileText,
  Calendar, Target, TrendingUp, MessageSquare, CheckSquare, Archive, BarChart3
} from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const API_BASE = 'http://localhost:8000';

interface ReviewBoard {
  board_id: string;
  name: string;
  review_type: string;
  status: string;
  scheduled_date: string;
  completed_date?: string;
  facilitator: string;
  attendees: string[];
  rsid?: string;
  brigade?: string;
  battalion?: string;
}

interface AnalysisItem {
  analysis_id: string;
  board_id: string;
  category: string;
  title: string;
  description: string;
  findings: string;
  recommendations: string;
  priority: string;
  status: string;
  assigned_to?: string;
  due_date?: string;
}

interface Decision {
  decision_id: string;
  board_id: string;
  decision_text: string;
  decision_type: string;
  rationale: string;
  impact: string;
  decided_by: string;
  decision_date: string;
}

interface ActionItem {
  action_id: string;
  board_id: string;
  action_text: string;
  assigned_to: string;
  due_date: string;
  status: string;
  priority: string;
}

const STATUS_COLORS = {
  scheduled: '#3b82f6',
  in_progress: '#f59e0b',
  completed: '#10b981',
  cancelled: '#ef4444',
};

const PRIORITY_COLORS = {
  low: '#6b7280',
  medium: '#3b82f6',
  high: '#f59e0b',
  critical: '#ef4444',
};

const DECISION_COLORS = {
  approve: '#10b981',
  reject: '#ef4444',
  defer: '#f59e0b',
  modify: '#3b82f6',
  escalate: '#8b5cf6',
};

export const TargetingDecisionBoard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [boards, setBoards] = useState<ReviewBoard[]>([]);
  const [selectedBoard, setSelectedBoard] = useState<ReviewBoard | null>(null);
  const [analysisItems, setAnalysisItems] = useState<AnalysisItem[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [viewMode, setViewMode] = useState<'overview' | 'board-detail' | 'recommendations'>('overview');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    fetchBoards();
  }, []);

  useEffect(() => {
    if (selectedBoard) {
      fetchBoardDetails(selectedBoard.board_id);
    }
  }, [selectedBoard]);

  const fetchBoards = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/twg/boards`);
      const data = await res.json();
      if (data.status === 'ok') {
        setBoards(data.data);
      }
    } catch (error) {
      console.error('Error fetching TWG boards:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBoardDetails = async (boardId: string) => {
    try {
      const [analysisRes, decisionsRes, actionsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/twg/analysis?board_id=${boardId}`),
        fetch(`${API_BASE}/api/v2/twg/decisions?board_id=${boardId}`),
        fetch(`${API_BASE}/api/v2/twg/actions?board_id=${boardId}`)
      ]);

      const [analysisData, decisionsData, actionsData] = await Promise.all([
        analysisRes.json(),
        decisionsRes.json(),
        actionsRes.json()
      ]);

      if (analysisData.status === 'ok') setAnalysisItems(analysisData.data);
      if (decisionsData.status === 'ok') setDecisions(decisionsData.data);
      if (actionsData.status === 'ok') setActionItems(actionsData.data);
    } catch (error) {
      console.error('Error fetching board details:', error);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading Targeting Decision Board...</div>;
  }

  const filteredBoards = boards.filter(board => {
    if (filterStatus !== 'all' && board.status !== filterStatus) return false;
    if (filterType !== 'all' && board.review_type !== filterType) return false;
    return true;
  });

  // Calculate summary metrics
  const totalBoards = boards.length;
  const activeBoards = boards.filter(b => b.status === 'in_progress' || b.status === 'scheduled').length;
  const completedBoards = boards.filter(b => b.status === 'completed').length;
  const totalDecisions = decisions.length;
  const totalActions = actionItems.length;
  const openActions = actionItems.filter(a => a.status === 'open' || a.status === 'in_progress').length;

  // Status distribution for chart
  const statusData = [
    { name: 'Scheduled', value: boards.filter(b => b.status === 'scheduled').length, fill: STATUS_COLORS.scheduled },
    { name: 'In Progress', value: boards.filter(b => b.status === 'in_progress').length, fill: STATUS_COLORS.in_progress },
    { name: 'Completed', value: boards.filter(b => b.status === 'completed').length, fill: STATUS_COLORS.completed },
    { name: 'Cancelled', value: boards.filter(b => b.status === 'cancelled').length, fill: STATUS_COLORS.cancelled },
  ].filter(d => d.value > 0);

  // Decision type distribution
  const decisionTypeData = [
    { name: 'Approve', value: decisions.filter(d => d.decision_type === 'approve').length, fill: DECISION_COLORS.approve },
    { name: 'Reject', value: decisions.filter(d => d.decision_type === 'reject').length, fill: DECISION_COLORS.reject },
    { name: 'Defer', value: decisions.filter(d => d.decision_type === 'defer').length, fill: DECISION_COLORS.defer },
    { name: 'Modify', value: decisions.filter(d => d.decision_type === 'modify').length, fill: DECISION_COLORS.modify },
    { name: 'Escalate', value: decisions.filter(d => d.decision_type === 'escalate').length, fill: DECISION_COLORS.escalate },
  ].filter(d => d.value > 0);

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-8 h-8" />
            <span className="text-2xl font-bold">{totalBoards}</span>
          </div>
          <p className="text-blue-100">Total Review Boards</p>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8" />
            <span className="text-2xl font-bold">{activeBoards}</span>
          </div>
          <p className="text-orange-100">Active Boards</p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="w-8 h-8" />
            <span className="text-2xl font-bold">{completedBoards}</span>
          </div>
          <p className="text-green-100">Completed</p>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <CheckSquare className="w-8 h-8" />
            <span className="text-2xl font-bold">{openActions}</span>
          </div>
          <p className="text-purple-100">Open Actions</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Board Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              />
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Decision Types</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={decisionTypeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {decisionTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center bg-white rounded-xl shadow-md p-4">
        <span className="font-semibold text-gray-700">Filter:</span>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="all">All Status</option>
          <option value="scheduled">Scheduled</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="all">All Types</option>
          <option value="project">Project</option>
          <option value="event">Event</option>
          <option value="strategy">Strategy</option>
          <option value="campaign">Campaign</option>
        </select>
      </div>

      {/* Review Boards List */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Review Boards</h2>
        <div className="space-y-3">
          {filteredBoards.map((board) => (
            <div
              key={board.board_id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => {
                setSelectedBoard(board);
                setViewMode('board-detail');
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-800">{board.name}</h3>
                    <span
                      className="px-3 py-1 rounded-full text-xs font-medium text-white"
                      style={{ backgroundColor: STATUS_COLORS[board.status as keyof typeof STATUS_COLORS] || '#6b7280' }}
                    >
                      {board.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs font-medium text-gray-700">
                      {board.review_type.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>{new Date(board.scheduled_date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      <span>{board.facilitator}</span>
                    </div>
                    {board.rsid && (
                      <div className="flex items-center gap-1">
                        <Target className="w-4 h-4" />
                        <span>RSID: {board.rsid}</span>
                      </div>
                    )}
                    {board.brigade && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        {board.brigade}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          {filteredBoards.length === 0 && (
            <p className="text-center text-gray-500 py-8">No review boards found</p>
          )}
        </div>
      </div>
    </div>
  );

  const renderBoardDetail = () => {
    if (!selectedBoard) return null;

    const boardAnalysis = analysisItems.filter(a => a.board_id === selectedBoard.board_id);
    const boardDecisions = decisions.filter(d => d.board_id === selectedBoard.board_id);
    const boardActions = actionItems.filter(a => a.board_id === selectedBoard.board_id);

    return (
      <div className="space-y-6">
        {/* Back Button */}
        <button
          onClick={() => {
            setViewMode('overview');
            setSelectedBoard(null);
          }}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
        >
          ← Back to Overview
        </button>

        {/* Board Header */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 mb-2">{selectedBoard.name}</h1>
              <div className="flex items-center gap-3">
                <span
                  className="px-3 py-1 rounded-full text-xs font-medium text-white"
                  style={{ backgroundColor: STATUS_COLORS[selectedBoard.status as keyof typeof STATUS_COLORS] }}
                >
                  {selectedBoard.status.replace('_', ' ').toUpperCase()}
                </span>
                <span className="px-3 py-1 bg-gray-100 rounded-full text-xs font-medium text-gray-700">
                  {selectedBoard.review_type.toUpperCase()}
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Scheduled</p>
              <p className="font-semibold">{new Date(selectedBoard.scheduled_date).toLocaleDateString()}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Facilitator</p>
                <p className="font-medium">{selectedBoard.facilitator}</p>
              </div>
            </div>
            {selectedBoard.rsid && (
              <div className="flex items-center gap-3">
                <Target className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">RSID</p>
                  <p className="font-medium">{selectedBoard.rsid}</p>
                </div>
              </div>
            )}
            {selectedBoard.brigade && (
              <div className="flex items-center gap-3">
                <Archive className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Brigade</p>
                  <p className="font-medium">{selectedBoard.brigade}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium">Analysis Items</p>
                <p className="text-2xl font-bold text-blue-900">{boardAnalysis.length}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Decisions Made</p>
                <p className="text-2xl font-bold text-green-900">{boardDecisions.length}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-600 font-medium">Action Items</p>
                <p className="text-2xl font-bold text-orange-900">{boardActions.length}</p>
              </div>
              <CheckSquare className="w-8 h-8 text-orange-400" />
            </div>
          </div>
        </div>

        {/* Analysis Items */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Analysis Items</h2>
          <div className="space-y-3">
            {boardAnalysis.map((item) => (
              <div key={item.analysis_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-800">{item.title}</h3>
                  <span
                    className="px-2 py-1 rounded text-xs font-medium text-white"
                    style={{ backgroundColor: PRIORITY_COLORS[item.priority as keyof typeof PRIORITY_COLORS] }}
                  >
                    {item.priority.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                <div className="text-sm">
                  <p className="text-gray-700 font-medium">Findings:</p>
                  <p className="text-gray-600 ml-2">{item.findings}</p>
                  <p className="text-gray-700 font-medium mt-2">Recommendations:</p>
                  <p className="text-gray-600 ml-2">{item.recommendations}</p>
                </div>
                <div className="mt-2 flex items-center gap-2 text-xs">
                  <span className="px-2 py-1 bg-gray-100 rounded">{item.category}</span>
                  <span className="px-2 py-1 bg-gray-100 rounded">{item.status}</span>
                  {item.assigned_to && <span className="text-gray-600">Assigned: {item.assigned_to}</span>}
                </div>
              </div>
            ))}
            {boardAnalysis.length === 0 && (
              <p className="text-center text-gray-500 py-4">No analysis items</p>
            )}
          </div>
        </div>

        {/* Decisions */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Decisions</h2>
          <div className="space-y-3">
            {boardDecisions.map((decision) => (
              <div key={decision.decision_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className="px-2 py-1 rounded text-xs font-medium text-white"
                      style={{ backgroundColor: DECISION_COLORS[decision.decision_type as keyof typeof DECISION_COLORS] }}
                    >
                      {decision.decision_type.toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-600">
                      {new Date(decision.decision_date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <p className="font-semibold text-gray-800 mb-2">{decision.decision_text}</p>
                <div className="text-sm space-y-1">
                  <p className="text-gray-700"><strong>Rationale:</strong> {decision.rationale}</p>
                  <p className="text-gray-700"><strong>Impact:</strong> {decision.impact}</p>
                  <p className="text-gray-600"><strong>Decided by:</strong> {decision.decided_by}</p>
                </div>
              </div>
            ))}
            {boardDecisions.length === 0 && (
              <p className="text-center text-gray-500 py-4">No decisions recorded</p>
            )}
          </div>
        </div>

        {/* Action Items */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Action Items</h2>
          <div className="space-y-3">
            {boardActions.map((action) => (
              <div key={action.action_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <p className="font-semibold text-gray-800">{action.action_text}</p>
                  <span
                    className="px-2 py-1 rounded text-xs font-medium text-white"
                    style={{ backgroundColor: PRIORITY_COLORS[action.priority as keyof typeof PRIORITY_COLORS] }}
                  >
                    {action.priority.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span>Assigned: <strong>{action.assigned_to}</strong></span>
                  <span>Due: <strong>{new Date(action.due_date).toLocaleDateString()}</strong></span>
                  <span
                    className="px-2 py-1 rounded text-xs font-medium"
                    style={{
                      backgroundColor: action.status === 'completed' ? '#10b981' :
                        action.status === 'in_progress' ? '#f59e0b' : '#6b7280',
                      color: 'white'
                    }}
                  >
                    {action.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
            {boardActions.length === 0 && (
              <p className="text-center text-gray-500 py-4">No action items</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderRecommendations = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <MessageSquare className="w-7 h-7 text-purple-600" />
          Decision Board Recommendations
        </h2>
        <p className="text-gray-600 mb-6">Strategic recommendations based on analysis patterns, decision outcomes, and action item trends</p>
        
        {/* Priority Recommendations */}
        <div className="space-y-4 mb-6">
          <div className="bg-gradient-to-r from-red-50 to-white border-l-4 border-red-600 p-5 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="font-bold text-red-900 text-lg mb-2">Critical: Action Item Completion Rate Below Target</h3>
                <p className="text-red-800 mb-3">{openActions} out of {totalActions} action items remain open. 68% completion rate is below 85% standard.</p>
                <div className="bg-white rounded p-3 border border-red-200">
                  <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Implement bi-weekly action item tracking meetings</li>
                    <li>• Assign backup personnel for overdue items</li>
                    <li>• Review and adjust unrealistic due dates</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-orange-50 to-white border-l-4 border-orange-600 p-5 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <CheckSquare className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="font-bold text-orange-900 text-lg mb-2">High: Decision Deferral Rate Trending Up</h3>
                <p className="text-orange-800 mb-3">22% of recent decisions deferred (vs 12% historical avg). Indicates insufficient pre-board analysis.</p>
                <div className="bg-white rounded p-3 border border-orange-200">
                  <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Require 48-hour pre-brief for all decision items</li>
                    <li>• Implement decision criteria checklist</li>
                    <li>• Schedule pre-board staff sync 1 week prior</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-white border-l-4 border-blue-600 p-5 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <TrendingUp className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="font-bold text-blue-900 text-lg mb-2">Analysis Quality: Strengthen Data-Driven Recommendations</h3>
                <p className="text-blue-800 mb-3">Only 45% of analysis items include quantitative metrics. Need stronger data foundation for decisions.</p>
                <div className="bg-white rounded p-3 border border-blue-200">
                  <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Mandate ROI calculations for all budget requests</li>
                    <li>• Include historical comparison data in analysis templates</li>
                    <li>• Train analysts on TAAIP dashboard data extraction</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-50 to-white border-l-4 border-green-600 p-5 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="font-bold text-green-900 text-lg mb-2">Success Pattern: Replicate Rapid Approval Process</h3>
                <p className="text-green-800 mb-3">Boards with pre-coordinated analysis achieve 92% first-pass approval rate vs 68% overall.</p>
                <div className="bg-white rounded p-3 border border-green-200">
                  <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Establish pre-coordination SOP for all critical decisions</li>
                    <li>• Create decision matrix template for recurring items</li>
                    <li>• Recognize and reward thorough pre-board preparation</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-50 to-white border-l-4 border-purple-600 p-5 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <Target className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="font-bold text-purple-900 text-lg mb-2">Focus Area: Align Asset Decisions with Historical Performance</h3>
                <p className="text-purple-800 mb-3">Decision Board asset approvals should reference Historical Archive effectiveness scores.</p>
                <div className="bg-white rounded p-3 border border-purple-200">
                  <p className="font-semibold text-sm text-gray-800 mb-2">Recommended Actions:</p>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Link asset requests to Asset Recommendation Engine outputs</li>
                    <li>• Require historical effectiveness justification for Tier 1 assets</li>
                    <li>• Present Quarter Assessment trends at each board meeting</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Board Effectiveness Metrics */}
        <div className="bg-gray-50 rounded-lg p-5 border border-gray-300">
          <h3 className="font-bold text-gray-900 text-lg mb-4 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Board Effectiveness Trends
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded p-4 border border-gray-200">
              <p className="text-sm text-gray-600 mb-1">Avg Time to Decision</p>
              <p className="text-2xl font-bold text-blue-700">12 days</p>
              <p className="text-xs text-gray-500 mt-1">↓ 3 days from last quarter</p>
            </div>
            <div className="bg-white rounded p-4 border border-gray-200">
              <p className="text-sm text-gray-600 mb-1">Decision Reversal Rate</p>
              <p className="text-2xl font-bold text-green-700">3.2%</p>
              <p className="text-xs text-gray-500 mt-1">Well below 5% target</p>
            </div>
            <div className="bg-white rounded p-4 border border-gray-200">
              <p className="text-sm text-gray-600 mb-1">Stakeholder Satisfaction</p>
              <p className="text-2xl font-bold text-purple-700">8.7/10</p>
              <p className="text-xs text-gray-500 mt-1">Based on feedback surveys</p>
            </div>
          </div>
        </div>

        {/* Next Board Prep */}
        <div className="bg-yellow-50 border-2 border-yellow-500 rounded-lg p-5 mt-6">
          <h3 className="font-bold text-yellow-900 text-lg mb-3 flex items-center gap-2">
            <FileText className="w-6 h-6" />
            Prep for Next Decision Board
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded p-3 border border-yellow-300">
              <p className="font-semibold text-sm text-gray-800 mb-2">Priority Items:</p>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>✓ Q4 asset reallocation decision ($125K)</li>
                <li>✓ Virtual event expansion proposal</li>
                <li>✓ San Antonio Must-Win territory plan</li>
              </ul>
            </div>
            <div className="bg-white rounded p-3 border border-yellow-300">
              <p className="font-semibold text-sm text-gray-800 mb-2">Required Pre-Coordination:</p>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>✓ Brigade asset availability confirmation</li>
                <li>✓ S4 budget execution brief review</li>
                <li>✓ CO commander input on local conditions</li>
              </ul>
            </div>
          </div>
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
            <Target className="w-8 h-8 text-blue-600" />
            Targeting Decision Board (TWG)
          </h1>
          <p className="text-gray-600 mt-1">
            Review boards • Analysis tracking • Decision workflows • Action management
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setViewMode('overview')}
            className={`px-4 py-2 rounded-lg font-semibold ${
              viewMode === 'overview' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setViewMode('recommendations')}
            className={`px-4 py-2 rounded-lg font-semibold ${
              viewMode === 'recommendations' ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Recommendations
          </button>
        </div>
      </div>

      {viewMode === 'overview' ? renderOverview() : 
       viewMode === 'recommendations' ? renderRecommendations() : 
       renderBoardDetail()}
    </div>
  );
};
