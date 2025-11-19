import React, { useState, useEffect } from 'react';
import {
  Target, TrendingUp, Users, Award, MapPin, BarChart3,
  AlertCircle, CheckCircle, Info, DollarSign, Percent
} from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

interface PRIZMSegment {
  segment_id: string;
  segment_name: string;
  socioeconomic_rank: number;
  life_stage: string;
  urbanicity: string;
  population_pct: number;
  propensity_score: number;
  p2p_ratio: number;
  enlistments: number;
  qualified_population: number;
  segment_type: 'high_value' | 'high_payoff' | 'opportunity' | 'supplemental';
  motivators: string[];
  barriers: string[];
  recommended_messaging: string;
}

interface CBSAMetrics {
  cbsa_code: string;
  cbsa_name: string;
  cbsa_type: 'metro' | 'micro';
  population: number;
  qma: number;
  enlistments: number;
  market_penetration: number;
  p2p_ratio: number;
  priority_tier: 'must_win' | 'must_keep' | 'opportunity' | 'supplemental';
}

interface RaceEthnicityP2P {
  group: string;
  population_pct: number;
  contract_pct: number;
  p2p_ratio: number;
  band_status: 'excellent' | 'underrepresented' | 'overrepresented';
  pacing_battalions: string[];
}

const SEGMENT_TYPE_COLORS = {
  high_value: '#10b981',
  high_payoff: '#f59e0b',
  opportunity: '#3b82f6',
  supplemental: '#6b7280'
};

const PRIORITY_COLORS = {
  must_win: '#dc2626',
  must_keep: '#f59e0b',
  opportunity: '#3b82f6',
  supplemental: '#6b7280'
};

const P2P_BAND = { min: 0.9, max: 1.1 };

