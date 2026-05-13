import React, { useEffect, useState } from 'react';
import { API_BASE } from '../config/api';

interface Recommendation {
  source: string;
  title: string;
  description?: string;
  confidence?: number;
}

export default function AIRecommendations() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v2/ai-lms/recommendations/mission/latest`);
        const data = await response.json();
        setRecommendations((data && data.recommendations) || []);
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError('Failed to load recommendations');
      } finally {
        setLoading(false);
      }
    };
    
    fetchRecommendations();
  }, []);

  return (
    <div style={{ padding: 20, maxWidth: 1000, margin: '0 auto' }}>
      <h2 style={{ fontSize: 20, marginBottom: 12, color: '#111827' }}>AI Recommendations</h2>
      
      {loading && <div style={{ color: '#6b7280' }}>Loading recommendations...</div>}
      {error && <div style={{ color: '#b91c1c' }}>Error: {error}</div>}
      
      {!loading && !error && recommendations.length === 0 && (
        <div style={{ color: '#6b7280' }}>No recommendations available at this time.</div>
      )}
      
      {!loading && !error && recommendations.length > 0 && (
        <div style={{ display: 'grid', gap: 12 }}>
          {recommendations.map((rec, idx) => (
            <div
              key={idx}
              style={{
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div style={{ fontSize: 14, fontWeight: 600, color: '#111827', marginBottom: 4 }}>
                {rec.title}
              </div>
              {rec.description && (
                <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 8 }}>
                  {rec.description}
                </div>
              )}
              <div style={{ fontSize: 12, color: '#9ca3af' }}>
                Source: {rec.source}
                {rec.confidence && ` • Confidence: ${(rec.confidence * 100).toFixed(0)}%`}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
