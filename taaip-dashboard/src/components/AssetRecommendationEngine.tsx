import React, { useState, useEffect } from 'react';
import {
  Target, Users, Calendar, MapPin, TrendingUp, Award, CheckCircle,
  AlertTriangle, Lightbulb, Settings, Filter, Download
} from 'lucide-react';
import { API_BASE } from '../config/api';

interface AssetTier {
  tier: 1 | 2 | 3;
  name: string;
  description: string;
  examples: string[];
}

interface Asset {
  asset_id: string;
  name: string;
  tier: 1 | 2 | 3;
  type: string;
  availability: 'available' | 'scheduled' | 'unavailable';
  effectiveness_score: number;
  cost: number;
  lead_generation_avg: number;
  best_for: string[];
}

interface ConOPInput {
  conop_id: string;
  title: string;
  event_type: string;
  target_audience: string;
  location: string;
  zipcode: string;
  expected_attendance: number;
  budget: number;
  date: string;
  priority: 'must_keep' | 'must_win' | 'standard';
}

interface AssetRecommendation {
  primary_assets: Asset[];
  alternate_assets: Asset[];
  reasoning: string;
  confidence_score: number;
  estimated_leads: number;
  estimated_roi: number;
  warnings: string[];
}

interface DecisionSupportRisk {
  risk: string;
  count: number;
}

interface DecisionSupportItem {
  asset_id: string;
  asset: string;
  score: number;
}

interface AssetReadiness {
  total_assets: number;
  eligible_assets: number;
  blocked_assets: number;
  assets_missing_rule_validation: number;
  assets_requiring_emm: number;
  assets_requiring_emm_portal: number;
}

const ASSET_TIERS: AssetTier[] = [
  {
    tier: 1,
    name: 'Tier 1 - High Impact',
    description: 'National-level assets with highest engagement and lead generation',
    examples: ['Army Experience Center', 'Mobile Esports Gaming Trailer', 'Black Daggers Parachute Team', 'Army Band']
  },
  {
    tier: 2,
    name: 'Tier 2 - Regional',
    description: 'Regional marketing assets for sustained engagement',
    examples: ['Regional Marketing Coordinators', 'Digital Campaigns', 'Social Media Influencers', 'Virtual Reality Simulators']
  },
  {
    tier: 3,
    name: 'Tier 3 - Local',
    description: 'Station/company-level resources',
    examples: ['Recruiter Teams', 'Local ROTC Support', 'Community Partners', 'Swag/Materials']
  }
];

