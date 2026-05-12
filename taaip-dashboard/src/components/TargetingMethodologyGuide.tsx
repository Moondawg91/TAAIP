import React from 'react';
import { Target, CheckCircle, Users, Map, Shield, TrendingUp } from 'lucide-react';

interface USARECPhase {
  phase: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  activities: string[];
}

const USAREC_PHASES: USARECPhase[] = [
  {
    phase: 'Market Intelligence & Baseline',
    description: 'Establish current market posture, production baselines, and demographic opportunity.',
    icon: <Map className="w-8 h-8" />,
    color: 'from-gray-700 to-gray-800',
    activities: [
      'Compile CBSA production & penetration rates',
      'Map QMA distribution and ALRL status',
      'Identify High Payoff vs Must Win districts',
      'Analyze PRIZM / segment composition',
      'Assess competitor (other services) presence',
      'Baseline propensity & barrier indicators'
    ]
  },
  {
    phase: 'Prioritize Segments & Institutions',
    description: 'Rank target segments/schools based on payoff, access feasibility, and strategic importance.',
    icon: <Shield className="w-8 h-8" />,
    color: 'from-yellow-600 to-yellow-700',
    activities: [
      'Score segments by P2P and contract yield',
      'Classify schools (Tier 1–3) & access constraints',
      'Identify influencer / COI leverage points',
      'Select pacing battalions / districts',
      'Refine addressable cohort sizes',
      'De-conflict overlapping asset demands'
    ]
  },
  {
    phase: 'Allocate Assets & Messaging',
    description: 'Align tiered assets, recruiter effort, and tailored messaging to priority targets.',
    icon: <Users className="w-8 h-8" />,
    color: 'from-blue-600 to-blue-700',
    activities: [
      'Assign TAIR / tiered event support',
      'Schedule calendar touchpoints (30/60/90)',
      'Tailor segment-specific value propositions',
      'Select digital vs physical engagement mix',
      'Define success metrics & KPIs',
      'Publish targeting tasking to units'
    ]
  },
  {
    phase: 'Engage & Capture Leads',
    description: 'Execute engagements, collect leads, and push prospects into the recruiting funnel.',
    icon: <Target className="w-8 h-8" />,
    color: 'from-green-600 to-green-700',
    activities: [
      'Run events with assigned tiered assets',
      'Deploy recruiters to High Payoff areas',
      'Activate COI / influencer partnerships',
      'Launch targeted digital outreach',
      'Capture and QC leads rapidly',
      'Route qualified leads to funnel stages'
    ]
  },
  {
    phase: 'Assess & Retarget',
    description: 'Evaluate effectiveness, refine prioritization, and iterate the cycle.',
    icon: <TrendingUp className="w-8 h-8" />,
    color: 'from-purple-600 to-purple-700',
    activities: [
      'AAR within 72 hrs of key events',
      'Analyze CPL / CPC and conversion velocity',
      'Update market penetration & P2P shifts',
      'Document lessons learned & adjustments',
      'Refresh segment & school prioritization',
      'Publish retarget guidance to units'
    ]
  }
];

const renderPhaseCards = (phases: USARECPhase[]) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {phases.map((phase, idx) => (
      <div key={idx} className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
        <div className={`bg-gradient-to-r ${phase.color} text-white p-6`}>
          <div className="flex items-center justify-between mb-3">
            {phase.icon}
            <span className="text-2xl font-bold">#{idx + 1}</span>
          </div>
          <h3 className="text-2xl font-bold mb-2">{phase.phase}</h3>
          <p className="text-sm opacity-90">{phase.description}</p>
        </div>
        <div className="p-6">
          <h4 className="font-bold text-gray-800 mb-3">Key Activities:</h4>
          <ul className="space-y-2">
            {phase.activities.map((activity, actIdx) => (
              <li key={actIdx} className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-700">{activity}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    ))}
  </div>
);

export const TargetingMethodologyGuide: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center">
          <Target className="w-8 h-8 mr-3 text-yellow-600" />
          USAREC Targeting Methodology
        </h1>
        <p className="text-gray-600 mt-2">
          Unified USAREC-specific cycle replacing legacy D3AE/F3A references for talent acquisition targeting and resource alignment.
        </p>
      </div>
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Cycle Overview</h2>
        <p className="text-gray-700 mb-4">
          This framework drives iterative targeting: establish intelligence, prioritize, allocate, engage, then assess and retarget.
          It aligns Fusion Team operations, TWG decisions, and recruiter execution under a single repeatable process.
        </p>
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 text-sm text-gray-700">
          <strong>Usage:</strong> Apply at battalion/brigade level for quarterly planning; refresh prioritization monthly or after major shifts.
        </div>
      </div>
      {renderPhaseCards(USAREC_PHASES)}
      {/* D3A Mapping per user-provided definitions */}
      <div className="mt-6 bg-white rounded-lg shadow-md p-6">
        <h3 className="text-2xl font-bold text-gray-800 mb-4">D3A (Quarter-Ahead) Mapping</h3>
        <p className="text-gray-700 mb-4">Aligned to Q+3 planning with explicit outputs for each phase.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="border-2 border-purple-200 rounded-lg p-4">
            <h4 className="font-bold text-purple-900 mb-2">Decide</h4>
            <p className="text-sm text-gray-700">
              Identify future strategic targets. <em>(Q+3 target segments and specific target audience)</em>
            </p>
          </div>
          <div className="border-2 border-blue-200 rounded-lg p-4">
            <h4 className="font-bold text-blue-900 mb-2">Detect</h4>
            <p className="text-sm text-gray-700">
              Identify the operational landscape and opportunities. <em>(Q+3 events, schools, COIs (Centers of Influence), and other key elements)</em>
            </p>
          </div>
          <div className="border-2 border-green-200 rounded-lg p-4">
            <h4 className="font-bold text-green-900 mb-2">Deliver</h4>
            <p className="text-sm text-gray-700">
              Outline required resources for execution. <em>(Q+3 resource needs including personnel, assets, PPI/RPI, and funding)</em>
            </p>
          </div>
          <div className="border-2 border-orange-200 rounded-lg p-4">
            <h4 className="font-bold text-orange-900 mb-2">Assess</h4>
            <p className="text-sm text-gray-700">
              Provide the initial plan for measuring effectiveness. <em>(Initial assessment plans for Q+3 operations)</em>
            </p>
          </div>
        </div>
      </div>
      <div className="mt-6 bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Users className="w-6 h-6 mr-2 text-yellow-600" /> Integration with TAAIP
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
          <div className="border-2 border-gray-200 rounded-lg p-4">
            <h4 className="font-bold mb-2">Intelligence & Baseline</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Analytics Dashboard</li>
              <li>Market Potential</li>
              <li>Segmentation Dashboard</li>
            </ul>
          </div>
          <div className="border-2 border-gray-200 rounded-lg p-4">
            <h4 className="font-bold mb-2">Prioritize & Allocate</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Fusion Team Dashboard</li>
              <li>Targeting Working Group</li>
              <li>Budget Tracker</li>
            </ul>
          </div>
          <div className="border-2 border-gray-200 rounded-lg p-4">
            <h4 className="font-bold mb-2">Engage & Assess</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Event Performance</li>
              <li>Recruiting Funnel</li>
              <li>Lead Status Report</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TargetingMethodologyGuide;
