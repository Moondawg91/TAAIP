const EMPTY_TEXT = 'No data available';

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return EMPTY_TEXT;
  }
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return EMPTY_TEXT;
  }
  return Number(value).toLocaleString();
}

export function buildBriefingModel(payload) {
  const data = payload || {};
  const mission = data.mission_delta_summary || {};
  const confidence = data.confidence || {};
  const causalFactors = asArray(data.causal_factors);
  const recommendations = asArray(data.recommendations);
  const executiveSummary = asArray(data.executive_summary);
  const assumptions = asArray(data.assumptions_and_limits);
  const evidence = asArray(data.evidence);

  const topCausalFactors = causalFactors
    .slice()
    .sort((a, b) => {
      const aw = Number(a?.weighted_score || 0);
      const bw = Number(b?.weighted_score || 0);
      if (bw !== aw) {
        return bw - aw;
      }
      return String(a?.code || a?.factor_id || '').localeCompare(String(b?.code || b?.factor_id || ''));
    })
    .slice(0, 5);

  return {
    requestId: data.request_id || '',
    traceabilityId: data.traceability_id || '',
    generatedAt: data.generated_at || '',
    mission,
    confidence,
    executiveSummary,
    commanderNarrative: data.commander_narrative || '',
    topCausalFactors,
    recommendations,
    accountabilityBrief: data.accountability_brief || {},
    loeSummary: data.loe_summary || {},
    assumptions,
    evidence,
    isPartialSignals:
      Number(confidence.completeness || 0) < 1 ||
      evidence.some((e) => String(e?.fields?.message || '').toLowerCase().includes('no targeting recommendations')),
  };
}

function renderList(items, itemRenderer, emptyMessage = EMPTY_TEXT) {
  if (!items.length) {
    return `<li class="mdj-empty">${escapeHtml(emptyMessage)}</li>`;
  }
  return items.map(itemRenderer).join('');
}

export function renderMissionSlide(payload, container) {
  if (!container) {
    return;
  }
  if (!payload || typeof payload !== 'object') {
    container.innerHTML = '<div class="mdj-empty-state">No data returned yet. Submit a request to generate a briefing slide.</div>';
    return;
  }

  const model = buildBriefingModel(payload);

  const currentPeriod = model.mission.current_period || {};
  const baselinePeriod = model.mission.baseline_period || {};

  container.innerHTML = `
    <section class="mdj-slide" aria-label="Mission decrease decision slide">
      <header class="mdj-header">
        <h1>Mission Decrease Justification</h1>
        <div class="mdj-trace">Request: ${escapeHtml(model.requestId || EMPTY_TEXT)} | Trace: ${escapeHtml(model.traceabilityId || EMPTY_TEXT)}</div>
      </header>

      ${model.isPartialSignals ? '<div class="mdj-warning">Partial signals detected. Review evidence and assumptions before final command decision.</div>' : ''}

      <div class="mdj-grid">
        <article class="mdj-panel mdj-top-left">
          <h2>Mission Delta + Confidence</h2>
          <p><strong>Current Total:</strong> ${escapeHtml(formatNumber(currentPeriod.mission_total))}</p>
          <p><strong>Baseline Total:</strong> ${escapeHtml(formatNumber(baselinePeriod.mission_total))}</p>
          <p><strong>Delta:</strong> ${escapeHtml(formatNumber(model.mission.delta))}</p>
          <p><strong>Delta %:</strong> ${escapeHtml(formatPercent(model.mission.delta_pct))}</p>
          <p><strong>Confidence Score:</strong> ${escapeHtml(formatNumber(model.confidence.score))}</p>
          <p><strong>Confidence Band:</strong> ${escapeHtml(model.confidence.band || EMPTY_TEXT)}</p>
          <p><strong>Completeness:</strong> ${escapeHtml(formatPercent(model.confidence.completeness))}</p>
        </article>

        <article class="mdj-panel mdj-top-right">
          <h2>Executive Summary</h2>
          <ul>
            ${renderList(model.executiveSummary, (line) => `<li>${escapeHtml(line)}</li>`, 'No executive summary provided')}
          </ul>
          <h3>Commander Narrative</h3>
          <p>${escapeHtml(model.commanderNarrative || EMPTY_TEXT)}</p>
        </article>

        <article class="mdj-panel mdj-middle-left">
          <h2>Top Causal Factors</h2>
          <ul>
            ${renderList(
              model.topCausalFactors,
              (factor) => `<li><strong>${escapeHtml(factor.label || factor.code || factor.factor_id || 'factor')}</strong> | impact: ${escapeHtml(formatNumber(factor.impact))} | weighted: ${escapeHtml(formatNumber(factor.weighted_score))}<br/>${escapeHtml(factor.rationale || '')}</li>`,
              'No causal factors provided'
            )}
          </ul>
        </article>

        <article class="mdj-panel mdj-middle-right">
          <h2>Recommendations</h2>
          <ul>
            ${renderList(
              model.recommendations,
              (rec) => `<li><strong>${escapeHtml(rec.title || rec.kind || 'recommendation')}</strong><br/>${escapeHtml(rec.rationale || '')}<br/><em>Actions:</em> ${escapeHtml(asArray(rec.actions).join('; ') || EMPTY_TEXT)}</li>`,
              'No recommendations provided'
            )}
          </ul>
        </article>

        <article class="mdj-panel mdj-bottom-left">
          <h2>Accountability + LOE</h2>
          <p><strong>Classification:</strong> ${escapeHtml(model.accountabilityBrief.classification || EMPTY_TEXT)}</p>
          <p><strong>Accountability Confidence:</strong> ${escapeHtml(model.accountabilityBrief.confidence || EMPTY_TEXT)}</p>
          <p><strong>Overdue Items:</strong> ${escapeHtml(asArray(model.accountabilityBrief.overdue_items).join('; ') || EMPTY_TEXT)}</p>
          <p><strong>LOE RAG:</strong> ${escapeHtml(model.loeSummary.rag || EMPTY_TEXT)}</p>
          <p><strong>LOE Rationale:</strong> ${escapeHtml(model.loeSummary.rationale || EMPTY_TEXT)}</p>
        </article>

        <article class="mdj-panel mdj-bottom-right">
          <h2>Assumptions, Limits, Traceability</h2>
          <ul>
            ${renderList(model.assumptions, (line) => `<li>${escapeHtml(line)}</li>`, 'No assumptions provided')}
          </ul>
          <p><strong>Generated At:</strong> ${escapeHtml(model.generatedAt || EMPTY_TEXT)}</p>
          <p><strong>Traceability:</strong> ${escapeHtml(model.traceabilityId || EMPTY_TEXT)}</p>
        </article>
      </div>

      <section class="mdj-panel mdj-evidence">
        <h2>Evidence</h2>
        <ul>
          ${renderList(
            model.evidence,
            (ev) => `<li><strong>${escapeHtml(ev.evidence_id || 'evidence')}</strong> | source: ${escapeHtml(ev.source || EMPTY_TEXT)} | ts: ${escapeHtml(ev.timestamp || EMPTY_TEXT)}</li>`,
            'No evidence provided'
          )}
        </ul>
      </section>
    </section>
  `;
}
