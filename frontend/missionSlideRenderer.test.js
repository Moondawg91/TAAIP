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
  decision_summary: {
    recommended_action: 'decrease',
    mission_delta: -10,
    confidence_score: 0.66,
    loe_rag: 'red',
  },
  recommended_action: {
    type: 'decrease',
    magnitude: 'moderate',
    confidence: 0.66,
    rationale: 'Performance is below baseline with degraded LOE and constrained access.',
  },
  confidence: { score: 0.66, band: 'medium', completeness: 0.9, agreement: 0.3 },
  executive_summary: ['Mission dropped 50%', 'Top cause: execution stalls'],
  commander_narrative: 'Commander narrative text',
  causal_factors: [
    { factor_id: 'z', code: 'z', label: 'Z', weighted_score: 0.7, impact: -0.3, rationale: 'z reason' },
    { factor_id: 'a', code: 'a', label: 'A', weighted_score: 0.7, impact: -0.2, rationale: 'a reason' },
  ],
  recommendations: [{ title: 'Shift effort', action: 'Re-allocate effort by station', rationale: 'Focus high opportunity areas', linked_factors: ['school_access'], actions: ['Re-allocate blocks'] }],
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

  test('supports explicit action types increase/decrease/hold', () => {
    const increase = buildBriefingModel({ recommended_action: { type: 'increase' } });
    const decrease = buildBriefingModel({ recommended_action: { type: 'decrease' } });
    const hold = buildBriefingModel({ recommended_action: { type: 'hold' } });

    expect(increase.recommendedAction.type).toBe('increase');
    expect(decrease.recommendedAction.type).toBe('decrease');
    expect(hold.recommendedAction.type).toBe('hold');
  });
});

describe('renderMissionSlide', () => {
  test('renders required one-slide sections', () => {
    const container = document.createElement('div');
    renderMissionSlide(samplePayload, container);

    const text = container.textContent;
    expect(text).toContain('Current Mission Feasibility');
    expect(text).toContain('Recommended Action');
    expect(text).toContain('Recommended Mission Adjustment');
    expect(text).toContain('Executive Summary');
    expect(text).toContain('Commander Narrative');
    expect(text).toContain('Top Causal Factors');
    expect(text).toContain('Recommendations');
    expect(text).toContain('Accountability Brief + LOE Summary');
    expect(text).toContain('Assumptions and Limits');
    expect(text).toContain('Evidence');
  });

  test('renders action banner states for increase/decrease/hold', () => {
    const container = document.createElement('div');

    renderMissionSlide({ ...samplePayload, recommended_action: { type: 'increase' }, decision_summary: { ...samplePayload.decision_summary, recommended_action: 'increase' } }, container);
    expect(container.innerHTML).toContain('mdj-action-increase');

    renderMissionSlide({ ...samplePayload, recommended_action: { type: 'decrease' }, decision_summary: { ...samplePayload.decision_summary, recommended_action: 'decrease' } }, container);
    expect(container.innerHTML).toContain('mdj-action-decrease');

    renderMissionSlide({ ...samplePayload, recommended_action: { type: 'hold' }, decision_summary: { ...samplePayload.decision_summary, recommended_action: 'hold' } }, container);
    expect(container.innerHTML).toContain('mdj-action-hold');
  });

  test('falls back to delta-based action type when explicit recommended_action is missing', () => {
    const container = document.createElement('div');
    const payload = {
      ...samplePayload,
      recommended_action: {},
      decision_summary: {},
      mission_delta_summary: {
        ...samplePayload.mission_delta_summary,
        delta_pct: 0.12,
      },
    };

    renderMissionSlide(payload, container);
    expect(container.innerHTML).toContain('mdj-action-increase');
  });

  test('does not render null/system phrasing in narrative with valid payload', () => {
    const container = document.createElement('div');
    renderMissionSlide(samplePayload, container);
    const text = (container.textContent || '').toLowerCase();
    expect(text).not.toContain('null');
    expect(text).not.toContain('no rows available');
  });

  test('renders no data state when payload is missing', () => {
    const container = document.createElement('div');
    renderMissionSlide(null, container);
    expect(container.textContent).toContain('No data returned yet');
  });
});