export const MarketSegmentationDashboard: React.FC = () => {
  const [activeView, setActiveView] = useState<'prizm' | 'cbsa' | 'p2p' | 'strategy'>('prizm');
  const [prizmSegments, setPrizmSegments] = useState<PRIZMSegment[]>([]);
  const [cbsaMetrics, setCbsaMetrics] = useState<CBSAMetrics[]>([]);
  const [raceEthnicityData, setRaceEthnicityData] = useState<RaceEthnicityP2P[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<PRIZMSegment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSegmentationData();
  }, []);

  const fetchSegmentationData = async () => {
    setLoading(true);
    try {
      // Mock data - replace with actual API calls
      setPrizmSegments([
        {
          segment_id: 'S01',
          segment_name: 'Young Strivers',
          socioeconomic_rank: 28,
          life_stage: 'Young Adult',
          urbanicity: 'Urban',
          population_pct: 3.2,
          propensity_score: 18.5,
          p2p_ratio: 1.45,
          enlistments: 2850,
          qualified_population: 15420,
          segment_type: 'high_payoff',
          motivators: ['Career Training', 'Education Benefits', 'Travel', 'Leadership Development'],
          barriers: ['Length of Commitment', 'Deployment Concerns'],
          recommended_messaging: 'Focus on technical skill development and college benefits'
        },
        {
          segment_id: 'S02',
          segment_name: 'Small Town Pride',
          socioeconomic_rank: 45,
          life_stage: 'Young Adult',
          urbanicity: 'Rural',
          population_pct: 5.8,
          propensity_score: 22.3,
          p2p_ratio: 1.62,
          enlistments: 5640,
          qualified_population: 28900,
          segment_type: 'high_payoff',
          motivators: ['Service to Country', 'Family Tradition', 'Stable Career', 'Local Heroes'],
          barriers: ['Fear of Unknown', 'Leaving Home'],
          recommended_messaging: 'Emphasize patriotism, family legacy, and hometown hero stories'
        },
        {
          segment_id: 'S03',
          segment_name: 'Urban Achievers',
          socioeconomic_rank: 12,
          life_stage: 'Young Adult',
          urbanicity: 'Urban',
          population_pct: 4.5,
          propensity_score: 8.2,
          p2p_ratio: 0.75,
          enlistments: 1820,
          qualified_population: 22400,
          segment_type: 'opportunity',
          motivators: ['Leadership', 'Global Experience', 'Network Building'],
          barriers: ['Private Sector Options', 'Lifestyle Concerns'],
          recommended_messaging: 'Highlight leadership training and unique career paths'
        },
        {
          segment_id: 'S04',
          segment_name: 'Suburban Families',
          socioeconomic_rank: 22,
          life_stage: 'Middle Age',
          urbanicity: 'Suburban',
          population_pct: 6.1,
          propensity_score: 4.8,
          p2p_ratio: 0.62,
          enlistments: 950,
          qualified_population: 30400,
          segment_type: 'supplemental',
          motivators: ['Education Benefits', 'Healthcare', 'Job Security'],
          barriers: ['Age', 'Family Obligations', 'Comfort Zone'],
          recommended_messaging: 'Target influencers - parents and educators'
        },
        {
          segment_id: 'S05',
          segment_name: 'Tech Savvy Youth',
          socioeconomic_rank: 18,
          life_stage: 'Young Adult',
          urbanicity: 'Suburban',
          population_pct: 7.2,
          propensity_score: 15.7,
          p2p_ratio: 1.28,
          enlistments: 4520,
          qualified_population: 35800,
          segment_type: 'high_value',
          motivators: ['Technology Training', 'Cybersecurity', 'Innovation', 'Problem Solving'],
          barriers: ['Tech Industry Competition', 'Deployment'],
          recommended_messaging: 'Showcase Army cyber and technical career fields'
        }
      ]);

      setCbsaMetrics([
        {
          cbsa_code: '41860',
          cbsa_name: 'San Francisco-Oakland-Berkeley, CA',
          cbsa_type: 'metro',
          population: 4729484,
          qma: 312450,
          enlistments: 2850,
          market_penetration: 9.12,
          p2p_ratio: 0.68,
          priority_tier: 'opportunity'
        },
        {
          cbsa_code: '41884',
          cbsa_name: 'San Antonio-New Braunfels, TX',
          cbsa_type: 'metro',
          population: 2558143,
          qma: 185600,
          enlistments: 4920,
          market_penetration: 26.50,
          p2p_ratio: 1.85,
          priority_tier: 'must_win'
        },
        {
          cbsa_code: '26420',
          cbsa_name: 'Houston-The Woodlands-Sugar Land, TX',
          cbsa_type: 'metro',
          population: 7122240,
          qma: 498700,
          enlistments: 6840,
          market_penetration: 13.72,
          p2p_ratio: 1.12,
          priority_tier: 'must_keep'
        },
        {
          cbsa_code: '19124',
          cbsa_name: 'Columbus, GA-AL',
          cbsa_type: 'metro',
          population: 328883,
          qma: 24200,
          enlistments: 1680,
          market_penetration: 69.42,
          p2p_ratio: 2.45,
          priority_tier: 'must_win'
        }
      ]);

      setRaceEthnicityData([
        {
          group: 'White',
          population_pct: 60.2,
          contract_pct: 58.5,
          p2p_ratio: 0.97,
          band_status: 'excellent',
          pacing_battalions: ['1-1 BN', '2-4 BN', '3-7 BN']
        },
        {
          group: 'Hispanic/Latino',
          population_pct: 18.8,
          contract_pct: 16.2,
          p2p_ratio: 0.86,
          band_status: 'underrepresented',
          pacing_battalions: ['4-2 BN', '1-8 BN', '5-3 BN']
        },
        {
          group: 'Black/African American',
          population_pct: 13.6,
          contract_pct: 15.8,
          p2p_ratio: 1.16,
          band_status: 'overrepresented',
          pacing_battalions: ['2-6 BN', '3-2 BN', '1-5 BN']
        },
        {
          group: 'Asian',
          population_pct: 6.1,
          contract_pct: 4.2,
          p2p_ratio: 0.69,
          band_status: 'underrepresented',
          pacing_battalions: ['1-3 BN', '4-5 BN', '2-9 BN']
        },
        {
          group: 'Other',
          population_pct: 1.3,
          contract_pct: 5.3,
          p2p_ratio: 4.08,
          band_status: 'overrepresented',
          pacing_battalions: ['3-1 BN', '2-2 BN']
        }
      ]);

    } catch (error) {
      console.error('Error fetching segmentation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getP2PBandStatus = (p2p: number) => {
    if (p2p >= P2P_BAND.min && p2p <= P2P_BAND.max) return 'excellent';
    if (p2p < P2P_BAND.min) return 'underrepresented';
    return 'overrepresented';
  };

  const getP2PColor = (status: string) => {
    const colors = {
      excellent: 'bg-green-100 text-green-800 border-green-300',
      underrepresented: 'bg-red-100 text-red-800 border-red-300',
      overrepresented: 'bg-yellow-100 text-yellow-800 border-yellow-300'
    };
    return colors[status as keyof typeof colors];
  };

  const renderPRIZMView = () => (
    <div className="space-y-6">
      {/* PRIZM Overview */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Target className="w-6 h-6 mr-2 text-yellow-600" />
          Claritas PRIZM Premier Segmentation
        </h3>
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
          <p className="text-sm text-gray-700">
            <strong>PRIZM</strong> (Potential Rating Index for Zip Markets) classifies households into 68 segments based on
            buying habits, life stage, urbanicity, and location (ZIP+4). Segments are ordered by socioeconomic rank and
            integrated with JAMRS data for youth attitudes toward military service.
          </p>
        </div>

        {/* Segment Type Legend */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
          <div className="border-2 border-green-300 bg-green-50 rounded-lg p-3">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="font-bold text-sm text-gray-800">High Value Segment</span>
            </div>
            <p className="text-xs text-gray-600">Top segments accounting for &gt;40% of total potential</p>
          </div>
          <div className="border-2 border-yellow-300 bg-yellow-50 rounded-lg p-3">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
              <span className="font-bold text-sm text-gray-800">High Payoff Segment</span>
            </div>
            <p className="text-xs text-gray-600">Overrepresented with P2P &gt; 1.0 from high value segments</p>
          </div>
          <div className="border-2 border-blue-300 bg-blue-50 rounded-lg p-3">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              <span className="font-bold text-sm text-gray-800">Market of Opportunity</span>
            </div>
            <p className="text-xs text-gray-600">Untapped potential with room for growth</p>
          </div>
          <div className="border-2 border-gray-300 bg-gray-50 rounded-lg p-3">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-gray-500 rounded-full mr-2"></div>
              <span className="font-bold text-sm text-gray-800">Supplemental</span>
            </div>
            <p className="text-xs text-gray-600">Lower propensity, secondary focus</p>
          </div>
        </div>

        {/* Segments Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {prizmSegments.map((segment) => (
            <div
              key={segment.segment_id}
              className="border-2 rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
              style={{ borderColor: SEGMENT_TYPE_COLORS[segment.segment_type] }}
              onClick={() => setSelectedSegment(segment)}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-bold text-lg text-gray-800">{segment.segment_name}</h4>
                  <p className="text-sm text-gray-600">Rank #{segment.socioeconomic_rank} • {segment.life_stage} • {segment.urbanicity}</p>
                </div>
                <div
                  className="px-3 py-1 rounded-full text-xs font-bold text-white"
                  style={{ backgroundColor: SEGMENT_TYPE_COLORS[segment.segment_type] }}
                >
                  {segment.segment_type.replace('_', ' ').toUpperCase()}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="text-center">
                  <p className="text-xs text-gray-600">Population %</p>
                  <p className="text-lg font-bold text-gray-800">{segment.population_pct.toFixed(1)}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-600">Propensity</p>
                  <p className="text-lg font-bold text-blue-600">{segment.propensity_score.toFixed(1)}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-600">P2P Ratio</p>
                  <p className={`text-lg font-bold ${
                    segment.p2p_ratio >= 1.0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {segment.p2p_ratio.toFixed(2)}
                  </p>
                </div>
              </div>

              <div className="border-t pt-3">
                <p className="text-xs font-semibold text-gray-700 mb-1">Top Motivators:</p>
                <div className="flex flex-wrap gap-1">
                  {segment.motivators.slice(0, 3).map((motivator, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                      {motivator}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Segment Detail */}
      {selectedSegment && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800">Segment Deep Dive: {selectedSegment.segment_name}</h3>
            <button
              onClick={() => setSelectedSegment(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕ Close
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-bold text-gray-700 mb-3">Key Motivators</h4>
              <ul className="space-y-2">
                {selectedSegment.motivators.map((motivator, idx) => (
                  <li key={idx} className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{motivator}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-bold text-gray-700 mb-3">Barriers to Service</h4>
              <ul className="space-y-2">
                {selectedSegment.barriers.map((barrier, idx) => (
                  <li key={idx} className="flex items-start">
                    <AlertCircle className="w-4 h-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{barrier}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-500 p-4">
            <h4 className="font-bold text-gray-800 mb-2 flex items-center">
              <Info className="w-5 h-5 mr-2 text-yellow-600" />
              Recommended Messaging Strategy
            </h4>
            <p className="text-sm text-gray-700">{selectedSegment.recommended_messaging}</p>
          </div>
        </div>
      )}
    </div>
  );

  const renderCBSAView = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <MapPin className="w-6 h-6 mr-2 text-yellow-600" />
        Core-Based Statistical Area (CBSA) Analysis
      </h3>
      
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
        <p className="text-sm text-gray-700 mb-2">
          <strong>CBSAs</strong> are metropolitan areas and surrounding counties with close socioeconomic ties.
          There are 388 Metro (&gt;50K pop) and 541 Micro (&gt;10K pop) CBSAs.
        </p>
        <p className="text-sm text-gray-700 font-semibold">
          CBSAs account for ~95% of QMA, ~93% of enlistments, and only 45% of U.S. square mileage.
        </p>
      </div>

      {/* Priority Tier Legend */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
        <div className="border-2 border-red-300 bg-red-50 rounded-lg p-3">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-600 rounded-full mr-2"></div>
            <span className="font-bold text-sm">Must Win</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">Critical high-potential markets</p>
        </div>
        <div className="border-2 border-yellow-300 bg-yellow-50 rounded-lg p-3">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-600 rounded-full mr-2"></div>
            <span className="font-bold text-sm">Must Keep</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">Sustain current performance</p>
        </div>
        <div className="border-2 border-blue-300 bg-blue-50 rounded-lg p-3">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-600 rounded-full mr-2"></div>
            <span className="font-bold text-sm">Opportunity</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">Growth potential markets</p>
        </div>
        <div className="border-2 border-gray-300 bg-gray-50 rounded-lg p-3">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-600 rounded-full mr-2"></div>
            <span className="font-bold text-sm">Supplemental</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">Supporting markets</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b-2 border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">CBSA</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Type</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">QMA</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Enlistments</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Penetration</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">P2P Ratio</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Priority</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {cbsaMetrics.map((cbsa) => (
              <tr key={cbsa.cbsa_code} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div>
                    <p className="font-medium text-gray-800">{cbsa.cbsa_name}</p>
                    <p className="text-xs text-gray-500">{cbsa.cbsa_code}</p>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                    cbsa.cbsa_type === 'metro' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                  }`}>
                    {cbsa.cbsa_type.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-semibold text-gray-800">
                  {cbsa.qma.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right font-semibold text-gray-800">
                  {cbsa.enlistments.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right text-gray-700">
                  {cbsa.market_penetration.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`font-bold ${
                    cbsa.p2p_ratio >= 1.0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {cbsa.p2p_ratio.toFixed(2)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className="px-3 py-1 rounded-full text-xs font-bold text-white"
                    style={{ backgroundColor: PRIORITY_COLORS[cbsa.priority_tier] }}
                  >
                    {cbsa.priority_tier.replace('_', ' ').toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 bg-green-50 border-l-4 border-green-500 p-4">
        <h4 className="font-bold text-gray-800 mb-2">Market Penetration Formula</h4>
        <p className="text-sm text-gray-700">
          Market Penetration = (Enlistments / QMA) × 1,000 youth
        </p>
        <p className="text-xs text-gray-600 mt-2">
          A localized measure of market propensity comparing enlistment rate per 1,000 qualified youth
        </p>
      </div>
    </div>
  );

  const renderP2PView = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <Users className="w-6 h-6 mr-2 text-yellow-600" />
        Race/Ethnicity Production-to-Potential (P2P) Analysis
      </h3>

      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
        <p className="text-sm text-gray-700 mb-2">
          <strong>P2P Ratio</strong> = (% of contracts from group) ÷ (% of population from group)
        </p>
        <p className="text-sm text-gray-700">
          <strong>Band of Excellence:</strong> 0.9 - 1.1 (indicating proportional representation)
        </p>
      </div>

      {/* P2P Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={raceEthnicityData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="group" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="population_pct" fill="#94a3b8" name="Population %" />
            <Bar dataKey="contract_pct" fill="#3b82f6" name="Contract %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* P2P Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b-2 border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Race/Ethnicity</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Pop %</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Contract %</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">P2P Ratio</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Pacing Battalions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {raceEthnicityData.map((group) => (
              <tr key={group.group} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-800">{group.group}</td>
                <td className="px-4 py-3 text-right text-gray-700">{group.population_pct.toFixed(1)}%</td>
                <td className="px-4 py-3 text-right text-gray-700">{group.contract_pct.toFixed(1)}%</td>
                <td className="px-4 py-3 text-right font-bold text-lg">
                  <span className={
                    group.band_status === 'excellent' ? 'text-green-600' :
                    group.band_status === 'underrepresented' ? 'text-red-600' :
                    'text-yellow-600'
                  }>
                    {group.p2p_ratio.toFixed(2)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getP2PColor(group.band_status)}`}>
                    {group.band_status.replace('_', ' ').toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {group.pacing_battalions.slice(0, 3).map((bn, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                        {bn}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-500 p-4">
        <h4 className="font-bold text-gray-800 mb-2">Pacing Battalions</h4>
        <p className="text-sm text-gray-700">
          The 10 battalions for each race/ethnicity group with the highest population. These represent centers of gravity
          for USAREC with respect to race/ethnicity production.
        </p>
      </div>
    </div>
  );

  const renderStrategyView = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <BarChart3 className="w-6 h-6 mr-2 text-yellow-600" />
          Market Segmentation Strategy Guide
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* JAMRS Guide to Marketing */}
          <div className="border-2 border-blue-200 rounded-lg p-4">
            <h4 className="font-bold text-blue-800 mb-3">JAMRS - "Guide to Marketing"</h4>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Builds on PRIZM Segmentation with Influencer Poll, Youth Poll, and New Recruit Survey data</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Provides youth, new recruit, and influencer attitudes toward military service</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Used by industry marketers to find and attract target customers</span>
              </li>
            </ul>
          </div>

          {/* USAREC G2 Guide */}
          <div className="border-2 border-green-200 rounded-lg p-4">
            <h4 className="font-bold text-green-800 mb-3">USAREC G2 - "Recruiter Guide to Market Segmentation"</h4>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Army-specific motivators and barriers to military service</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Identifies high-value & high-payoff segments by battalion</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                <span>Provides segment snap-shot descriptions for starting market conversations</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Key Definitions */}
        <div className="mt-6 space-y-4">
          <div className="bg-gradient-to-r from-green-50 to-white border-l-4 border-green-500 p-4">
            <h5 className="font-bold text-gray-800 mb-2">High Value Segment (HVS)</h5>
            <p className="text-sm text-gray-700">
              Segments ordered from highest to lowest potential. The top segments, in aggregate, account for just over
              40% of the total potential for the market.
            </p>
          </div>

          <div className="bg-gradient-to-r from-yellow-50 to-white border-l-4 border-yellow-500 p-4">
            <h5 className="font-bold text-gray-800 mb-2">High Payoff Segment (HPS)</h5>
            <p className="text-sm text-gray-700">
              An overrepresented segment in terms of P2P from within the subset of high value segments. These segments
              each have a P2P &gt; 1.0 and production greater than its proportion of the population.
            </p>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-white border-l-4 border-blue-500 p-4">
            <h5 className="font-bold text-gray-800 mb-2">Propensity</h5>
            <p className="text-sm text-gray-700">
              Estimated from semi-annual DoD Youth Poll surveys asking about likelihood of military service within the
              next few years. Historically between 10% - 15% of participants indicate propensity.
            </p>
          </div>

          <div className="bg-gradient-to-r from-purple-50 to-white border-l-4 border-purple-500 p-4">
            <h5 className="font-bold text-gray-800 mb-2">Market Penetration</h5>
            <p className="text-sm text-gray-700">
              A localized, general measure of market propensity. Compares rate of enlistments per 1,000 youth (QMA) in
              the market. Good measure of relative recruiting success influenced by propensity, operations, and proximity
              to military populations.
            </p>
          </div>
        </div>
      </div>

      {/* Geotargeting vs Geofencing */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Digital Targeting Strategies</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border-2 border-purple-200 bg-purple-50 rounded-lg p-4">
            <h4 className="font-bold text-purple-800 mb-3">Geofencing</h4>
            <p className="text-sm text-gray-700 mb-3">
              A more general audience within a geographic area. Delivers digital messages to attendees at an event using
              the venue to define the location.
            </p>
            <div className="bg-white rounded p-3">
              <p className="text-xs font-semibold text-gray-600 mb-1">Use Cases:</p>
              <ul className="text-xs text-gray-700 space-y-1">
                <li>• Drive traffic to recruiters at large events</li>
                <li>• Deliver promotional ads to students in school districts</li>
              </ul>
            </div>
          </div>

          <div className="border-2 border-indigo-200 bg-indigo-50 rounded-lg p-4">
            <h4 className="font-bold text-indigo-800 mb-3">Geotargeting</h4>
            <p className="text-sm text-gray-700 mb-3">
              A more specifically defined audience in a geographic area based on demographic and behavioral characteristics.
            </p>
            <div className="bg-white rounded p-3">
              <p className="text-xs font-semibold text-gray-600 mb-1">Use Cases:</p>
              <ul className="text-xs text-gray-700 space-y-1">
                <li>• Deliver ads to Hispanic men age 18-24 within radius of event</li>
                <li>• Target specific PRIZM segments in high-payoff CBSAs</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading segmentation data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center">
          <Target className="w-8 h-8 mr-3 text-yellow-600" />
          Market Segmentation & Intelligence Dashboard
        </h1>
        <p className="text-gray-600 mt-2">
          PRIZM segments, CBSA analysis, P2P ratios, and strategic targeting guidance for high-value markets
        </p>
      </div>

      {/* View Tabs */}
      <div className="bg-white rounded-lg shadow-md mb-6">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          <button
            onClick={() => setActiveView('prizm')}
            className={`px-6 py-3 font-semibold transition-colors whitespace-nowrap ${
              activeView === 'prizm'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            PRIZM Segments
          </button>
          <button
            onClick={() => setActiveView('cbsa')}
            className={`px-6 py-3 font-semibold transition-colors whitespace-nowrap ${
              activeView === 'cbsa'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            CBSA Analysis
          </button>
          <button
            onClick={() => setActiveView('p2p')}
            className={`px-6 py-3 font-semibold transition-colors whitespace-nowrap ${
              activeView === 'p2p'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            P2P Analysis
          </button>
          <button
            onClick={() => setActiveView('strategy')}
            className={`px-6 py-3 font-semibold transition-colors whitespace-nowrap ${
              activeView === 'strategy'
                ? 'border-b-2 border-yellow-600 text-yellow-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Strategy Guide
          </button>
        </div>
      </div>

      {/* Content */}
      {activeView === 'prizm' && renderPRIZMView()}
      {activeView === 'cbsa' && renderCBSAView()}
      {activeView === 'p2p' && renderP2PView()}
      {activeView === 'strategy' && renderStrategyView()}
    </div>
  );
};

export default MarketSegmentationDashboard;
