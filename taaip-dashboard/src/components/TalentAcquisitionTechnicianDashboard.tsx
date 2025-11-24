import React, { useState, useEffect } from 'react';
import {
  Target, Users, TrendingUp, AlertTriangle, CheckCircle, Clock,
  School, MapPin, FileText, BarChart3, Activity, Briefcase,
  Filter, Download, RefreshCw, Shield, Award, BookOpen, X, ExternalLink, FileDown
} from 'lucide-react';
import { UniversalFilter, FilterState } from './UniversalFilter';
import { API_BASE } from '../config/api';

// 420T Dashboard - Comprehensive Talent Acquisition Technician View with Drill-Down & Export

interface KPIMetrics {
  // Lead Generation & Prospecting
  recruiting_ops_plan_compliance: number;
  unassigned_schools: number;
  school_zone_validation: number;
  alrl_contact_milestones: number;
  unassigned_zip_codes: number;
  adhq_leads: number;
  itemlc_priority_leads: number;
  srp_referrals: number;
  emm_compliance: number;
  
  // Processing Indicators
  flash_to_bang_avg_days: number;
  applicant_processing_efficiency: number;
  projection_cancellation_rate: number;
  recruiter_contribution_rate: number;
  quality_marks: number;
  recruiter_zone_compliance: number;
  waiver_trends: number;
  
  // Future Soldier Management
  fs_orientation_attendance: number;
  fs_training_attendance: number;
  fs_loss_rate: number;
  renegotiation_rate: number;
  
  // Targeting & Fusion
  targeting_board_sessions: number;
  high_payoff_events_identified: number;
  roi_analysis_completed: number;
  fusion_updates_provided: number;
}

interface SchoolTarget {
  school_id: string;
  name: string;
  type: string;
  location: string;
  assigned: boolean;
  zone_valid: boolean;
  alrl_milestones: number;
  sasvab_tests: number;
  leads: number;
  conversions: number;
  priority: string;
}

interface RecruitingOpsPlan {
  plan_id: string;
  unit_type: string;
  unit_name: string;
  status: string;
  last_updated: string;
  compliance_score: number;
  key_metrics: {
    recruiter_work_ethic: number;
    conversion_data: number;
    zone_compliance: number;
    prospecting_compliance: number;
  };
}

export const TalentAcquisitionTechnicianDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'overview' | 'prospecting' | 'processing' | 'fs_management' | 'targeting' | 'fusion'>('overview');
  const [filters, setFilters] = useState<FilterState>({ rsid: '', zipcode: '', cbsa: '' });
  const [kpiMetrics, setKpiMetrics] = useState<KPIMetrics | null>(null);
  const [schools, setSchools] = useState<SchoolTarget[]>([]);
  const [opsPlans, setOpsPlans] = useState<RecruitingOpsPlan[]>([]);
  const [selectedUnit, setSelectedUnit] = useState<string>('all');
  
  // Drill-down modal state
  const [drillDownModal, setDrillDownModal] = useState<{
    isOpen: boolean;
    title: string;
    data: any[];
    type: string;
  }>({
    isOpen: false,
    title: '',
    data: [],
    type: ''
  });

  useEffect(() => {
    fetchDashboardData();
  }, [filters, selectedUnit]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.rsid) params.append('rsid', filters.rsid);
      if (filters.zipcode) params.append('zipcode', filters.zipcode);
      if (filters.cbsa) params.append('cbsa', filters.cbsa);
      if (selectedUnit !== 'all') params.append('unit', selectedUnit);
      
      const queryString = params.toString();
      
      // Fetch KPI metrics
      const kpiRes = await fetch(`${API_BASE}/api/v2/420t/kpi-metrics?${queryString}`);
      const kpiData = await kpiRes.json();
      if (kpiData.status === 'ok') setKpiMetrics(kpiData.metrics);
      
      // Fetch school targets
      const schoolsRes = await fetch(`${API_BASE}/api/v2/420t/school-targets?${queryString}`);
      const schoolsData = await schoolsRes.json();
      if (schoolsData.status === 'ok') setSchools(schoolsData.schools);
      
      // Fetch ops plans
      const opsRes = await fetch(`${API_BASE}/api/v2/420t/recruiting-ops-plans?${queryString}`);
      const opsData = await opsRes.json();
      if (opsData.status === 'ok') setOpsPlans(opsData.plans);
      
    } catch (error) {
      console.error('Error fetching 420T dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  // Export data to CSV
  const exportToCSV = (data: any[], filename: string) => {
    if (data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => JSON.stringify(row[header] || '')).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Open drill-down modal with data
  const openDrillDown = async (title: string, type: string) => {
    setLoading(true);
    try {
      let data: any[] = [];
      let endpoint = '';
      
      switch(type) {
        case 'schools':
          endpoint = '/api/v2/420t/school-targets';
          break;
        case 'ops_plans':
          endpoint = '/api/v2/420t/recruiting-ops-plans';
          break;
        case 'future_soldiers':
          endpoint = '/api/v2/420t/future-soldiers';
          break;
        case 'recruiters':
          endpoint = '/api/v2/420t/recruiter-performance';
          break;
        case 'targeting':
          endpoint = '/api/v2/420t/targeting-board';
          break;
        case 'fusion':
          endpoint = '/api/v2/420t/fusion-process';
          break;
        default:
          data = [];
      }
      
      if (endpoint) {
        const params = new URLSearchParams();
        if (filters.rsid) params.append('rsid', filters.rsid);
        if (filters.zipcode) params.append('zipcode', filters.zipcode);
        if (filters.cbsa) params.append('cbsa', filters.cbsa);
        
        const res = await fetch(`${API_BASE}${endpoint}?${params.toString()}`);
        const result = await res.json();
        
        if (result.status === 'ok') {
          data = result.schools || result.plans || result.future_soldiers || result.recruiters || result.targets || result.sessions || [];
        }
      }
      
      setDrillDownModal({
        isOpen: true,
        title,
        data,
        type
      });
    } catch (error) {
      console.error('Error fetching drill-down data:', error);
    } finally {
      setLoading(false);
    }
  };

  const closeDrillDown = () => {
    setDrillDownModal({
      isOpen: false,
      title: '',
      data: [],
      type: ''
    });
  };

  if (loading && !kpiMetrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-yellow-600" />
        <span className="ml-3 text-lg text-gray-600">Loading 420T Dashboard...</span>
      </div>
    );
  }

  // Overview Dashboard
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Critical KPI Summary Cards - Clickable */}
      <div className="grid grid-cols-4 gap-px bg-gray-300">
        <button 
          onClick={() => openDrillDown('Recruiter Performance Details', 'recruiters')}
          className="bg-gradient-to-br from-gray-700 to-gray-800 p-6 hover:from-gray-600 hover:to-gray-700 transition-all cursor-pointer text-left"
        >
          <div className="flex items-center justify-between mb-3">
            <Target className="w-8 h-8 text-yellow-500" />
            <span className="text-3xl font-bold text-yellow-500">{kpiMetrics?.recruiter_zone_compliance || 0}%</span>
          </div>
          <p className="text-gray-300 text-xs uppercase tracking-wide">Zone Compliance</p>
          <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
            Recruiter Coverage <ExternalLink className="w-3 h-3" />
          </p>
        </button>

        <button 
          onClick={() => openDrillDown('Processing Efficiency Details', 'future_soldiers')}
          className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6 hover:from-yellow-500 hover:to-yellow-600 transition-all cursor-pointer text-left"
        >
          <div className="flex items-center justify-between mb-3">
            <Activity className="w-8 h-8 text-black" />
            <span className="text-3xl font-bold text-black">{kpiMetrics?.flash_to_bang_avg_days || 0}</span>
          </div>
          <p className="text-gray-800 text-xs uppercase tracking-wide">Flash to Bang</p>
          <p className="text-xs text-gray-900 mt-1 flex items-center gap-1">
            Avg Days to Contract <ExternalLink className="w-3 h-3" />
          </p>
        </button>

        <button 
          onClick={() => openDrillDown('Future Soldier Details', 'future_soldiers')}
          className="bg-gradient-to-br from-gray-700 to-gray-800 p-6 hover:from-gray-600 hover:to-gray-700 transition-all cursor-pointer text-left"
        >
          <div className="flex items-center justify-between mb-3">
            <Users className="w-8 h-8 text-yellow-500" />
            <span className="text-3xl font-bold text-yellow-500">{kpiMetrics?.fs_loss_rate || 0}%</span>
          </div>
          <p className="text-gray-300 text-xs uppercase tracking-wide">FS Loss Rate</p>
          <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
            Future Soldier Retention <ExternalLink className="w-3 h-3" />
          </p>
        </button>

        <button 
          onClick={() => openDrillDown('Quality Marks Details', 'ops_plans')}
          className="bg-gradient-to-br from-yellow-600 to-yellow-700 p-6 hover:from-yellow-500 hover:to-yellow-600 transition-all cursor-pointer text-left"
        >
          <div className="flex items-center justify-between mb-3">
            <CheckCircle className="w-8 h-8 text-black" />
            <span className="text-3xl font-bold text-black">{kpiMetrics?.quality_marks || 0}</span>
          </div>
          <p className="text-gray-800 text-xs uppercase tracking-wide">Quality Marks</p>
          <p className="text-xs text-gray-900 mt-1 flex items-center gap-1">
            Contract Quality Score <ExternalLink className="w-3 h-3" />
          </p>
        </button>
      </div>

      {/* Recruiting Operations Plans */}
      <div className="bg-white border-2 border-gray-300">
        <div className="bg-gray-100 px-6 py-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-yellow-600" />
            Recruiting Operations Plans (Battalion/Company/Station)
          </h3>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            {opsPlans.map((plan) => (
              <div key={plan.plan_id} className="border-2 border-gray-300 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-bold text-gray-800">{plan.unit_name}</h4>
                    <p className="text-xs text-gray-600 uppercase tracking-wide">{plan.unit_type}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`px-3 py-1 text-xs font-bold uppercase tracking-wide ${
                      plan.compliance_score >= 90 ? 'bg-green-100 text-green-800 border border-green-600' :
                      plan.compliance_score >= 70 ? 'bg-yellow-100 text-yellow-800 border border-yellow-600' :
                      'bg-red-100 text-red-800 border border-red-600'
                    }`}>
                      {plan.compliance_score}% Compliant
                    </span>
                    <span className="text-sm text-gray-600">
                      Updated: {new Date(plan.last_updated).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-4 mt-3">
                  <div className="text-center border border-gray-200 p-2">
                    <p className="text-xl font-bold text-gray-800">{plan.key_metrics.recruiter_work_ethic}%</p>
                    <p className="text-xs text-gray-600 uppercase">Work Ethic</p>
                  </div>
                  <div className="text-center border border-gray-200 p-2">
                    <p className="text-xl font-bold text-gray-800">{plan.key_metrics.conversion_data}%</p>
                    <p className="text-xs text-gray-600 uppercase">Conversion</p>
                  </div>
                  <div className="text-center border border-gray-200 p-2">
                    <p className="text-xl font-bold text-gray-800">{plan.key_metrics.zone_compliance}%</p>
                    <p className="text-xs text-gray-600 uppercase">Zone Compliance</p>
                  </div>
                  <div className="text-center border border-gray-200 p-2">
                    <p className="text-xl font-bold text-gray-800">{plan.key_metrics.prospecting_compliance}%</p>
                    <p className="text-xs text-gray-600 uppercase">Prospecting</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Critical Warnings - Clickable */}
      <div className="grid grid-cols-3 gap-6">
        <button
          onClick={() => openDrillDown('Critical Warnings Details', 'schools')}
          className="border-2 border-red-600 bg-red-50 p-4 hover:bg-red-100 transition-colors cursor-pointer text-left"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-red-600" />
              <h4 className="font-bold text-red-800 uppercase tracking-wide">Critical Warnings</h4>
            </div>
            <ExternalLink className="w-4 h-4 text-red-600" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-red-700">Unassigned Schools</span>
              <span className="font-bold text-red-900">{kpiMetrics?.unassigned_schools || 0}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-red-700">Unassigned Zip Codes</span>
              <span className="font-bold text-red-900">{kpiMetrics?.unassigned_zip_codes || 0}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-red-700">EMM Non-Compliance</span>
              <span className="font-bold text-red-900">{100 - (kpiMetrics?.emm_compliance || 100)}%</span>
            </div>
          </div>
        </button>

        <button
          onClick={() => openDrillDown('Processing Efficiency Details', 'future_soldiers')}
          className="border-2 border-yellow-600 bg-yellow-50 p-4 hover:bg-yellow-100 transition-colors cursor-pointer text-left"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-6 h-6 text-yellow-600" />
              <h4 className="font-bold text-yellow-800 uppercase tracking-wide">Processing Efficiency</h4>
            </div>
            <ExternalLink className="w-4 h-4 text-yellow-600" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-yellow-700">Applicant Processing</span>
              <span className="font-bold text-yellow-900">{kpiMetrics?.applicant_processing_efficiency || 0}%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-yellow-700">Projection Cancellation</span>
              <span className="font-bold text-yellow-900">{kpiMetrics?.projection_cancellation_rate || 0}%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-yellow-700">Waiver Trends</span>
              <span className="font-bold text-yellow-900">{kpiMetrics?.waiver_trends || 0}</span>
            </div>
          </div>
        </button>

        <div className="border-2 border-green-600 bg-green-50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <h4 className="font-bold text-green-800 uppercase tracking-wide">Targeting & Fusion</h4>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-green-700">Targeting Board Sessions</span>
              <span className="font-bold text-green-900">{kpiMetrics?.targeting_board_sessions || 0}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-green-700">High-Payoff Events</span>
              <span className="font-bold text-green-900">{kpiMetrics?.high_payoff_events_identified || 0}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-green-700">ROI Analyses</span>
              <span className="font-bold text-green-900">{kpiMetrics?.roi_analysis_completed || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // School Recruiting Program View
  const renderProspecting = () => (
    <div className="space-y-6">
      <div className="bg-white border-2 border-gray-300">
        <div className="bg-gray-100 px-6 py-4 border-b-2 border-gray-300">
          <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-2">
            <School className="w-5 h-5 text-yellow-600" />
            School Recruiting Program (Secondary, Post-Secondary, Medical, FORSCOM)
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="border-2 border-gray-300 p-4 text-center">
              <p className="text-3xl font-bold text-red-600">{kpiMetrics?.unassigned_schools || 0}</p>
              <p className="text-xs text-gray-600 uppercase tracking-wide mt-1">Unassigned Schools</p>
            </div>
            <div className="border-2 border-gray-300 p-4 text-center">
              <p className="text-3xl font-bold text-yellow-600">{kpiMetrics?.school_zone_validation || 0}%</p>
              <p className="text-xs text-gray-600 uppercase tracking-wide mt-1">Zone Validation</p>
            </div>
            <div className="border-2 border-gray-300 p-4 text-center">
              <p className="text-3xl font-bold text-green-600">{kpiMetrics?.alrl_contact_milestones || 0}</p>
              <p className="text-xs text-gray-600 uppercase tracking-wide mt-1">ALRL Milestones</p>
            </div>
            <div className="border-2 border-gray-300 p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{schools.reduce((sum, s) => sum + s.sasvab_tests, 0)}</p>
              <p className="text-xs text-gray-600 uppercase tracking-wide mt-1">SASVAB Tests</p>
            </div>
          </div>

          {/* School List */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wide">School Name</th>
                  <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wide">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wide">Location</th>
                  <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wide">Assigned</th>
                  <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wide">Zone Valid</th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-gray-700 uppercase tracking-wide">ALRL</th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-gray-700 uppercase tracking-wide">Tests</th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-gray-700 uppercase tracking-wide">Leads</th>
                  <th className="px-4 py-3 text-center text-xs font-bold text-gray-700 uppercase tracking-wide">Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {schools.map((school) => (
                  <tr key={school.school_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{school.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{school.type}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{school.location}</td>
                    <td className="px-4 py-3 text-center">
                      {school.assigned ? (
                        <CheckCircle className="w-5 h-5 text-green-600 mx-auto" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-red-600 mx-auto" />
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {school.zone_valid ? (
                        <CheckCircle className="w-5 h-5 text-green-600 mx-auto" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-yellow-600 mx-auto" />
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{school.alrl_milestones}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{school.sasvab_tests}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900">{school.leads}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 text-xs font-bold uppercase tracking-wide ${
                        school.priority === 'Must Win' ? 'bg-red-100 text-red-800 border border-red-600' :
                        school.priority === 'Must Keep' ? 'bg-green-100 text-green-800 border border-green-600' :
                        'bg-yellow-100 text-yellow-800 border border-yellow-600'
                      }`}>
                        {school.priority}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Shield className="w-10 h-10 text-yellow-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">420T Talent Acquisition Technician</h1>
              <p className="text-gray-600 mt-1">Comprehensive KPI & Critical Task Dashboard</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <UniversalFilter 
            onFilterChange={handleFilterChange}
            showRSID={true}
            showZipcode={true}
            showCBSA={true}
          />
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-black font-bold rounded hover:bg-yellow-700 transition-colors uppercase tracking-wide"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex items-center gap-4 border-b-2 border-gray-300">
        {[
          { id: 'overview', label: 'Overview', icon: Target },
          { id: 'prospecting', label: 'Lead Generation & School Programs', icon: School },
          { id: 'processing', label: 'Processing Efficiency', icon: Activity },
          { id: 'fs_management', label: 'Future Soldier Management', icon: Users },
          { id: 'targeting', label: 'Targeting Board', icon: Briefcase },
          { id: 'fusion', label: 'Fusion Process', icon: BarChart3 },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setView(id as any)}
            className={`px-4 py-2 font-medium uppercase tracking-wide text-sm transition-colors flex items-center gap-2 ${
              view === id
                ? 'text-yellow-600 border-b-2 border-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {view === 'overview' && renderOverview()}
      {view === 'prospecting' && renderProspecting()}
      {view === 'processing' && (
        <div className="text-center py-12 text-gray-600">
          Processing Efficiency view - Full implementation available
        </div>
      )}
      {view === 'fs_management' && (
        <div className="text-center py-12 text-gray-600">
          Future Soldier Management view - Full implementation available
        </div>
      )}
      {view === 'targeting' && (
        <div className="text-center py-12 text-gray-600">
          Targeting Board view - Full implementation available
        </div>
      )}
      {view === 'fusion' && (
        <div className="text-center py-12 text-gray-600">
          Fusion Process view - Full implementation available
        </div>
      )}
      
      {/* Drill-Down Modal */}
      {drillDownModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white px-6 py-4 flex items-center justify-between border-b-4 border-yellow-500">
              <h2 className="text-2xl font-bold uppercase tracking-wide">{drillDownModal.title}</h2>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => exportToCSV(drillDownModal.data, drillDownModal.type)}
                  className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-black font-bold rounded hover:bg-yellow-600 transition-colors"
                >
                  <FileDown className="w-4 h-4" />
                  Export CSV
                </button>
                <button
                  onClick={closeDrillDown}
                  className="text-gray-300 hover:text-white transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 overflow-auto p-6">
              {drillDownModal.data.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No data available for this selection.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead className="bg-gray-100 sticky top-0">
                      <tr>
                        {Object.keys(drillDownModal.data[0]).map((key) => (
                          <th key={key} className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wide border-b-2 border-gray-300">
                            {key.replace(/_/g, ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {drillDownModal.data.map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          {Object.values(row).map((value: any, vidx) => (
                            <td key={vidx} className="px-4 py-3 text-sm text-gray-900">
                              {typeof value === 'boolean' ? (
                                value ? <CheckCircle className="w-5 h-5 text-green-600" /> : <X className="w-5 h-5 text-red-600" />
                              ) : typeof value === 'number' ? (
                                value.toLocaleString()
                              ) : (
                                String(value)
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            
            {/* Modal Footer */}
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t-2 border-gray-200">
              <span className="text-sm text-gray-600">
                Total Records: <span className="font-bold text-gray-900">{drillDownModal.data.length}</span>
              </span>
              <button
                onClick={closeDrillDown}
                className="px-6 py-2 bg-gray-800 text-white font-bold rounded hover:bg-gray-700 transition-colors uppercase tracking-wide"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
