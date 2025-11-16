import React, { useState, useCallback, useMemo } from 'react';
import { Target, TrendingUp, Cpu, RefreshCw, AlertTriangle, CheckCircle, Map, Users, BarChart3, ChevronRight, XCircle } from 'lucide-react';

// IMPORTANT: This is a single-file React component using functional components and hooks.
// It assumes Tailwind CSS is available in the environment.

// --- MOCK API DATA & CONSTANTS (Based on Uploaded Documents) ---

// Mock data for the Market Prioritization Matrix
const MARKET_PRIORITIES = {
  MUST_WIN: {
    title: "Must Win",
    description: "Underrepresented, high potential markets. Resource priority: Create success.",
    color: "bg-red-500",
    icon: <AlertTriangle className="w-6 h-6" />,
    style: "border-red-600 shadow-red-500/50",
  },
  MUST_KEEP: {
    title: "Must Keep",
    description: "Doing well, sustain or exploit. Responsibility to maintain markets.",
    color: "bg-yellow-500",
    icon: <CheckCircle className="w-6 h-6" />,
    style: "border-yellow-600 shadow-yellow-500/50",
  },
  MARKET_OF_OPPORTUNITY: {
    title: "Market of Opportunity",
    description: "Small potential being achieved. Maintain awareness.",
    color: "bg-blue-500",
    icon: <TrendingUp className="w-6 h-6" />,
    style: "border-blue-600 shadow-blue-500/50",
  },
  SUPPLEMENTAL: {
    title: "Supplemental",
    description: "Not a significant market. Not a resource priority.",
    color: "bg-gray-500",
    icon: <XCircle className="w-6 h-6" />,
    style: "border-gray-600 shadow-gray-500/50",
  },
};

// Mock data for a specific PRIZM Segment (Segment 50: Empty Nests)
const MOCK_SEGMENT_DATA = {
  segmentId: 50,
  segmentName: "Empty Nests",
  propensity: "5%",
  penetrationIndex: "Far below average (Needs tailored engagement)",
  demographics: [
    "Mature (65+)",
    "Mostly Retired",
    "Upper Midscale",
    "No Kids",
    "Slight Reserve Preference",
  ],
  motivators: ["Travel", "Pay for Education", "Experience Adventure"],
  barriers: [
    "Physical Injury/Death",
    "Possibility of PTSD/Psych Issues",
    "Leave Family/Friends",
    "Other Career Interests",
  ],
  messageCluster: "Army As A Solution (Will consider if life doesn't go according to plan)",
};

// Mock Funnel KPIs (Based on 'terpret' and 'Walk in' PDFs)
const MOCK_FUNNEL_KPIS = [
  { stage: "Contact to Lead", metric: "3.6M Leads from 25M Contacts" },
  { stage: "Lead to Contract", metric: "37.3 Leads per Contract (RA)" },
  { stage: "Appt Scheduled Rate", metric: "50% of appts made in first week" },
  { stage: "Appt to Interview", metric: "Avg 2.6 Days" },
];

// Mock Marketing Benchmarks (Based on 'terpret' PDF)
const MOCK_BENCHMARKS = [
    { KPI: "Cost Per Engagement (CPE)", tactic: "Exhibit (EMM OBJ: Engagement)", less: "<$169", target: "$169-$258", more: ">$258" },
    { KPI: "Cost Per Lead (CPL)", tactic: "Direct Job Posting (EMM OBJ: Activation)", less: "<$303", target: "$303-$426", more: ">$426" },
];


// --- UTILITY COMPONENTS ---

// Helper component for styled text boxes
type InfoBoxProps = {
  title: string;
  content: string;
  icon?: React.ReactNode;
  className?: string;
};
const InfoBox: React.FC<InfoBoxProps> = ({ title, content, icon, className = "" }) => (
  <div className={`p-4 bg-white border border-gray-200 rounded-xl shadow-lg ${className}`}>
    <div className="flex items-center text-blue-600 mb-2">
      {icon}
      <h3 className="ml-2 text-md font-semibold text-gray-800">{title}</h3>
    </div>
    <p className="text-sm text-gray-600">{content}</p>
  </div>
);

// --- DASHBOARD VIEW COMPONENTS ---

