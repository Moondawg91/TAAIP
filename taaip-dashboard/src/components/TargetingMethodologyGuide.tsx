import React, { useState } from 'react';
import {
  Target, Eye, Crosshair, CheckCircle, AlertTriangle,
  TrendingUp, Users, Map, Zap, Shield, Award
} from 'lucide-react';

interface TargetingPhase {
  phase: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  activities: string[];
}

export const TargetingMethodologyGuide: React.FC = () => {
  const [activeMethodology, setActiveMethodology] = useState<'d3ae' | 'f3a' | 'mipoe'>('d3ae');

  const D3AE_PHASES: TargetingPhase[] = [
    {
      phase: 'Detect',
      description: 'Identify and locate high-value prospects and market segments',
      icon: <Eye className="w-8 h-8" />,
      color: 'from-blue-600 to-blue-700',
      activities: [
        'Use PRIZM segmentation to identify high-value and high-payoff segments',
        'Analyze CBSA market penetration data to find underserved areas',
        'Review P2P ratios to identify representation gaps',
        'Monitor propensity scores and Youth Poll data',
        'Identify influencer networks and community leaders',
        'Track competitor (other services) activity in target markets'
      ]
    },
    {
      phase: 'Discriminate',
      description: 'Distinguish between high-priority and low-priority targets',
      icon: <Crosshair className="w-8 h-8" />,
      color: 'from-yellow-600 to-yellow-700',
      activities: [
        'Prioritize segments with P2P > 1.0 (High Payoff)',
        'Focus on Must Win and Must Keep CBSAs',
        'Segment prospects by propensity score and barriers',
        'Identify geographic centers of gravity (pacing battalions)',
        'Assess lead quality and conversion probability',
        'Filter for QMA and ALRL criteria'
      ]
    },
    {
      phase: 'Decide',
      description: 'Make targeting decisions and allocate resources',
      icon: <CheckCircle className="w-8 h-8" />,
      color: 'from-green-600 to-green-700',
      activities: [
        'Assign tiered assets (T1, T2, T3) to events',
        'Allocate marketing budget across high-value segments',
        'Select appropriate messaging for each segment',
        'Choose geotargeting vs geofencing strategies',
        'Determine event types and locations',
        'Set production goals and success metrics'
      ]
    },
    {
      phase: 'Act',
      description: 'Execute the targeting plan and engage prospects',
      icon: <Zap className="w-8 h-8" />,
      color: 'from-red-600 to-red-700',
      activities: [
        'Launch targeted digital advertising campaigns',
        'Execute events with appropriate TAIR support',
        'Deploy recruiters to high-payoff locations',
        'Activate influencer and community partnerships',
        'Deliver segment-specific messaging',
        'Track real-time engagement and lead generation'
      ]
    },
    {
      phase: 'Exploit/Assess',
      description: 'Capitalize on successes and evaluate outcomes',
      icon: <TrendingUp className="w-8 h-8" />,
      color: 'from-purple-600 to-purple-700',
      activities: [
        'Conduct After Action Reviews (AARs) within 72 hours',
        'Analyze cost per lead (CPL) and cost per contract (CPC)',
        'Measure market penetration changes',
        'Track P2P ratio improvements',
        'Document lessons learned and best practices',
        'Update segment profiles with new intelligence'
      ]
    }
  ];

  const F3A_PHASES: TargetingPhase[] = [
    {
      phase: 'Find',
      description: 'Locate potential recruits and identify target markets',
      icon: <Eye className="w-8 h-8" />,
      color: 'from-blue-600 to-blue-700',
      activities: [
        'Query JAMRS and market intelligence databases',
        'Identify high school and college target lists',
        'Use social media intelligence and digital footprints',
        'Leverage community events and local networks',
        'Analyze competitor activity and market gaps',
        'Review historical production data for patterns'
      ]
    },
    {
      phase: 'Fix',
      description: 'Establish contact and confirm prospect details',
      icon: <Target className="w-8 h-8" />,
      color: 'from-yellow-600 to-yellow-700',
      activities: [
        'Verify contact information and QMA status',
        'Conduct initial propensity assessment',
        'Identify motivators and barriers through conversation',
        'Segment leads by PRIZM classification',
        'Establish preferred communication channels',
        'Schedule follow-up appointments'
      ]
    },
    {
      phase: 'Finish',
      description: 'Close the deal and convert prospect to contract',
      icon: <Award className="w-8 h-8" />,
      color: 'from-green-600 to-green-700',
      activities: [
        'Navigate prospect through recruiting funnel',
        'Address barriers with targeted information',
        'Leverage motivators in messaging',
        'Coordinate MEPS processing',
        'Secure enlistment commitment',
        'Complete contract paperwork'
      ]
    },
    {
      phase: 'Assess',
      description: 'Evaluate effectiveness and refine approach',
      icon: <TrendingUp className="w-8 h-8" />,
      color: 'from-purple-600 to-purple-700',
      activities: [
        'Track conversion rates through funnel stages',
        'Analyze time-to-contract metrics',
        'Measure recruiter productivity',
        'Review market penetration impact',
        'Conduct quarterly performance reviews',
        'Update targeting strategies based on results'
      ]
    }
  ];

  const MIPOE_PHASES = [
    {
      phase: 'Define the Operations Environment',
      description: 'Understand the recruiting landscape and competitive space',
      icon: <Map className="w-8 h-8" />,
      color: 'from-gray-600 to-gray-700',
      activities: [
        'Map CBSA boundaries and demographics',
        'Identify school districts and population centers',
        'Locate competitor recruiting stations',
        'Document military installations and influence zones',
        'Assess transportation and accessibility',
        'Review socioeconomic factors by ZIP code'
      ]
    },
    {
      phase: 'Describe Environmental Effects',
      description: 'Analyze how environment impacts recruiting operations',
      icon: <AlertTriangle className="w-8 h-8" />,
      color: 'from-blue-600 to-blue-700',
      activities: [
        'Assess propensity by geographic area',
        'Identify cultural and community attitudes',
        'Evaluate economic conditions and job market',
        'Consider seasonal effects on recruiting',
        'Analyze education system structure',
        'Review local media landscape and influence'
      ]
    },
    {
      phase: 'Evaluate the Competition',
      description: 'Understand other services and employment alternatives',
      icon: <Shield className="w-8 h-8" />,
      color: 'from-yellow-600 to-yellow-700',
      activities: [
        'Track other services\' market share and production',
        'Identify competitor recruiting strategies',
        'Monitor private sector employment opportunities',
        'Assess college enrollment trends',
        'Review civilian job market competition',
        'Document competitor strengths and weaknesses'
      ]
    },
    {
      phase: 'Assess Market Potential',
      description: 'Determine total addressable market and opportunity',
      icon: <Target className="w-8 h-8" />,
      color: 'from-green-600 to-green-700',
      activities: [
        'Calculate total QMA by geography',
        'Segment population by PRIZM classification',
        'Estimate propensity distribution',
        'Project realistic production goals',
        'Identify high-value and high-payoff segments',
        'Prioritize markets for resource allocation'
      ]
    }
  ];

  const renderPhaseCards = (phases: TargetingPhase[]) => (
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center">
          <Target className="w-8 h-8 mr-3 text-yellow-600" />
          Targeting Methodology Framework
        </h1>
        <p className="text-gray-600 mt-2">
          Military-proven targeting cycles adapted for talent acquisition operations
        </p>
      </div>

      {/* Methodology Selector */}
      <div className="bg-white rounded-lg shadow-md mb-6">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveMethodology('d3ae')}
            className={`flex-1 px-6 py-4 font-semibold transition-colors ${
              activeMethodology === 'd3ae'
                ? 'border-b-2 border-yellow-600 text-yellow-600 bg-yellow-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <div className="text-center">
              <div className="text-xl font-bold">D3AE</div>
              <div className="text-xs mt-1">Detect • Discriminate • Decide • Act • Exploit/Assess</div>
            </div>
          </button>
          <button
            onClick={() => setActiveMethodology('f3a')}
            className={`flex-1 px-6 py-4 font-semibold transition-colors ${
              activeMethodology === 'f3a'
                ? 'border-b-2 border-yellow-600 text-yellow-600 bg-yellow-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <div className="text-center">
              <div className="text-xl font-bold">F3A</div>
              <div className="text-xs mt-1">Find • Fix • Finish • Assess</div>
            </div>
          </button>
          <button
            onClick={() => setActiveMethodology('mipoe')}
            className={`flex-1 px-6 py-4 font-semibold transition-colors ${
              activeMethodology === 'mipoe'
                ? 'border-b-2 border-yellow-600 text-yellow-600 bg-yellow-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <div className="text-center">
              <div className="text-xl font-bold">M-IPOE</div>
              <div className="text-xs mt-1">Market Intelligence Prep of Operations Environment</div>
            </div>
          </button>
        </div>
      </div>

      {/* Overview Card */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        {activeMethodology === 'd3ae' && (
          <>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">D3AE Targeting Cycle</h2>
            <p className="text-gray-700 mb-4">
              The <strong>D3AE</strong> (Detect, Discriminate, Decide, Act, Exploit/Assess) targeting methodology is a 
              systematic approach to identifying, prioritizing, and engaging high-value prospects. This cycle integrates 
              market intelligence (PRIZM, CBSA, P2P) with operational execution to maximize recruiting effectiveness.
            </p>
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
              <p className="text-sm text-gray-700">
                <strong>Best Used For:</strong> Strategic market analysis, campaign planning, and resource allocation 
                across multiple segments and geographic areas.
              </p>
            </div>
          </>
        )}
        
        {activeMethodology === 'f3a' && (
          <>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">F3A Targeting Cycle</h2>
            <p className="text-gray-700 mb-4">
              The <strong>F3A</strong> (Find, Fix, Finish, Assess) methodology focuses on the individual prospect lifecycle 
              from initial identification through contract completion. This approach emphasizes rapid engagement and 
              conversion while maintaining quality standards.
            </p>
            <div className="bg-green-50 border-l-4 border-green-500 p-4">
              <p className="text-sm text-gray-700">
                <strong>Best Used For:</strong> Recruiter-level operations, lead management, and individual prospect 
                engagement from first contact through MEPS processing.
              </p>
            </div>
          </>
        )}
        
        {activeMethodology === 'mipoe' && (
          <>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">M-IPOE Framework</h2>
            <p className="text-gray-700 mb-4">
              <strong>Market Intelligence Preparation of the Operations Environment (M-IPOE)</strong> is adapted from 
              military Intelligence Preparation of the Battlefield (IPB). This framework provides comprehensive market 
              analysis to support mission planning and resource allocation decisions.
            </p>
            <div className="bg-purple-50 border-l-4 border-purple-500 p-4">
              <p className="text-sm text-gray-700">
                <strong>Best Used For:</strong> Battalion and brigade-level mission planning, market analysis, 
                competitive assessment, and establishing the intelligence foundation for targeting decisions.
              </p>
            </div>
          </>
        )}
      </div>

      {/* Phase Cards */}
      {activeMethodology === 'd3ae' && renderPhaseCards(D3AE_PHASES)}
      {activeMethodology === 'f3a' && renderPhaseCards(F3A_PHASES)}
      {activeMethodology === 'mipoe' && renderPhaseCards(MIPOE_PHASES)}

      {/* Integration Guide */}
      <div className="mt-6 bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Users className="w-6 h-6 mr-2 text-yellow-600" />
          Integrating Methodologies with TAAIP
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border-2 border-blue-200 rounded-lg p-4">
            <h4 className="font-bold text-blue-800 mb-2">Strategic Planning (D3AE)</h4>
            <p className="text-sm text-gray-700 mb-3">
              Use for Fusion Team planning cycles, Targeting Working Group meetings, and brigade-level strategy.
            </p>
            <div className="text-xs text-gray-600">
              <div className="font-semibold mb-1">TAAIP Tools:</div>
              <ul className="list-disc list-inside space-y-1">
                <li>Market Segmentation Dashboard</li>
                <li>Mission Analysis (M-IPOE)</li>
                <li>Budget Tracker</li>
                <li>TWG Dashboard</li>
              </ul>
            </div>
          </div>
          
          <div className="border-2 border-green-200 rounded-lg p-4">
            <h4 className="font-bold text-green-800 mb-2">Tactical Execution (F3A)</h4>
            <p className="text-sm text-gray-700 mb-3">
              Use for station and recruiter-level operations, individual lead management, and daily activities.
            </p>
            <div className="text-xs text-gray-600">
              <div className="font-semibold mb-1">TAAIP Tools:</div>
              <ul className="list-disc list-inside space-y-1">
                <li>Recruiting Funnel Dashboard</li>
                <li>Lead Status Reports</li>
                <li>420T Command Center</li>
                <li>Calendar Scheduler</li>
              </ul>
            </div>
          </div>
          
          <div className="border-2 border-purple-200 rounded-lg p-4">
            <h4 className="font-bold text-purple-800 mb-2">Intelligence Foundation (M-IPOE)</h4>
            <p className="text-sm text-gray-700 mb-3">
              Use for establishing baseline market knowledge and supporting all targeting decisions.
            </p>
            <div className="text-xs text-gray-600">
              <div className="font-semibold mb-1">TAAIP Tools:</div>
              <ul className="list-disc list-inside space-y-1">
                <li>Market Potential Dashboard</li>
                <li>Analytics & Insights</li>
                <li>G2 Zone Analysis</li>
                <li>Event Performance</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TargetingMethodologyGuide;
