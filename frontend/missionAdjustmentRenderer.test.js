import { describe, it, expect } from 'vitest';
import { buildBriefingModel, renderMissionAdjustment } from './missionAdjustmentRenderer.js';

describe('missionAdjustmentRenderer', () => {
  describe('buildBriefingModel', () => {
    it('determines decrease recommendation when delta_pct is negative', () => {
      const payload = {
        mission_delta_summary: {
          delta: -50,
          delta_pct: -0.15,
          current_period: { mission_total: 850, sample_count: 100 },
          baseline_period: { mission_total: 1000, sample_count: 100 },
        },
        confidence: { score: 0.75, band: 'high', completeness: 0.9, agreement: 0.8 },
        causal_factors: [
          { factor_id: 'f1', code: 'loe_health', label: 'LOE Health', weighted_score: 0.8, impact: 0.3, rationale: 'Test' },
          { factor_id: 'f2', code: 'market_cap', label: 'Market Cap', weighted_score: 0.6, impact: -0.2, rationale: 'Test' },
        ],
      };

      const model = buildBriefingModel(payload);
      expect(model.adjustmentType).toBe('decrease');
      expect(model.adjustmentLabel.label).toBe('DECREASE mission output');
      expect(model.adjustmentLabel.class).toBe('maj-decrease');
    });

    it('determines increase recommendation when delta_pct is positive', () => {
      const payload = {
        mission_delta_summary: {
          delta: 75,
          delta_pct: 0.10,
          current_period: { mission_total: 1100, sample_count: 100 },
          baseline_period: { mission_total: 1000, sample_count: 100 },
        },
        confidence: { score: 0.80, band: 'high', completeness: 0.95, agreement: 0.85 },
        causal_factors: [
          { factor_id: 'f1', code: 'execution', label: 'Execution Quality', weighted_score: 0.85, impact: 0.4, rationale: 'Strong' },
        ],
      };

      const model = buildBriefingModel(payload);
      expect(model.adjustmentType).toBe('increase');
      expect(model.adjustmentLabel.label).toBe('INCREASE mission output');
      expect(model.adjustmentLabel.class).toBe('maj-increase');
    });

    it('determines hold recommendation when delta_pct is within threshold', () => {
      const payload = {
        mission_delta_summary: {
          delta: 5,
          delta_pct: 0.005,
          current_period: { mission_total: 1005, sample_count: 100 },
          baseline_period: { mission_total: 1000, sample_count: 100 },
        },
        confidence: { score: 0.55, band: 'medium', completeness: 0.7, agreement: 0.65 },
        causal_factors: [],
      };

      const model = buildBriefingModel(payload);
      expect(model.adjustmentType).toBe('hold');
      expect(model.adjustmentLabel.label).toBe('HOLD mission output at current level');
      expect(model.adjustmentLabel.class).toBe('maj-hold');
    });

    it('handles null/missing payload fields gracefully', () => {
      const payload = {
        mission_delta_summary: { delta_pct: -0.08 },
        confidence: {},
        causal_factors: null,
      };

      const model = buildBriefingModel(payload);
      expect(model.adjustmentType).toBe('decrease');
      expect(Array.isArray(model.topCausalFactors)).toBe(true);
      expect(model.topCausalFactors.length).toBe(0);
      expect(Array.isArray(model.recommendations)).toBe(true);
      expect(model.recommendations.length).toBe(0);
    });

    it('maintains deterministic causal factor ordering by weighted_score desc then code asc', () => {
      const payload = {
        mission_delta_summary: { delta_pct: 0 },
        confidence: {},
        causal_factors: [
          { code: 'z_factor', weighted_score: 0.5, rationale: 'test' },
          { code: 'a_factor', weighted_score: 0.5, rationale: 'test' },
          { code: 'b_factor', weighted_score: 0.8, rationale: 'test' },
        ],
      };

      const model = buildBriefingModel(payload);
      expect(model.topCausalFactors[0].code).toBe('b_factor');
      expect(model.topCausalFactors[1].code).toBe('a_factor');
      expect(model.topCausalFactors[2].code).toBe('z_factor');
    });
  });

  describe('renderMissionAdjustment', () => {
    it('renders all required sections for decrease scenario', () => {
      const payload = {
        request_id: 'maj-123',
        traceability_id: 'trace-456',
        generated_at: '2026-04-13T00:00:00Z',
        mission_delta_summary: {
          delta: -40,
          delta_pct: -0.12,
          current_period: { mission_total: 880 },
          baseline_period: { mission_total: 1000 },
        },
        confidence: { score: 0.7, band: 'high', completeness: 0.85 },
        causal_factors: [],
        executive_summary: ['Test summary'],
        commander_narrative: 'Test narrative',
        recommendations: [],
        accountability_brief: {},
        loe_summary: {},
        assumptions_and_limits: [],
        evidence: [],
      };

      const container = document.createElement('section');
      renderMissionAdjustment(payload, container);

      expect(container.innerHTML).toContain('Mission Adjustment Justification');
      expect(container.innerHTML).toContain('DECREASE mission output');
      expect(container.innerHTML).toContain('maj-decrease');
      expect(container.innerHTML).toContain('Recommended Action');
      expect(container.innerHTML).toContain('Mission Delta + Confidence');
      expect(container.innerHTML).toContain('Executive Summary');
      expect(container.innerHTML).toContain('Top Causal Factors');
      expect(container.innerHTML).toContain('Recommendations');
      expect(container.innerHTML).toContain('Accountability + LOE');
      expect(container.innerHTML).toContain('Assumptions, Limits, Traceability');
    });

    it('renders all required sections for increase scenario', () => {
      const payload = {
        request_id: 'maj-789',
        traceability_id: 'trace-999',
        generated_at: '2026-04-13T12:00:00Z',
        mission_delta_summary: {
          delta: 120,
          delta_pct: 0.15,
          current_period: { mission_total: 1120 },
          baseline_period: { mission_total: 1000 },
        },
        confidence: { score: 0.82, band: 'high', completeness: 0.9 },
        causal_factors: [],
        executive_summary: [],
        commander_narrative: '',
        recommendations: [],
        accountability_brief: {},
        loe_summary: {},
        assumptions_and_limits: [],
        evidence: [],
      };

      const container = document.createElement('section');
      renderMissionAdjustment(payload, container);

      expect(container.innerHTML).toContain('INCREASE mission output');
      expect(container.innerHTML).toContain('maj-increase');
    });

    it('renders all required sections for hold scenario', () => {
      const payload = {
        request_id: 'maj-hold',
        traceability_id: 'trace-hold',
        generated_at: '2026-04-13T12:00:00Z',
        mission_delta_summary: {
          delta: 0,
          delta_pct: 0.001,
          current_period: { mission_total: 1000 },
          baseline_period: { mission_total: 999 },
        },
        confidence: { score: 0.5, band: 'medium', completeness: 0.6 },
        causal_factors: [],
        executive_summary: [],
        commander_narrative: '',
        recommendations: [],
        accountability_brief: {},
        loe_summary: {},
        assumptions_and_limits: [],
        evidence: [],
      };

      const container = document.createElement('section');
      renderMissionAdjustment(payload, container);

      expect(container.innerHTML).toContain('HOLD mission output at current level');
      expect(container.innerHTML).toContain('maj-hold');
    });

    it('renders no-data state when payload is null or undefined', () => {
      const container = document.createElement('section');
      renderMissionAdjustment(null, container);

      expect(container.innerHTML).toContain('No data returned yet');
      expect(container.innerHTML).toContain('maj-empty-state');
    });

    it('renders empty container gracefully', () => {
      const container = document.createElement('section');
      const result = renderMissionAdjustment({}, container);

      expect(result).toBeUndefined();
      expect(container.innerHTML.length).toBeGreaterThan(0);
    });
  });
});