const AssetRecommendationEngine: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [conopInput, setConopInput] = useState<ConOPInput>({
    conop_id: '',
    title: '',
    event_type: 'career_fair',
    target_audience: 'high_school',
    location: '',
    zipcode: '',
    expected_attendance: 0,
    budget: 0,
    date: '',
    priority: 'standard'
  });
  const [recommendations, setRecommendations] = useState<AssetRecommendation | null>(null);
  const [availableAssets, setAvailableAssets] = useState<Asset[]>([]);
  const [historicalConops, setHistoricalConops] = useState<ConOPInput[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [topRisks, setTopRisks] = useState<DecisionSupportRisk[]>([]);
  const [recommendedNow, setRecommendedNow] = useState<DecisionSupportItem[]>([]);
  const [readiness, setReadiness] = useState<AssetReadiness | null>(null);

  useEffect(() => {
    loadAssets();
    loadHistoricalConops();
    loadReadiness();
  }, []);

  const fetchWithTimeout = async (url: string, timeoutMs = 10000) => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, { signal: controller.signal });
    } finally {
      window.clearTimeout(timeoutId);
    }
  };

  const loadAssets = async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/asset_recommendations`);
      const payload = await response.json();
      const recommendations = Array.isArray(payload?.recommendations) ? payload.recommendations : [];
      const mapped: Asset[] = recommendations.map((r: any, idx: number) => ({
        asset_id: String(r?.asset_id ?? `asset_${idx + 1}`),
        name: String(r?.asset ?? 'Unnamed Asset'),
        tier: (r?.priority === 'HIGH' ? 1 : r?.priority === 'MEDIUM' ? 2 : 3) as 1 | 2 | 3,
        type: String(r?.category ?? 'General'),
        availability: r?.execution === 'not_executable_in_timeline' ? 'unavailable' : (r?.execution === 'executable_with_risk' ? 'scheduled' : 'available'),
        effectiveness_score: Number(r?.score ?? 0) || 0,
        cost: Number(r?.estimated_cost ?? 0) || 0,
        lead_generation_avg: Number(r?.estimated_leads ?? 0) || 0,
        best_for: Array.isArray(r?.supports) ? r.supports : [],
      }));
      setAvailableAssets(mapped);
      setStatusMessage('');
    } catch (error) {
      console.error('Error loading asset recommendations:', error);
      setAvailableAssets([]);
      setStatusMessage('Asset availability data is temporarily unavailable.');
    }
  };

  const loadHistoricalConops = async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/asset_recommendations/decision_support`);
      const payload = await response.json();
      const recommended = Array.isArray(payload?.recommended_now) ? payload.recommended_now : [];
      setRecommendedNow(recommended);
      setTopRisks(Array.isArray(payload?.top_risks) ? payload.top_risks : []);
      const mapped: ConOPInput[] = recommended.map((r: any, idx: number) => ({
        conop_id: `conop_${idx + 1}`,
        title: String(r?.asset ?? ''),
        event_type: 'career_fair',
        target_audience: 'high_school',
        location: '',
        zipcode: '',
        expected_attendance: Number(r?.score ?? 0) * 10,
        budget: 0,
        date: new Date().toISOString().split('T')[0],
        priority: 'standard'
      }));
      setHistoricalConops(mapped);
    } catch (error) {
      console.error('Error loading decision support history:', error);
      setHistoricalConops([]);
      setRecommendedNow([]);
      setTopRisks([]);
      setStatusMessage('Decision support history is temporarily unavailable.');
    }
  };

  const loadReadiness = async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/api/asset_recommendations/readiness`);
      const payload = await response.json();
      setReadiness(payload);
    } catch (error) {
      console.error('Error loading asset readiness:', error);
      setReadiness(null);
      setStatusMessage('Readiness checks are temporarily unavailable.');
    }
  };

  const generateRecommendations = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (conopInput.date) params.append('event_date', conopInput.date);
      if (conopInput.event_type) params.append('event_type', conopInput.event_type);
      if (conopInput.priority) params.append('command_scope', conopInput.priority === 'must_win' ? 'BDE' : 'BN');
      if (conopInput.location) params.append('geography_scope', conopInput.location);
      params.append('funding_available', 'baseline');

      const response = await fetchWithTimeout(`${API_BASE}/api/asset_recommendations?${params.toString()}`);
      const payload = await response.json();
      const liveRecommendations = Array.isArray(payload?.recommendations) ? payload.recommendations : [];
      const actionable = liveRecommendations.filter((item: any) => item.execution !== 'not_executable_in_timeline');
      const primaryIds = actionable.slice(0, 3).map((item: any) => String(item.asset_id));
      const alternateIds = actionable.slice(3, 6).map((item: any) => String(item.asset_id));

      const primary = availableAssets.filter((asset) => primaryIds.includes(asset.asset_id));
      const alternate = availableAssets.filter((asset) => alternateIds.includes(asset.asset_id));
      const estimatedLeads = primary.reduce((sum, asset) => sum + asset.lead_generation_avg, 0);
      const totalCost = primary.reduce((sum, asset) => sum + asset.cost, 0);

      const warnings = actionable
        .slice(0, 3)
        .flatMap((item: any) => Array.isArray(item.warning_reasons) ? item.warning_reasons : [])
        .map((reason: string) => reason.replace(/_/g, ' '));

      const readinessSummary = payload?.context
        ? `Scope ${String(payload.context.command_scope || 'connected')} with ${String(payload.context.days_until_event ?? 'unknown')} days until event.`
        : 'Live rules and operational context applied.';

      setRecommendations({
        primary_assets: primary,
        alternate_assets: alternate,
        reasoning: `Live backend ranking applied for ${conopInput.event_type} targeting ${conopInput.target_audience}. ${readinessSummary}`,
        confidence_score: actionable.length > 0 ? 90 : 40,
        estimated_leads: estimatedLeads,
        estimated_roi: totalCost > 0 ? parseFloat((estimatedLeads / (totalCost / 1000)).toFixed(2)) : 0,
        warnings,
      });

      await loadHistoricalConops();
      await loadReadiness();
      setStatusMessage('');
    } catch (error) {
      console.error('Error generating asset recommendations:', error);
      setRecommendations(null);
      setStatusMessage('Unable to generate recommendations right now. Check connectivity and try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadHistoricalConop = (conop: ConOPInput) => {
    setConopInput(conop);
    setShowHistory(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-800 to-purple-900 rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3">
          <Lightbulb className="w-8 h-8 text-yellow-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Asset Recommendation Engine</h1>
            <p className="text-purple-200 text-sm">AI-powered asset allocation for ConOPs and Projects</p>
          </div>
        </div>
      </div>

      {statusMessage && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-900">
          {statusMessage}
        </div>
      )}

      {/* Asset Tier Reference */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {ASSET_TIERS.map((tier) => (
          <div key={tier.tier} className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Award className={`w-6 h-6 ${tier.tier === 1 ? 'text-yellow-600' : tier.tier === 2 ? 'text-blue-600' : 'text-gray-600'}`} />
              <h3 className="font-bold text-gray-800">{tier.name}</h3>
            </div>
            <p className="text-sm text-gray-600 mb-3">{tier.description}</p>
            <div className="space-y-1">
              {tier.examples.map((ex, idx) => (
                <p key={idx} className="text-xs text-gray-500">• {ex}</p>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ConOP Input Form */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-md border-2 border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Settings className="w-6 h-6 text-purple-600" />
              ConOP / Project Input
            </h2>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              Load Historical
            </button>
          </div>

          {showHistory && (
            <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="font-semibold text-sm text-gray-800 mb-2">Recent ConOPs:</p>
              {historicalConops.map((conop) => (
                <button
                  key={conop.conop_id}
                  onClick={() => loadHistoricalConop(conop)}
                  className="block w-full text-left p-2 mb-2 bg-white rounded hover:bg-blue-100 border border-blue-200"
                >
                  <p className="font-medium text-sm text-gray-800">{conop.title}</p>
                  <p className="text-xs text-gray-600">{conop.location} • {conop.date}</p>
                </button>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Event Title</label>
              <input
                type="text"
                value={conopInput.title}
                onChange={(e) => setConopInput({ ...conopInput, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="e.g., Houston Tech Career Fair"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
              <select
                value={conopInput.event_type}
                onChange={(e) => setConopInput({ ...conopInput, event_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="career_fair">Career Fair</option>
                <option value="college_event">College Event</option>
                <option value="gaming_event">Gaming/Esports</option>
                <option value="community_event">Community Event</option>
                <option value="sporting_event">Sporting Event</option>
                <option value="virtual_event">Virtual Event</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Audience</label>
              <select
                value={conopInput.target_audience}
                onChange={(e) => setConopInput({ ...conopInput, target_audience: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="high_school">High School</option>
                <option value="college">College</option>
                <option value="general_public">General Public</option>
                <option value="professionals">Young Professionals</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
              <input
                type="text"
                value={conopInput.location}
                onChange={(e) => setConopInput({ ...conopInput, location: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="City, State"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Zipcode</label>
              <input
                type="text"
                value={conopInput.zipcode}
                onChange={(e) => setConopInput({ ...conopInput, zipcode: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                placeholder="77001"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expected Attendance</label>
              <input
                type="number"
                value={conopInput.expected_attendance}
                onChange={(e) => setConopInput({ ...conopInput, expected_attendance: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Budget ($)</label>
              <input
                type="number"
                value={conopInput.budget}
                onChange={(e) => setConopInput({ ...conopInput, budget: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Event Date</label>
              <input
                type="date"
                value={conopInput.date}
                onChange={(e) => setConopInput({ ...conopInput, date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <select
                value={conopInput.priority}
                onChange={(e) => setConopInput({ ...conopInput, priority: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="standard">Standard</option>
                <option value="must_keep">Must Keep</option>
                <option value="must_win">Must Win</option>
              </select>
            </div>
          </div>

          <button
            onClick={generateRecommendations}
            disabled={!conopInput.title || !conopInput.date || conopInput.budget === 0}
            className="w-full mt-6 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-bold rounded-lg flex items-center justify-center gap-2"
          >
            <Target className="w-5 h-5" />
            Generate Asset Recommendations
          </button>
        </div>

        {/* Available Assets Summary */}
        <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-600" />
            Asset Inventory
          </h3>
          {readiness && (
            <div className="mb-4 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded border border-green-200 bg-green-50 p-2">
                <p className="text-gray-600">Eligible Now</p>
                <p className="font-bold text-green-700">{readiness.eligible_assets}</p>
              </div>
              <div className="rounded border border-red-200 bg-red-50 p-2">
                <p className="text-gray-600">Blocked</p>
                <p className="font-bold text-red-700">{readiness.blocked_assets}</p>
              </div>
            </div>
          )}
          <div className="space-y-3">
            {[1, 2, 3].map((tier) => {
              const tierAssets = availableAssets.filter(a => a.tier === tier);
              const available = tierAssets.filter(a => a.availability === 'available').length;
              return (
                <div key={tier} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-sm text-gray-800">Tier {tier}</span>
                    <span className={`text-xs font-bold px-2 py-1 rounded ${
                      available > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {available}/{tierAssets.length} Available
                    </span>
                  </div>
                  {tierAssets.slice(0, 3).map((asset) => (
                    <div key={asset.asset_id} className="text-xs text-gray-600 flex items-center gap-1 mt-1">
                      <span className={`w-2 h-2 rounded-full ${
                        asset.availability === 'available' ? 'bg-green-500' :
                        asset.availability === 'scheduled' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}></span>
                      {asset.name}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
          {topRisks.length > 0 && (
            <div className="mt-4 border-t border-gray-200 pt-4">
              <p className="text-xs font-bold uppercase tracking-wide text-gray-700 mb-2">Top Execution Risks</p>
              <div className="space-y-1">
                {topRisks.slice(0, 4).map((risk) => (
                  <div key={risk.risk} className="flex items-center justify-between text-xs text-gray-600">
                    <span>{risk.risk.replace(/_/g, ' ')}</span>
                    <span className="font-bold text-gray-800">{risk.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recommendations Output */}
      {recommendations && (
        <div className="bg-white rounded-lg shadow-lg border-2 border-purple-500 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <CheckCircle className="w-7 h-7 text-green-600" />
              Asset Recommendations
            </h2>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-600">Confidence Score</p>
                <p className="text-2xl font-bold text-purple-600">{recommendations.confidence_score}%</p>
              </div>
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2">
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>

          {/* Warnings */}
          {recommendations.warnings.length > 0 && (
            <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-sm text-yellow-800 mb-2">Warnings:</p>
                  {recommendations.warnings.map((warning, idx) => (
                    <p key={idx} className="text-sm text-yellow-700">• {warning}</p>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Estimated Outcomes */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <TrendingUp className="w-6 h-6 text-green-600 mb-2" />
              <p className="text-xs text-gray-600">Est. Lead Generation</p>
              <p className="text-2xl font-bold text-green-800">{recommendations.estimated_leads}</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <Award className="w-6 h-6 text-blue-600 mb-2" />
              <p className="text-xs text-gray-600">Est. ROI</p>
              <p className="text-2xl font-bold text-blue-800">{recommendations.estimated_roi}x</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <Target className="w-6 h-6 text-purple-600 mb-2" />
              <p className="text-xs text-gray-600">Total Cost</p>
              <p className="text-2xl font-bold text-purple-800">
                ${recommendations.primary_assets.reduce((sum, a) => sum + a.cost, 0).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Reasoning */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm font-semibold text-gray-800 mb-2">AI Reasoning:</p>
            <p className="text-sm text-gray-700">{recommendations.reasoning}</p>
            {recommendedNow.length > 0 && (
              <div className="mt-3 border-t border-blue-200 pt-3">
                <p className="text-xs font-bold uppercase tracking-wide text-gray-700 mb-2">Current Backend Recommendations</p>
                <div className="space-y-1">
                  {recommendedNow.slice(0, 3).map((item) => (
                    <div key={item.asset_id} className="flex items-center justify-between text-xs text-gray-700">
                      <span>{item.asset}</span>
                      <span className="font-bold">{item.score}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Primary Assets */}
          <div className="mb-6">
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Award className="w-5 h-5 text-yellow-600" />
              Primary Asset Recommendations
            </h3>
            <div className="space-y-3">
              {recommendations.primary_assets.map((asset) => (
                <div key={asset.asset_id} className="bg-gradient-to-r from-yellow-50 to-white rounded-lg p-4 border-2 border-yellow-300">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          asset.tier === 1 ? 'bg-yellow-100 text-yellow-800' :
                          asset.tier === 2 ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          Tier {asset.tier}
                        </span>
                        <h4 className="font-bold text-gray-800">{asset.name}</h4>
                        <span className={`ml-auto px-2 py-1 rounded text-xs font-bold ${
                          asset.availability === 'available' ? 'bg-green-100 text-green-800' :
                          asset.availability === 'scheduled' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {asset.availability}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{asset.type}</p>
                      <div className="grid grid-cols-4 gap-4 text-xs">
                        <div>
                          <p className="text-gray-500">Effectiveness</p>
                          <p className="font-bold text-purple-700">{asset.effectiveness_score}/10</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Avg. Leads</p>
                          <p className="font-bold text-green-700">{asset.lead_generation_avg}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Cost</p>
                          <p className="font-bold text-blue-700">${asset.cost.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Best For</p>
                          <p className="font-bold text-gray-700">{asset.best_for.length} types</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Alternate Assets */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-600" />
              Alternate Asset Options
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {recommendations.alternate_assets.map((asset) => (
                <div key={asset.asset_id} className="bg-gray-50 rounded-lg p-3 border border-gray-300">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      asset.tier === 1 ? 'bg-yellow-100 text-yellow-800' :
                      asset.tier === 2 ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      Tier {asset.tier}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      asset.availability === 'available' ? 'bg-green-100 text-green-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {asset.availability}
                    </span>
                  </div>
                  <h4 className="font-bold text-sm text-gray-800 mb-1">{asset.name}</h4>
                  <p className="text-xs text-gray-600 mb-2">{asset.type}</p>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-600">Score: <strong>{asset.effectiveness_score}</strong></span>
                    <span className="text-gray-600">Cost: <strong>${(asset.cost / 1000).toFixed(0)}k</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetRecommendationEngine;
