import { describe, expect, test } from 'vitest';

import { buildBriefingModel, renderMissionSlide } from './missionSlideRenderer.js';

const samplePayload = {
  request_id: 'mdj-123',
  traceability_id: 'trace-mdj-123',
  generated_at: '2026-04-12T12:00:00Z',
  mission_delta_summary: {
    current_period: { mission_total: 10 },
    baseline_period: { mission_total: 20 },
    delta: -10,
    delta_pct: -0.5,
  },
  confidence: { score: 0.66, band: 'medium', completeness: 0.9, agreement: 0.3 },
  executive_summary: ['Mission dropped 50%', 'Top cause: execution stalls'],
  commander_narrative: 'Commander narrative text',
  causal_factors: [
    { factor_id: 'z', code: 'z', label: 'Z', weighted_score: 0.7, impact: -0.3, rationale: 'z reason' },
    { factor_id: 'a', code: 'a', label: 'A', weighted_score: 0.7, impact: -0.2, rationale: 'a reason' },
  ],
  recommendations: [{ title: 'Shift effort', rationale: 'Focus high opportunity areas', actions: ['Re-allocate blocks'] }],
  accountability_brief: { classification: 'execution_failure', confidence: 'medium', overdue_items: ['Recovery plan'] },
  loe_summary: { rag: 'red', rationale: 'At risk concentration' },
  assumptions_and_limits: ['Signal completeness not 100%'],
  evidence: [{ evidence_id: 'ev-1', source: 'market_qma', timestamp: '2026-04-12T12:00:00Z' }],
};

describe('buildBriefingModel', () => {
  test('keeps deterministic causal factor ordering on tie by code', () => {
    const model = buildBriefingModel(samplePayload);
    expect(model.topCausalFactors[0].code).toBe('a');
    expect(model.topCausalFactors[1].code).toBe('z');
  });

  test('handles null payload fields safely', () => {
    const model = buildBriefingModel({
      confidence: null,
      causal_factors: null,
      recommendations: null,
      assumptions_and_limits: null,
      evidence: null,
    });

    expect(model.topCausalFactors).toEqual([]);
    expect(model.recommendations).toEqual([]);
    expect(model.assumptions).toEqual([]);
    expect(model.evidence).toEqual([]);
  });
});

describe('renderMissionSlide', () => {
  test('renders required one-slide sections', () => {
    const container = document.createElement('div');
    renderMissionSlide(samplePayload, container);

    const text = container.textContent;
    expect(text).toContain('Mission Delta + Confidence');
    expect(text).toContain('Executive Summary');
    expect(text).toContain('Commander Narrative');
    expect(text).toContain('Top Causal Factors');
    expect(text).toContain('Recommendations');
    expect(text).toContain('Accountability + LOE');
    expect(text).toContain('Assumptions, Limits, Traceability');
    expect(text).toContain('Evidence');
  });

  test('renders no data state when payload is missing', () => {
    const container = document.createElement('div');
    renderMissionSlide(null, container);
    expect(container.textContent).toContain('No data returned yet');
  });
});
