import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, Eye, MousePointer, Share2, Heart, MessageCircle, 
  Mail, Target, DollarSign, Users, BarChart3, PieChart, Filter,
  Calendar, Download, RefreshCw, ExternalLink, Instagram, Facebook,
  Linkedin, Youtube, Twitter, Video
} from 'lucide-react';
import { BarChart, Bar, LineChart, Line, PieChart as RePieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

interface MarketingOverview {
  total_campaigns: number;
  active_campaigns: number;
  total_impressions: number;
  total_views: number;
  total_engagements: number;
  total_clicks: number;
  total_conversions: number;
  avg_engagement_rate: number;
  avg_ctr: number;
  avg_conversion_rate: number;
  top_platforms: Array<{
    platform: string;
    total_engagements: number;
    total_impressions: number;
    avg_engagement_rate: number;
  }>;
  social_performance: Array<{
    platform: string;
    post_count: number;
    total_engagements: number;
    total_impressions: number;
  }>;
  period_days: number;
}

interface Campaign {
  id: number;
  campaign_id: string;
  campaign_name: string;
  campaign_type: string;
  platform: string;
  start_date: string;
  end_date: string;
  status: string;
  target_audience: string;
  budget_allocated: number;
  budget_spent: number;
  objective: string;
}

interface EngagementMetric {
  id: number;
  campaign_id: string;
  platform: string;
  metric_date: string;
  impressions: number;
  views: number;
  reach: number;
  engagements: number;
  clicks: number;
  shares: number;
  likes: number;
  comments: number;
  saves: number;
  video_views: number;
  video_completion_rate: number;
  click_through_rate: number;
  engagement_rate: number;
  cost_per_impression: number;
  cost_per_click: number;
  cost_per_engagement: number;
  conversions: number;
  conversion_rate: number;
}

interface SocialPost {
  id: number;
  post_id: string;
  campaign_id: string | null;
  platform: string;
  post_type: string;
  content: string;
  posted_date: string;
  impressions: number;
  views: number;
  engagements: number;
  clicks: number;
  shares: number;
  likes: number;
  comments: number;
  saves: number;
  reach: number;
  engagement_rate: number;
}

interface Platform {
  id: number;
  platform_name: string;
  platform_type: string;
  api_endpoint: string;
  last_sync_date: string | null;
  sync_status: string;
  sync_frequency: string;
  is_active: number;
}

export const MarketingEngagementDashboard: React.FC = () => {
  const [overview, setOverview] = useState<MarketingOverview | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [metrics, setMetrics] = useState<EngagementMetric[]>([]);
  const [socialPosts, setSocialPosts] = useState<SocialPost[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'overview' | 'campaigns' | 'social' | 'email' | 'ads'>('overview');

  useEffect(() => {
    loadData();
  }, [timeRange, selectedPlatform]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [overviewRes, campaignsRes, metricsRes, socialRes, platformsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/marketing/overview?days=${timeRange}`),
        fetch(`${API_BASE}/api/v2/marketing/campaigns${selectedPlatform !== 'all' ? `?platform=${selectedPlatform}` : ''}`),
        fetch(`${API_BASE}/api/v2/marketing/engagement-metrics?limit=100${selectedPlatform !== 'all' ? `&platform=${selectedPlatform}` : ''}`),
        fetch(`${API_BASE}/api/v2/marketing/social-media-posts?limit=50${selectedPlatform !== 'all' ? `&platform=${selectedPlatform}` : ''}`),
        fetch(`${API_BASE}/api/v2/marketing/platforms`)
      ]);

      const overviewData = await overviewRes.json();
      const campaignsData = await campaignsRes.json();
      const metricsData = await metricsRes.json();
      const socialData = await socialRes.json();
      const platformsData = await platformsRes.json();

      if (overviewData.status === 'ok') setOverview(overviewData.overview);
      if (campaignsData.status === 'ok') setCampaigns(campaignsData.campaigns);
      if (metricsData.status === 'ok') setMetrics(metricsData.metrics);
      if (socialData.status === 'ok') setSocialPosts(socialData.posts);
      if (platformsData.status === 'ok') setPlatforms(platformsData.platforms);
    } catch (error) {
      console.error('Error loading marketing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const getPlatformIcon = (platform: string) => {
    const platformLower = platform.toLowerCase();
    if (platformLower.includes('facebook')) return <Facebook className="w-5 h-5" />;
    if (platformLower.includes('instagram')) return <Instagram className="w-5 h-5" />;
    if (platformLower.includes('linkedin')) return <Linkedin className="w-5 h-5" />;
    if (platformLower.includes('youtube')) return <Youtube className="w-5 h-5" />;
    if (platformLower.includes('twitter') || platformLower.includes('x')) return <Twitter className="w-5 h-5" />;
    if (platformLower.includes('tiktok')) return <Video className="w-5 h-5" />;
    return <Target className="w-5 h-5" />;
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658', '#ff7c7c'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <TrendingUp className="w-8 h-8 text-blue-600" />
            Marketing Engagement Performance
          </h1>
          <p className="text-gray-600 mt-1">
            Multi-platform marketing analytics from Vantage, Sprinkler, EMM, MACs, and social media
          </p>
        </div>
        <div className="flex gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={60}>Last 60 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
          <select
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Platforms</option>
            <option value="Facebook">Facebook</option>
            <option value="Instagram">Instagram</option>
            <option value="LinkedIn">LinkedIn</option>
            <option value="YouTube">YouTube</option>
            <option value="TikTok">TikTok</option>
            <option value="Vantage">Vantage</option>
            <option value="MACs">MACs</option>
            <option value="Sprinkler">Sprinkler</option>
          </select>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {(['overview', 'campaigns', 'social', 'email', 'ads'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 font-medium capitalize transition-colors ${
              activeTab === tab
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && overview && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <Eye className="w-8 h-8 text-blue-600" />
                <span className="text-sm font-medium text-blue-700">Impressions</span>
              </div>
              <div className="text-3xl font-bold text-blue-900">{formatNumber(overview.total_impressions)}</div>
              <div className="text-sm text-blue-600 mt-1">Total reach across all platforms</div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <Heart className="w-8 h-8 text-green-600" />
                <span className="text-sm font-medium text-green-700">Engagements</span>
              </div>
              <div className="text-3xl font-bold text-green-900">{formatNumber(overview.total_engagements)}</div>
              <div className="text-sm text-green-600 mt-1">
                {overview.avg_engagement_rate.toFixed(2)}% engagement rate
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <MousePointer className="w-8 h-8 text-purple-600" />
                <span className="text-sm font-medium text-purple-700">Clicks</span>
              </div>
              <div className="text-3xl font-bold text-purple-900">{formatNumber(overview.total_clicks)}</div>
              <div className="text-sm text-purple-600 mt-1">{overview.avg_ctr.toFixed(2)}% CTR</div>
            </div>

            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-6 border border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <Target className="w-8 h-8 text-orange-600" />
                <span className="text-sm font-medium text-orange-700">Conversions</span>
              </div>
              <div className="text-3xl font-bold text-orange-900">{formatNumber(overview.total_conversions)}</div>
              <div className="text-sm text-orange-600 mt-1">
                {overview.avg_conversion_rate.toFixed(2)}% conversion rate
              </div>
            </div>
          </div>

          {/* Additional Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <Users className="w-6 h-6 text-indigo-600" />
                <h3 className="text-lg font-semibold text-gray-900">Views (Awareness)</h3>
              </div>
              <div className="text-4xl font-bold text-indigo-900">{formatNumber(overview.total_views)}</div>
              <p className="text-sm text-gray-600 mt-2">Content views and video plays</p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <BarChart3 className="w-6 h-6 text-cyan-600" />
                <h3 className="text-lg font-semibold text-gray-900">Active Campaigns</h3>
              </div>
              <div className="text-4xl font-bold text-cyan-900">
                {overview.active_campaigns} / {overview.total_campaigns}
              </div>
              <p className="text-sm text-gray-600 mt-2">Currently running campaigns</p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <Calendar className="w-6 h-6 text-pink-600" />
                <h3 className="text-lg font-semibold text-gray-900">Period</h3>
              </div>
              <div className="text-4xl font-bold text-pink-900">{overview.period_days} Days</div>
              <p className="text-sm text-gray-600 mt-2">Data reporting period</p>
            </div>
          </div>

          {/* Top Performing Platforms */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <PieChart className="w-6 h-6 text-blue-600" />
                Top Performing Platforms
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <RePieChart>
                  <Pie
                    data={overview.top_platforms}
                    dataKey="total_engagements"
                    nameKey="platform"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={(entry) => `${entry.platform}: ${formatNumber(entry.total_engagements)}`}
                  >
                    {overview.top_platforms.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </RePieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Share2 className="w-6 h-6 text-green-600" />
                Social Media Performance
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={overview.social_performance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="platform" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="total_engagements" fill="#10b981" name="Engagements" />
                  <Bar dataKey="post_count" fill="#3b82f6" name="Posts" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Platform Integrations Status */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <ExternalLink className="w-6 h-6 text-purple-600" />
              Platform Integration Status
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {platforms.map((platform) => (
                <div
                  key={platform.id}
                  className={`p-4 rounded-lg border-2 ${
                    platform.is_active
                      ? 'border-green-200 bg-green-50'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getPlatformIcon(platform.platform_name)}
                      <span className="font-semibold text-gray-900">{platform.platform_name}</span>
                    </div>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        platform.sync_status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {platform.sync_status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600">{platform.platform_type}</p>
                  <p className="text-xs text-gray-500 mt-1">Sync: {platform.sync_frequency}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Campaigns Tab */}
      {activeTab === 'campaigns' && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Active Campaigns</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Campaign</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Platform</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Type</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Start Date</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Budget</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Spent</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Objective</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((campaign) => (
                    <tr key={campaign.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div>
                          <div className="font-medium text-gray-900">{campaign.campaign_name}</div>
                          <div className="text-xs text-gray-500">{campaign.campaign_id}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {getPlatformIcon(campaign.platform)}
                          <span>{campaign.platform}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-sm text-gray-700">{campaign.campaign_type}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            campaign.status === 'active'
                              ? 'bg-green-100 text-green-700'
                              : campaign.status === 'completed'
                              ? 'bg-gray-100 text-gray-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {campaign.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">{campaign.start_date}</td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        ${campaign.budget_allocated.toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            ${campaign.budget_spent.toLocaleString()}
                          </div>
                          <div className="text-xs text-gray-500">
                            {((campaign.budget_spent / campaign.budget_allocated) * 100).toFixed(1)}%
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">{campaign.objective}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Social Media Tab */}
      {activeTab === 'social' && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Recent Social Media Posts</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {socialPosts.slice(0, 12).map((post) => (
                <div key={post.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getPlatformIcon(post.platform)}
                      <span className="font-semibold text-gray-900">{post.platform}</span>
                    </div>
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                      {post.post_type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mb-3 line-clamp-2">{post.content}</p>
                  <div className="grid grid-cols-3 gap-2 text-xs text-gray-600 mb-2">
                    <div className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {formatNumber(post.views)}
                    </div>
                    <div className="flex items-center gap-1">
                      <Heart className="w-3 h-3" />
                      {formatNumber(post.likes)}
                    </div>
                    <div className="flex items-center gap-1">
                      <Share2 className="w-3 h-3" />
                      {formatNumber(post.shares)}
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                    <span className="text-xs text-gray-500">{post.posted_date.split(' ')[0]}</span>
                    <span className="text-xs font-medium text-green-600">
                      {post.engagement_rate.toFixed(2)}% eng.
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Email and Ads tabs would be similar structures */}
      {(activeTab === 'email' || activeTab === 'ads') && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="text-center py-12">
            <Mail className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {activeTab === 'email' ? 'Email Marketing' : 'Digital Advertising'} Metrics
            </h3>
            <p className="text-gray-600">
              Detailed {activeTab === 'email' ? 'email campaign' : 'digital ad'} metrics from{' '}
              {activeTab === 'email' ? 'MACs and Sprinkler' : 'Vantage and display networks'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketingEngagementDashboard;