const MarketSegmentDashboard: React.FC = () => {
  return (
    <div className="space-y-8 p-4 md:p-8">
      <h2 className="text-3xl font-extrabold text-gray-900 border-b pb-2">
        <Map className="inline-block mr-2 w-7 h-7 text-green-600" />
        Market & Segment Analysis
      </h2>
      <p className="text-gray-600 italic">
        Integrating Market Value/Strength and Claritas PRIZM segmentation for resource prioritization.
      </p>

      {/* Market Prioritization Matrix */}
      <div className="bg-white p-6 rounded-xl shadow-2xl">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2 text-indigo-600" />
          Target Market Priorities
        </h3>
        <p className="text-sm text-gray-500 mb-6">
          Prioritization based on **Market Value** (potential) vs. **Market Strength** (penetration/performance).
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.values(MARKET_PRIORITIES).map((priority, index) => (
            <div
              key={index}
              className={`p-5 rounded-xl border-4 ${priority.style} transition duration-300 hover:scale-[1.02] cursor-default`}
            >
              <div className="flex items-center mb-2">
                <div className={`p-2 rounded-full ${priority.color} text-white`}>
                  {priority.icon}
                </div>
                <h4 className="ml-3 text-xl font-bold text-gray-900">{priority.title}</h4>
              </div>
              <p className="text-sm text-gray-600">{priority.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Claritas PRIZM Segment Deep Dive */}
      <div className="bg-white p-6 rounded-xl shadow-2xl">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
          <Users className="w-5 h-5 mr-2 text-indigo-600" />
          Segment Deep Dive: PRIZM #{MOCK_SEGMENT_DATA.segmentId} - {MOCK_SEGMENT_DATA.segmentName}
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Column 1: Core Metrics */}
          <div className="space-y-4">
            <InfoBox
              title="Propensity (DoD Youth Poll)"
              content={`Only ${MOCK_SEGMENT_DATA.propensity} of this segment indicate military service likelihood.`}
              icon={<TrendingUp />}
              className="bg-blue-50 border-blue-200"
            />
            <InfoBox
              title="Penetration Index"
              content={MOCK_SEGMENT_DATA.penetrationIndex}
              icon={<BarChart3 />}
              className="bg-yellow-50 border-yellow-200"
            />
            <InfoBox
              title="Message Cluster"
              content={MOCK_SEGMENT_DATA.messageCluster}
              icon={<ChevronRight />}
              className="bg-green-50 border-green-200"
            />
          </div>

          {/* Column 2: Demographics & Motivators */}
          <div className="space-y-4">
            <h4 className="font-semibold text-lg text-gray-700">Key Characteristics</h4>
            <ul className="list-disc list-inside text-sm text-gray-600 bg-gray-50 p-3 rounded-lg space-y-1">
              {MOCK_SEGMENT_DATA.demographics.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
            <h4 className="font-semibold text-lg text-gray-700">Motivators for Army Consideration</h4>
            <ul className="list-disc list-inside text-sm text-gray-600 bg-green-50 p-3 rounded-lg space-y-1">
              {MOCK_SEGMENT_DATA.motivators.map((m, i) => <li key={i} className="text-green-800">{m}</li>)}
            </ul>
          </div>

          {/* Column 3: Barriers & Actionable Insights */}
          <div className="space-y-4">
            <h4 className="font-semibold text-lg text-gray-700">Primary Barriers to Service</h4>
            <ul className="list-disc list-inside text-sm text-gray-600 bg-red-50 p-3 rounded-lg space-y-1">
              {MOCK_SEGMENT_DATA.barriers.map((b, i) => <li key={i} className="text-red-800">{b}</li>)}
            </ul>
          </div>
        </div>
      </div>

      {/* Funnel KPIs & Benchmarks */}
      <div className="bg-white p-6 rounded-xl shadow-2xl">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2 text-indigo-600" />
          Recruiting Funnel Metrics & EMM Benchmarks
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className='border-r pr-6'>
                <h4 className="font-semibold text-lg text-gray-700 mb-3">Key Funnel Conversion Ratios</h4>
                <div className='space-y-3'>
                    {MOCK_FUNNEL_KPIS.map((kpi, i) => (
                        <div key={i} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm font-medium text-gray-900">{kpi.stage}</span>
                            <span className="text-sm text-blue-700 font-bold">{kpi.metric}</span>
                        </div>
                    ))}
                </div>
            </div>
            <div>
                <h4 className="font-semibold text-lg text-gray-700 mb-3">Target Marketing Benchmarks (CPE/CPL)</h4>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">KPI (Tactic)</th>
                                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Less than 1SD</th>
                                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">1SD - 2SD (Target)</th>
                                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">More than 2SD</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200 text-sm text-gray-700">
                            {MOCK_BENCHMARKS.map((b, i) => (
                                <tr key={i}>
                                    <td className="px-3 py-3 font-medium">{b.KPI} <span className="text-gray-400">({b.tactic})</span></td>
                                    <td className="px-3 py-3 text-green-600 font-semibold">{b.less}</td>
                                    <td className="px-3 py-3 bg-yellow-50 font-semibold">{b.target}</td>
                                    <td className="px-3 py-3 text-red-600 font-semibold">{b.more}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
      </div>


    </div>
  );
};

// --- LEAD SCORING VIEW COMPONENT ---
type FormInputProps = {
  label: string;
  name: string;
  type?: string;
  value: any;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  [key: string]: any;
};
const FormInput: React.FC<FormInputProps> = ({ label, name, type = 'text', value, onChange, ...props }) => (
  <div>
    <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
      {label}
    </label>
    <input
      type={type}
      name={name}
      id={name}
      value={value}
      onChange={onChange}
      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150"
      {...props}
    />
  </div>
);

type Option = { value: any; label: string };
type FormSelectProps = {
  label: string;
  name: string;
  value: any;
  onChange?: React.ChangeEventHandler<HTMLSelectElement>;
  options: Option[];
};
const FormSelect: React.FC<FormSelectProps> = ({ label, name, value, onChange, options }) => (
  <div>
    <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
      {label}
    </label>
    <select
      name={name}
      id={name}
      value={value}
      onChange={onChange}
      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm appearance-none bg-white transition duration-150"
    >
      {options.map((opt) => (
        <option key={String(opt.value)} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  </div>
);


type LeadFormData = {
  lead_id: string;
  age: number;
  education_level: string;
  propensity_score: number;
  prizm_segment: number;
  web_activity: number;
};
const initialFormData: LeadFormData = {
  lead_id: 'L-' + (Math.floor(Math.random() * 9000) + 1000),
  age: 20,
  education_level: 'High School',
  propensity_score: 8,
  prizm_segment: 3,
  web_activity: 5,
};

const LeadScoringTool: React.FC = () => {
  const [formData, setFormData] = useState<LeadFormData>(initialFormData);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any | null>(null);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target as HTMLInputElement;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'age' || name === 'propensity_score' || name === 'prizm_segment' || name === 'web_activity'
        ? parseInt(value, 10)
        : value,
    }));
  }, []);

  const scoreLead = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    // MOCK LEAD SCORING LOGIC (Simulating AI/ML Pipeline)
    // Score is calculated based on Propensity (weight 4), Age (weight 2), and Web Activity (weight 1)
    const baseScore = (formData.propensity_score * 4) + (formData.age * 0.5) + (formData.web_activity * 1);
    let totalScore = Math.min(100, Math.round(baseScore + (Math.random() * 20 - 10))); // Add randomness
    totalScore = Math.max(20, totalScore); // Ensure minimum score

    const decisionMatrix = {
      90: "Tier 1: High Propensity - Immediate Recruiter Action (Call/Walk-In)",
      70: "Tier 2: Strong Lead - Targeted Digital Engagement (Email/Text)",
      50: "Tier 3: Moderate Potential - Nurture Campaign (Social/Mail)",
      0: "Tier 4: Low Potential - Supplemental Awareness efforts",
    };

    let recommendedAction = decisionMatrix[0];
    if (totalScore >= 90) recommendedAction = decisionMatrix[90];
    else if (totalScore >= 70) recommendedAction = decisionMatrix[70];
    else if (totalScore >= 50) recommendedAction = decisionMatrix[50];


    setTimeout(() => {
      setLoading(false);
      setResult({
        lead_id: formData.lead_id,
        score: totalScore,
        tier: recommendedAction.split(':')[0],
        action: recommendedAction.split(': ')[1],
        prizm: `${formData.prizm_segment} - ${formData.education_level}`,
        notes: "Recommendation generated by the Lookalike Modeling and Lead Scoring Engine based on user profile and activity.",
      });
    }, 1500);
  }, [formData]);

  const prizmOptions = useMemo<Option[]>(() => ([
    { value: 3, label: '3 - Movers & Shakers' },
    { value: 4, label: '4 - Young Digerati' },
    { value: 13, label: '13 - Upward Bound' },
    { value: 50, label: '50 - Metro Grads' },
  ]), []);

  return (
    <div className="p-4 md:p-8 space-y-8">
      <h2 className="text-3xl font-extrabold text-gray-900 border-b pb-2">
        <Cpu className="inline-block mr-2 w-7 h-7 text-green-600" />
        AI-Powered Lead Scoring Tool
      </h2>
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Input Form */}
        <form onSubmit={scoreLead} className="bg-white p-6 rounded-xl shadow-2xl lg:w-1/2 space-y-6">
          <h3 className="text-xl font-bold text-gray-800 flex items-center mb-4">
            <Target className="w-5 h-5 mr-2 text-indigo-600" />
            Lead Profile Input
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Lead ID" name="lead_id" value={formData.lead_id} onChange={handleChange} disabled />
            <FormInput label="Age" name="age" type="number" min="17" max="35" value={formData.age} onChange={handleChange} required />
            <FormSelect
              label="Education Level"
              name="education_level"
              value={formData.education_level}
              onChange={handleChange}
              options={[{ value: 'High School', label: 'High School' }, { value: 'Some College', label: 'Some College' }, { value: 'Degree', label: 'Degree' }]}
            />
            <FormInput label="Propensity Score (1-10)" name="propensity_score" type="number" min="1" max="10" value={formData.propensity_score} onChange={handleChange} required />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormSelect
              label="Claritas PRIZM Segment"
              name="prizm_segment"
              value={formData.prizm_segment}
              onChange={handleChange}
              options={prizmOptions}
            />
            <FormInput label="Web Activity Score (1-10)" name="web_activity" type="number" min="1" max="10" value={formData.web_activity} onChange={handleChange} required />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-md text-sm font-semibold text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition duration-150 ease-in-out disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-5 h-5 mr-2 animate-spin" /> : <TrendingUp className="w-5 h-5 mr-2" />}
            {loading ? 'Analyzing...' : 'Generate TAAIP Lead Score'}
          </button>
        </form>

        {/* Output Result */}
        <div className="lg:w-1/2">
          {result && (
            <div className={`p-6 bg-white rounded-xl shadow-2xl border-l-4 ${result.tier.includes('Tier 1') ? 'border-red-500' : result.tier.includes('Tier 2') ? 'border-yellow-500' : 'border-blue-500'}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">TAAIP Lead Score Result</h3>
                <span className={`text-3xl font-extrabold p-2 rounded-full ${result.tier.includes('Tier 1') ? 'bg-red-100 text-red-700' : result.tier.includes('Tier 2') ? 'bg-yellow-100 text-yellow-700' : 'bg-blue-100 text-blue-700'}`}>
                  {result.score}
                </span>
              </div>
              <div className="space-y-3">
                <p className="text-lg font-semibold text-gray-800">{result.tier}</p>
                <p className="text-sm text-gray-700">
                  <strong className='text-gray-900'>Recommended Action:</strong> {result.action}
                </p>
                <p className="text-sm text-gray-700">
                  <strong className='text-gray-900'>Segment Profile:</strong> {result.prizm}
                </p>
                <div className="text-sm text-gray-400 pt-4 border-t">
                  <span className="font-mono">Lead ID: {result.lead_id}</span>
                </div>
              </div>
            </div>
          )}
          {!result && !loading && (
            <div className="p-6 bg-gray-50 border border-dashed border-gray-300 rounded-xl text-center text-gray-500 h-full flex items-center justify-center">
                <p className='flex flex-col items-center'>
                    <Target className='w-8 h-8 mb-2' />
                    Enter lead data and click 'Generate TAAIP Lead Score' to get the recommended action.
                </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


// --- MAIN APP COMPONENT ---

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'scoring'>('dashboard'); // 'dashboard' or 'scoring'

  const NavItem: React.FC<{ tabName: 'dashboard' | 'scoring'; icon?: React.ReactNode; label: string }> = ({ tabName, icon, label }) => (
    <button
      onClick={() => setActiveTab(tabName)}
      className={`flex items-center justify-center px-4 py-3 rounded-t-lg transition-all duration-300 ease-in-out ${
        activeTab === tabName
          ? 'bg-white border-b-4 border-green-600 text-green-700 font-bold shadow-inner'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800'
      }`}
    >
      {icon}
      <span className="ml-2 hidden sm:inline">{label}</span>
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <header className="bg-white shadow-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex justify-between items-center">
          <h1 className="text-2xl font-extrabold text-gray-900 flex items-center">
            <img src="https://placehold.co/32x32/10b981/ffffff?text=TA" alt="TAAIP Logo" className="mr-3 rounded-full"/>
            TAAIP: Targeting & Intelligence Platform
          </h1>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-gray-200 shadow-inner">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-2 sm:space-x-4">
          <NavItem
            tabName="dashboard"
            icon={<Map className="w-5 h-5" />}
            label="Market & Segment Dashboard"
          />
          <NavItem
            tabName="scoring"
            icon={<Cpu className="w-5 h-5" />}
            label="AI Lead Scoring Tool"
          />
        </div>
      </nav>

      <main className="max-w-7xl mx-auto">
        {activeTab === 'dashboard' ? <MarketSegmentDashboard /> : <LeadScoringTool />}
      </main>

      <footer className="w-full py-4 mt-10 bg-gray-800 text-center text-gray-400 text-xs">
        TAAIP: Talent Acquisition Analytics and Intelligence Platform | USAREC/USARD
      </footer>
    </div>
  );
};

export default App;
