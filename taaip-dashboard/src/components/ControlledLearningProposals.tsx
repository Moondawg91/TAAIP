import React, { useEffect, useState } from 'react';
import { API_BASE } from '../config/api';

interface Proposal {
  proposal_id: string;
  title: string;
  description?: string;
  state?: string;
  created_at?: string;
}

export default function ControlledLearningProposals() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProposals = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v2/admin/controlled-learning/proposals`);
        const data = await response.json();
        setProposals((data && data.proposals) || []);
      } catch (err) {
        console.error('Error fetching proposals:', err);
        setError('Failed to load proposals');
      } finally {
        setLoading(false);
      }
    };
    
    fetchProposals();
  }, []);

  return (
    <div style={{ padding: 20, maxWidth: 1000, margin: '0 auto' }}>
      <h2 style={{ fontSize: 20, marginBottom: 12, color: '#111827' }}>Controlled Learning Proposals</h2>
      
      {loading && <div style={{ color: '#6b7280' }}>Loading proposals...</div>}
      {error && <div style={{ color: '#b91c1c' }}>Error: {error}</div>}
      
      {!loading && !error && proposals.length === 0 && (
        <div style={{ color: '#6b7280' }}>No proposals available at this time.</div>
      )}
      
      {!loading && !error && proposals.length > 0 && (
        <div style={{ display: 'grid', gap: 12 }}>
          {proposals.map((proposal) => (
            <div
              key={proposal.proposal_id}
              style={{
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div style={{ fontSize: 14, fontWeight: 600, color: '#111827', marginBottom: 4 }}>
                {proposal.title}
              </div>
              {proposal.description && (
                <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 8 }}>
                  {proposal.description}
                </div>
              )}
              <div style={{ fontSize: 12, color: '#9ca3af' }}>
                ID: {proposal.proposal_id}
                {proposal.state && ` • State: ${proposal.state}`}
                {proposal.created_at && ` • Created: ${new Date(proposal.created_at).toLocaleDateString()}`}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
