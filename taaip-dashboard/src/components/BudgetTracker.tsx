import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingDown, TrendingUp, AlertCircle, CheckCircle, Calendar, Filter } from 'lucide-react';
import { API_BASE } from '../config/api';

interface BudgetAllocation {
  unit_id: string;
  unit_name: string;
  unit_type: 'battalion' | 'brigade';
  fiscal_year: number;
  total_budget: number;
  allocated: number;
  spent: number;
  remaining: number;
  utilization_rate: number;
  categories: {
    events: number;
    projects: number;
    operations: number;
    other: number;
  };
  transactions: BudgetTransaction[];
}

interface BudgetTransaction {
  id: string;
  date: string;
  type: 'event' | 'project' | 'operation' | 'other';
  description: string;
  amount: number;
  unit: string;
  status: 'approved' | 'pending' | 'completed';
}

export const BudgetTracker: React.FC = () => {
  const [budgets, setBudgets] = useState<BudgetAllocation[]>([]);
  const [transactions, setTransactions] = useState<BudgetTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState<string>('all');
  const [fiscalYear, setFiscalYear] = useState<number>(2025);
  const [viewMode, setViewMode] = useState<'overview' | 'detailed'>('overview');

  useEffect(() => {
    loadBudgetData();
  }, [fiscalYear, selectedUnit]);

  const loadBudgetData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
          `${API_BASE}/api/v2/budget/allocations?fiscal_year=${fiscalYear}${selectedUnit !== 'all' ? `&unit_id=${selectedUnit}` : ''}`
        );
      const data = await response.json();
      
      if (data.status === 'ok') {
        setBudgets(data.budgets || []);
        setTransactions(data.recent_transactions || []);
      }
    } catch (error) {
      console.error('Error loading budget data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTotalBudget = () => budgets.reduce((sum, b) => sum + b.total_budget, 0);
  const getTotalSpent = () => budgets.reduce((sum, b) => sum + b.spent, 0);
  const getTotalRemaining = () => budgets.reduce((sum, b) => sum + b.remaining, 0);
  const getOverallUtilization = () => {
    const total = getTotalBudget();
    return total > 0 ? (getTotalSpent() / total) * 100 : 0;
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getUtilizationColor = (rate: number): string => {
    if (rate < 50) return 'text-green-600';
    if (rate < 75) return 'text-yellow-600';
    if (rate < 90) return 'text-orange-600';
    return 'text-red-600';
  };

  const getUtilizationBgColor = (rate: number): string => {
    if (rate < 50) return 'bg-green-500';
    if (rate < 75) return 'bg-yellow-500';
    if (rate < 90) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-xl shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold uppercase tracking-wider flex items-center gap-3">
              <DollarSign className="w-8 h-8 text-yellow-500" />
              Budget Tracker
            </h1>
            <p className="text-gray-300 mt-2">FY {fiscalYear} Budget Allocation & Utilization</p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={fiscalYear}
              onChange={(e) => setFiscalYear(parseInt(e.target.value))}
              className="px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:ring-2 focus:ring-yellow-500"
            >
              <option value={2024}>FY 2024</option>
              <option value={2025}>FY 2025</option>
              <option value={2026}>FY 2026</option>
            </select>
            <button
              onClick={() => setViewMode(viewMode === 'overview' ? 'detailed' : 'overview')}
              className="px-4 py-2 bg-yellow-500 text-black font-semibold rounded-lg hover:bg-yellow-400"
            >
              {viewMode === 'overview' ? 'Detailed View' : 'Overview'}
            </button>
          </div>
        </div>
      </div>

      {/* Overall Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm uppercase font-semibold">Total Budget</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{formatCurrency(getTotalBudget())}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <DollarSign className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm uppercase font-semibold">Total Spent</p>
              <p className="text-3xl font-bold text-red-600 mt-2">{formatCurrency(getTotalSpent())}</p>
            </div>
            <div className="bg-red-100 p-3 rounded-lg">
              <TrendingDown className="w-8 h-8 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm uppercase font-semibold">Remaining</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{formatCurrency(getTotalRemaining())}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm uppercase font-semibold">Utilization</p>
              <p className={`text-3xl font-bold mt-2 ${getUtilizationColor(getOverallUtilization())}`}>
                {getOverallUtilization().toFixed(1)}%
              </p>
            </div>
            <div className={`${getOverallUtilization() > 90 ? 'bg-red-100' : 'bg-yellow-100'} p-3 rounded-lg`}>
              {getOverallUtilization() > 90 ? (
                <AlertCircle className="w-8 h-8 text-red-600" />
              ) : (
                <CheckCircle className="w-8 h-8 text-yellow-600" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl shadow-md p-4 mb-6">
        <div className="flex items-center gap-4">
          <Filter className="w-5 h-5 text-gray-500" />
          <select
            value={selectedUnit}
            onChange={(e) => setSelectedUnit(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
          >
            <option value="all">All Units</option>
            <optgroup label="Brigades">
              <option value="brigade_1">1st Brigade</option>
              <option value="brigade_2">2nd Brigade</option>
              <option value="brigade_3">3rd Brigade</option>
              <option value="brigade_4">4th Brigade</option>
              <option value="brigade_5">5th Brigade</option>
              <option value="brigade_6">6th Brigade</option>
            </optgroup>
            <optgroup label="Battalions">
              <option value="battalion_101">1-101 Battalion</option>
              <option value="battalion_102">1-102 Battalion</option>
              <option value="battalion_201">2-201 Battalion</option>
              <option value="battalion_202">2-202 Battalion</option>
              <option value="battalion_301">3-301 Battalion</option>
              <option value="battalion_401">4-401 Battalion</option>
              <option value="battalion_501">5-501 Battalion</option>
              <option value="battalion_601">6-601 Battalion</option>
            </optgroup>
          </select>
        </div>
      </div>

      {/* Budget Breakdown by Unit */}
      {viewMode === 'overview' ? (
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="bg-gray-100 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Budget by Unit</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Unit</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase">Type</th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-gray-700 uppercase">Total Budget</th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-gray-700 uppercase">Spent</th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-gray-700 uppercase">Remaining</th>
                  <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase">Utilization</th>
                  <th className="px-6 py-3 text-center text-xs font-bold text-gray-700 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {budgets.map((budget) => (
                  <tr key={budget.unit_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-900">{budget.unit_name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        budget.unit_type === 'brigade' 
                          ? 'bg-purple-100 text-purple-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {budget.unit_type.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-gray-900">
                      {formatCurrency(budget.total_budget)}
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-red-600">
                      {formatCurrency(budget.spent)}
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-green-600">
                      {formatCurrency(budget.remaining)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col items-center gap-2">
                        <span className={`font-bold ${getUtilizationColor(budget.utilization_rate)}`}>
                          {budget.utilization_rate.toFixed(1)}%
                        </span>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getUtilizationBgColor(budget.utilization_rate)}`}
                            style={{ width: `${Math.min(budget.utilization_rate, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      {budget.utilization_rate > 90 ? (
                        <AlertCircle className="w-6 h-6 text-red-600 mx-auto" />
                      ) : budget.utilization_rate > 75 ? (
                        <AlertCircle className="w-6 h-6 text-yellow-600 mx-auto" />
                      ) : (
                        <CheckCircle className="w-6 h-6 text-green-600 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Detailed View with Category Breakdown */
        <div className="space-y-6">
          {budgets.map((budget) => (
            <div key={budget.unit_id} className="bg-white rounded-xl shadow-md overflow-hidden">
              <div className="bg-gradient-to-r from-gray-700 to-gray-800 text-white px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold">{budget.unit_name}</h3>
                    <p className="text-gray-300 text-sm mt-1">
                      {budget.unit_type.toUpperCase()} • FY {budget.fiscal_year}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold">{formatCurrency(budget.remaining)}</p>
                    <p className="text-gray-300 text-sm">Remaining</p>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-blue-600 text-sm font-semibold uppercase">Events</p>
                    <p className="text-2xl font-bold text-blue-900 mt-2">
                      {formatCurrency(budget.categories.events)}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <p className="text-purple-600 text-sm font-semibold uppercase">Projects</p>
                    <p className="text-2xl font-bold text-purple-900 mt-2">
                      {formatCurrency(budget.categories.projects)}
                    </p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <p className="text-green-600 text-sm font-semibold uppercase">Operations</p>
                    <p className="text-2xl font-bold text-green-900 mt-2">
                      {formatCurrency(budget.categories.operations)}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-600 text-sm font-semibold uppercase">Other</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2">
                      {formatCurrency(budget.categories.other)}
                    </p>
                  </div>
                </div>

                {/* Recent Transactions for this unit */}
                <div className="border-t pt-4">
                  <h4 className="text-lg font-bold text-gray-900 mb-3">Recent Transactions</h4>
                  <div className="space-y-2">
                    {budget.transactions.slice(0, 5).map((transaction) => (
                      <div key={transaction.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                        <div className="flex items-center gap-3">
                          <Calendar className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="font-semibold text-gray-900">{transaction.description}</p>
                            <p className="text-xs text-gray-500">{transaction.date} • {transaction.type}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-red-600">-{formatCurrency(transaction.amount)}</p>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            transaction.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : transaction.status === 'approved'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {transaction.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto"></div>
            <p className="text-gray-900 mt-4">Loading budget data...</p>
          </div>
        </div>
      )}
    </div>
  );
};
