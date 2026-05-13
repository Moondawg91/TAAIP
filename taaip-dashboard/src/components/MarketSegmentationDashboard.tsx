import React, { useState, useEffect } from 'react';
import {
  Target, TrendingUp, Users, Award, MapPin, BarChart3,
  AlertCircle, CheckCircle, Info, DollarSign, Percent
} from 'lucide-react';
import { API_BASE } from '../config/api';
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

const SEGMENT_TYPE_COLORS: Record<PRIZMSegment['segment_type'], string> = {
  high_value: '#16a34a',
  high_payoff: '#ca8a04',
  opportunity: '#2563eb',
  supplemental: '#6b7280',
};

const PRIORITY_COLORS: Record<CBSAMetrics['priority_tier'], string> = {
  must_win: '#dc2626',
  must_keep: '#ca8a04',
  opportunity: '#2563eb',
  supplemental: '#6b7280',
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
      const [segmentResp, zoneResp, demographicsResp] = await Promise.all([
        fetch(`${API_BASE}/api/v2/market-intel/segment-analysis?segment_type=all`),
        fetch(`${API_BASE}/api/v2/g2-zones`),
        fetch(`${API_BASE}/api/market-intel/demographics`),
      ]);

      const segmentPayload = segmentResp.ok ? await segmentResp.json() : { segments: [] };
      const zonePayload = zoneResp.ok ? await zoneResp.json() : { data: [] };
      const demographicsPayload = demographicsResp.ok ? await demographicsResp.json() : { gaps: [] };

      const segmentRows = Array.isArray(segmentPayload?.segments) ? segmentPayload.segments : [];
      const zoneRows = Array.isArray(zonePayload?.data) ? zonePayload.data : [];
      const demoRows = Array.isArray(demographicsPayload?.gaps) ? demographicsPayload.gaps : [];

      const mappedSegments: PRIZMSegment[] = segmentRows.map((row: any, idx: number) => {
        const p2p = Number(row?.p2p_ratio ?? row?.p2p ?? 0);
        let segmentType: PRIZMSegment['segment_type'] = 'supplemental';
        if (p2p >= 1.2) segmentType = 'high_payoff';
        else if (p2p >= 1.0) segmentType = 'high_value';
        else if (p2p >= 0.8) segmentType = 'opportunity';

        return {
          segment_id: String(row?.segment_id ?? row?.id ?? `seg_${idx + 1}`),
          segment_name: String(row?.segment_name ?? row?.name ?? `Segment ${idx + 1}`),
          socioeconomic_rank: Number(row?.socioeconomic_rank ?? row?.rank ?? 0),
          life_stage: String(row?.life_stage ?? 'Unknown'),
          urbanicity: String(row?.urbanicity ?? 'Unknown'),
          population_pct: Number(row?.population_pct ?? row?.population_percent ?? 0),
          propensity_score: Number(row?.propensity_score ?? row?.opportunity_score ?? 0),
          p2p_ratio: p2p,
          enlistments: Number(row?.enlistments ?? row?.contracts ?? 0),
          qualified_population: Number(row?.qualified_population ?? row?.potential ?? 0),
          segment_type: segmentType,
          motivators: Array.isArray(row?.motivators) ? row.motivators : [],
          barriers: Array.isArray(row?.barriers) ? row.barriers : [],
          recommended_messaging: String(row?.recommended_messaging ?? ''),
        };
      });

      const mappedCbsa: CBSAMetrics[] = zoneRows.map((row: any, idx: number) => {
        const p2p = Number(row?.competitive_index ?? row?.p2p_ratio ?? 0);
        const penetration = Number(row?.market_penetration_rate ?? 0);
        let tier: CBSAMetrics['priority_tier'] = 'supplemental';
        if (penetration >= 1.2 || p2p >= 1.2) tier = 'must_win';
        else if (penetration >= 1.0 || p2p >= 1.0) tier = 'must_keep';
        else if (penetration >= 0.8) tier = 'opportunity';
        return {
          cbsa_code: String(row?.zone_id ?? row?.cbsa_code ?? `CBSA-${idx + 1}`),
          cbsa_name: String(row?.zone_name ?? row?.geographic_area ?? `Market ${idx + 1}`),
          cbsa_type: 'metro',
          population: Number(row?.population ?? row?.military_age_population ?? 0),
          qma: Number(row?.military_age_population ?? row?.population ?? 0),
          enlistments: Number(row?.enlistment_count ?? row?.conversion_count ?? 0),
          market_penetration: penetration,
          p2p_ratio: p2p,
          priority_tier: tier,
        };
      });

      const raceRows = demoRows
        .filter((row: any) => String(row?.dimension || '').toLowerCase().includes('race'))
        .map((row: any) => ({
          group: String(row?.group ?? 'Unknown'),
          population: Number(row?.population ?? 0),
          contracts: Number(row?.contracts ?? 0),
        }));
      const totalPopulation = raceRows.reduce((sum: number, r: any) => sum + r.population, 0);
      const totalContracts = raceRows.reduce((sum: number, r: any) => sum + r.contracts, 0);
      const mappedRace: RaceEthnicityP2P[] = raceRows.map((row: any) => {
        const populationPct = totalPopulation > 0 ? (row.population / totalPopulation) * 100 : 0;
        const contractPct = totalContracts > 0 ? (row.contracts / totalContracts) * 100 : 0;
        const p2p = populationPct > 0 ? contractPct / populationPct : 0;
        return {
          group: row.group,
          population_pct: populationPct,
          contract_pct: contractPct,
          p2p_ratio: p2p,
          band_status: getP2PBandStatus(p2p),
          pacing_battalions: [],
        };
      });

      setPrizmSegments(mappedSegments);
      setCbsaMetrics(mappedCbsa);
      setRaceEthnicityData(mappedRace);

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
