import React, { useEffect, useState } from 'react'

export default function CommandCenter() {
  const [marketHealth, setMarketHealth] = useState(null)
  const [missionRisk, setMissionRisk] = useState(null)
  const [targeting, setTargeting] = useState([])
  const [allocation, setAllocation] = useState([])
  const [loading, setLoading] = useState(true)
  const [asOf, setAsOf] = useState('today')
  const [customDate, setCustomDate] = useState('')
  const [unitRsid, setUnitRsid] = useState('')
  const [marketFilter, setMarketFilter] = useState('all')
  const [units, setUnits] = useState([])
  const [markets, setMarkets] = useState([])
  const [showHierarchy, setShowHierarchy] = useState(false)
  const [hierarchy, setHierarchy] = useState(null)
  const [loadingHierarchy, setLoadingHierarchy] = useState(false)
  const [briefing, setBriefing] = useState(null)
  const [loadingBriefing, setLoadingBriefing] = useState(false)
  // Mission allocation decision state
  const [runId, setRunId] = useState(null)
  const [recommendedTotal, setRecommendedTotal] = useState(null)
  const [approvedAllocation, setApprovedAllocation] = useState('')
  const [decisionStatus, setDecisionStatus] = useState('recommended')
  const [decisionNotes, setDecisionNotes] = useState('')
  const [approvedBy, setApprovedBy] = useState('')
  const [savingDecision, setSavingDecision] = useState(false)
  const [decisionLoaded, setDecisionLoaded] = useState(false)
  const [approvedAt, setApprovedAt] = useState(null)
  const [decisionExists, setDecisionExists] = useState(false)
  const [decisionError, setDecisionError] = useState(null)
  const [decisionSuccess, setDecisionSuccess] = useState(null)

  useEffect(() => {
    const buildParams = () => {
      const params = new URLSearchParams()
      // asOf options: 'today', 'yesterday', 'last_7', 'custom'
      let as_of_date = ''
      const today = new Date()
      const yday = new Date(Date.now() - 24 * 3600 * 1000)
      if (asOf === 'today') as_of_date = today.toISOString().slice(0, 10)
      else if (asOf === 'yesterday') as_of_date = yday.toISOString().slice(0, 10)
      else if (asOf === 'last_7') as_of_date = 'last_7'
      else if (asOf === 'custom' && customDate) as_of_date = customDate
      if (as_of_date) params.set('as_of_date', as_of_date)
      if (unitRsid) params.set('unit_rsid', unitRsid)
      if (marketFilter && marketFilter !== 'all') params.set('market', marketFilter)
      return params.toString() ? `?${params.toString()}` : ''
    }

    setLoading(true)
    const q = buildParams()
    Promise.all([
      fetch(`/api/v2/market-health/latest${q}`).then(r => r.json()).catch(() => null),
      fetch(`/api/v2/mission-risk/latest${q}`).then(r => r.json()).catch(() => null),
      fetch(`/api/v2/targeting/schools${q}`).then(r => r.json()).catch(() => ({ results: [] })),
      fetch(`/api/v2/mission-allocation/latest${q}`).then(r => r.json()).catch(() => ({ results: [] })),
    ]).then(([mh, mr, st, ma]) => {
      setMarketHealth(mh?.results || mh || null)
      setMissionRisk(mr?.results || mr || null)
      // targeting endpoint returns { schools: [...] }
      setTargeting(st?.schools || st?.results || [])
      setAllocation(ma?.results || ma || [])
      setLoading(false)
    })
  }, [asOf, customDate, unitRsid, marketFilter])

  // persist simple filter selections to localStorage for session persistence
  useEffect(() => {
    try {
      const f = { asOf, customDate, unitRsid, marketFilter }
      localStorage.setItem('command_center_filters_v1', JSON.stringify(f))
    } catch (e) {}
  }, [asOf, customDate, unitRsid, marketFilter])

  // restore filters on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('command_center_filters_v1')
      if (raw) {
        const f = JSON.parse(raw)
        if (f) {
          if (f.asOf) setAsOf(f.asOf)
          if (f.customDate) setCustomDate(f.customDate)
          if (f.unitRsid) setUnitRsid(f.unitRsid)
          if (f.marketFilter) setMarketFilter(f.marketFilter)
        }
      }
    } catch (e) {}
  }, [])


  // When unit changes or allocation data updates, locate latest run and load decision state
  useEffect(() => {
    if (!unitRsid) return
    setDecisionLoaded(false)
    // list runs for unit -> pick latest
    fetch(`/api/v2/mission-allocation/runs?unit_rsid=${encodeURIComponent(unitRsid)}`)
      .then(r => r.json())
      .then(j => {
        const rows = j?.rows || []
        if (!rows.length) {
          setRunId(null)
          setDecisionLoaded(true)
          return
        }
        const rid = rows[0].run_id || rows[0].runId || rows[0].run
        setRunId(rid)

        // load existing decision state
        fetch(`/api/v2/mission-allocation/runs/${encodeURIComponent(rid)}/decision`)
          .then(r => r.json())
          .then(d => {
            if (d && d.status === 'ok') {
              setApprovedAllocation(d.approved_allocation ?? '')
              setDecisionStatus(d.decision_status ?? 'recommended')
              setDecisionNotes(d.decision_notes ?? '')
              setApprovedBy(d.approved_by ?? '')
              setApprovedAt(d.approved_at ?? null)
              setDecisionExists(Boolean(d.decision_status || d.approved_allocation || d.decision_notes || d.approved_by || d.approved_at))
              setDecisionError(null)
            } else {
              setApprovedAllocation('')
              setDecisionStatus('recommended')
              setDecisionNotes('')
              setApprovedBy('')
              setApprovedAt(null)
              setDecisionExists(false)
            }
          }).catch(() => {
            setDecisionError('Failed to load decision state')
          })
          .finally(() => setDecisionLoaded(true))

        // load results to compute recommended total
        fetch(`/api/v2/mission-allocation/runs/${encodeURIComponent(rid)}/results`)
          .then(r => r.json())
          .then(res => {
            const recs = res?.recommendations || []
            const sum = recs.reduce((s, c) => s + (Number(c.recommended_allocation) || 0), 0)
            setRecommendedTotal(sum)
          }).catch(() => setRecommendedTotal(null))
      }).catch(() => setDecisionLoaded(true))
  }, [unitRsid, allocation])

  // Fetch available units and markets for dropdowns
  useEffect(() => {
    // units: /api/v2/org/roots -> { status, roots: [{ rsid, display_name, ... }] }
    fetch('/api/v2/org/roots')
      .then(r => r.json())
      .then(j => {
        const roots = j?.roots || []
        setUnits(roots)
        // set default unit if none selected
        if (!unitRsid && roots && roots.length) setUnitRsid(roots[0].rsid)
      })
      .catch(() => setUnits([]))

    // markets: /api/ops/market/cbsa -> { status, rows: [{ cbsa_code, cbsa_name }] }
    fetch('/api/ops/market/cbsa')
      .then(r => r.json())
      .then(j => {
        const rows = j?.rows || []
        setMarkets(rows)
      })
      .catch(() => setMarkets([]))
  }, [])

  useEffect(() => {
    if (!showHierarchy) return
    if (!unitRsid) return
    setLoadingHierarchy(true)
    fetch(`/api/v2/org/tree?unit_rsid=${encodeURIComponent(unitRsid)}&depth=2`)
      .then(r => r.json())
      .then(j => {
        setHierarchy(j?.tree || null)
      })
      .catch(() => setHierarchy(null))
      .finally(() => setLoadingHierarchy(false))
  }, [showHierarchy, unitRsid])

  const mrLevel = (score) => {
    if (score == null) return 'No data'
    if (score >= 75) return 'Low'
    if (score >= 40) return 'Monitor'
    return 'High'
  }

  const mhLevel = (score) => {
    if (score == null) return 'No data'
    // higher market health is better
    if (score >= 75) return 'Healthy'
    if (score >= 40) return 'Watch'
    return 'At Risk'
  }

  const allocLevel = (count) => {
    if (!count) return 'Low'
    if (count <= 10) return 'Monitor'
    return 'High'
  }

  const loadBriefing = () => {
    setLoadingBriefing(true)
    const buildParams = () => {
      const params = new URLSearchParams()
      if (unitRsid) params.set('unit_rsid', unitRsid)
      let as_of_date = ''
      if (asOf === 'custom' && customDate) as_of_date = customDate
      else if (asOf === 'today') as_of_date = (new Date()).toISOString().slice(0,10)
      else if (asOf === 'yesterday') as_of_date = (new Date(Date.now()-24*3600*1000)).toISOString().slice(0,10)
      if (as_of_date) params.set('as_of_date', as_of_date)
      return params.toString() ? `?${params.toString()}` : ''
    }
    const q = buildParams()
    Promise.all([
      fetch(`/api/v2/mission-risk/latest${q}`).then(r => r.json()).catch(() => ({ results: [] })),
      fetch(`/api/v2/market-health/latest${q}`).then(r => r.json()).catch(() => ({ results: [] })),
      fetch(`/api/v2/mission-allocation/latest${q}`).then(r => r.json()).catch(() => ({ results: [] })),
      fetch(`/api/v2/targeting/schools${q}`).then(r => r.json()).catch(() => ({ schools: [] })),
    ]).then(([mr, mh, ma, st]) => {
      const mrResults = mr?.results || []
      const mhResults = mh?.results || []
      const maResults = ma?.results || []
      const stResults = st?.schools || st?.results || []
      const highestMr = mrResults.length ? mrResults.reduce((acc, cur) => ( (cur.mission_risk_score ?? -Infinity) > (acc.mission_risk_score ?? -Infinity) ? cur : acc), mrResults[0]) : null
      const weakestMh = mhResults.length ? mhResults.reduce((acc, cur) => ( (cur.market_health_score ?? Infinity) < (acc.market_health_score ?? Infinity) ? cur : acc), mhResults[0]) : null
      const topSchools = (stResults || []).slice().sort((a,b) => ((b.priority ?? b.score ?? b.targeting_score ?? 0) - (a.priority ?? a.score ?? a.targeting_score ?? 0))).slice(0,3)

      // Build one-line recommended actions
      const highestMrAction = highestMr ? (() => {
        const target = highestMr.company_name || highestMr.company || highestMr.unit_name || highestMr.company_rsid || 'the unit'
        const factors = highestMr.top_risk_factors || highestMr.risk_factors || []
        if (factors && factors.length) {
          const f = factors.slice(0,2).join(' and ')
          return `Investigate ${f} in ${target}.`
        }
        return `Investigate mission risk drivers in ${target}.`
      })() : null

      const topSchoolsAction = (topSchools && topSchools.length) ? (() => {
        const names = topSchools.map(s => (s.name || s.school || s.school_name)).filter(Boolean)
        return `Prioritize commander engagement and recruiter coverage for ${names.join(', ')}.`
      })() : null

      const weakestMhAction = weakestMh ? (() => {
        const market = weakestMh.market || weakestMh.market_name || weakestMh.cbsa_code || 'this market'
        return `Review access strategy and event coverage in ${market}.`
      })() : null

      const allocAction = (() => {
        const cnt = maResults.length
        if (!cnt) return 'No allocation actions needed.'
        if (cnt <= 10) return 'Monitor allocation distribution; consider light adjustments.'
        return 'Reassess company mission distribution for overburdened units.'
      })()

      setBriefing({ highestMr, weakestMh, allocationCount: maResults.length, topSchools, highestMrAction, topSchoolsAction, weakestMhAction, allocAction })
    }).finally(() => setLoadingBriefing(false))
  }

  useEffect(() => { loadBriefing() }, [unitRsid, asOf, customDate])
  const latestMH = marketHealth && marketHealth[0]
  const latestMR = missionRisk && missionRisk[0]
  const noData = !marketHealth && !missionRisk && (!allocation || allocation.length === 0) && (!targeting || targeting.length === 0)

  const scrollToPanel = (id) => {
    try {
      const el = document.getElementById(id)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } catch (e) {}
  }

  return (
    <div style={{ padding: 20 }}>
      <h2>Command Center (MVP)</h2>

      {loading && <div>Loading engine data…</div>}

      {!loading && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center' }}>
            <label>
              As-Of:
              <select value={asOf} onChange={e => setAsOf(e.target.value)} style={{ marginLeft: 8 }}>
                <option value="today">Today</option>
                <option value="yesterday">Yesterday</option>
                <option value="last_7">Last 7 days</option>
                <option value="custom">Custom</option>
              </select>
            </label>

            {asOf === 'custom' && (
              <label>
                Date:
                <input type="date" value={customDate} onChange={e => setCustomDate(e.target.value)} style={{ marginLeft: 8 }} />
              </label>
            )}

            <label>
              Unit:
              <select value={unitRsid} onChange={e => setUnitRsid(e.target.value)} style={{ marginLeft: 8 }}>
                {units && units.length ? (
                  units.map(u => (
                    <option key={u.rsid} value={u.rsid}>{u.display_name || u.rsid}</option>
                  ))
                ) : (
                  <option value="">(no units)</option>
                )}
              </select>
            </label>

            <button style={{ marginLeft: 8 }} onClick={() => setShowHierarchy(s => !s)}>{showHierarchy ? 'Hide hierarchy' : 'Show hierarchy'}</button>

            <label>
              Market:
              <select value={marketFilter} onChange={e => setMarketFilter(e.target.value)} style={{ marginLeft: 8 }}>
                <option value="all">All</option>
                {markets && markets.length ? markets.map(m => (
                  <option key={m.cbsa_code || m.cbsaName || m.cbsa_name} value={m.cbsa_code || m.cbsaCode || m.cbsa_code}>{m.cbsa_name || m.cbsaName || m.cbsaCode || m.cbsa_code}</option>
                )) : null}
              </select>
            </label>
          </div>
          {showHierarchy && (
            <div style={{ marginBottom: 12, padding: 12, border: '1px solid #eee', borderRadius: 6 }}>
              <h5>Unit hierarchy (depth 2)</h5>
              {loadingHierarchy && <div>Loading...</div>}
              {!loadingHierarchy && hierarchy && (
                <div>
                  {/** simple recursive render */}
                  {function renderNode(n, depth=0){
                    return (
                      <div key={n.unit_rsid || n.rsid || n.unit_name} style={{ marginLeft: depth * 12 }}>
                        <div><strong>{n.unit_name || n.display_name || n.rsid}</strong> {n.unit_rsid || n.rsid ? `(${n.unit_rsid || n.rsid})` : ''}</div>
                        {n.children && n.children.length ? n.children.map(c => renderNode(c, depth+1)) : null}
                      </div>
                    )
                  }(hierarchy)}
                </div>
              )}
              {!loadingHierarchy && !hierarchy && (<div>No hierarchy available</div>)}
            </div>
          )}

          {/* Command briefing summary panel */}
          <div style={{ marginBottom: 12, padding: 12, border: '1px solid #ddd', borderRadius: 6, background: '#fafafa', display: 'flex', gap: 12, alignItems: 'center' }}>
            {loadingBriefing ? (
              <div>Loading briefing…</div>
            ) : (
              <>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>Highest Mission Risk</div>
                  <div style={{ fontWeight: 600 }}>{briefing?.highestMr ? (briefing.highestMr.company_name || briefing.highestMr.company || briefing.highestMr.unit_name || briefing.highestMr.company_rsid) : 'No items'}</div>
                  <div style={{ fontSize: 12, color: '#444' }}>{briefing?.highestMr ? `Score ${briefing.highestMr.mission_risk_score ?? '—'} · ${mrLevel(briefing.highestMr.mission_risk_score)}` : ''}</div>
                  {briefing?.highestMrAction && <div style={{ fontStyle: 'italic', marginTop: 6 }}>{briefing.highestMrAction}</div>}
                      <div style={{ marginTop: 6 }}><a href="#" onClick={(e)=>{e.preventDefault(); scrollToPanel('mission-risk-panel')}}>View mission risk details</a></div>
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>Top Priority Schools</div>
                  {briefing?.topSchools && briefing.topSchools.length ? (
                    briefing.topSchools.map((s, i) => (
                      <div key={i} style={{ fontWeight: 600 }}>{s.name || s.school || s.school_name || 'School'} — {s.priority ?? s.score ?? s.targeting_score ?? '—'}</div>
                    ))
                  ) : (
                    <div style={{ fontWeight: 600 }}>None</div>
                  )}
                  {briefing?.topSchoolsAction && <div style={{ fontStyle: 'italic', marginTop: 6 }}>{briefing.topSchoolsAction}</div>}
                  <div style={{ marginTop: 6 }}><a href="#" onClick={(e)=>{e.preventDefault(); scrollToPanel('targeting-panel')}}>View schools</a></div>
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>Weakest Market Health</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ fontWeight: 600 }}>{briefing?.weakestMh ? (briefing.weakestMh.market || briefing.weakestMh.market_name || briefing.weakestMh.cbsa_code || '—') : 'No data'}</div>
                    {briefing?.weakestMh && <div style={{ fontSize: 12, background: '#fff7e6', padding: '2px 6px', borderRadius: 12, color: '#8a6d00' }}>{mhLevel(briefing.weakestMh.market_health_score)}</div>}
                  </div>
                  <div style={{ fontSize: 12, color: '#444' }}>{briefing?.weakestMh ? `Score ${briefing.weakestMh.market_health_score ?? '—'}` : ''}</div>
                  {briefing?.weakestMhAction && <div style={{ fontStyle: 'italic', marginTop: 6 }}>{briefing.weakestMhAction}</div>}
                  <div style={{ marginTop: 6 }}><a href="#" onClick={(e)=>{e.preventDefault(); scrollToPanel('market-health-panel')}}>View market details</a></div>
                </div>

                <div style={{ width: 220 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>Allocation Pressure</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ fontWeight: 600 }}>{briefing ? `${briefing.allocationCount} companies` : '—'}</div>
                    {briefing && <div style={{ fontSize: 12, background: '#e6f7ff', padding: '2px 6px', borderRadius: 12, color: '#055160' }}>{allocLevel(briefing.allocationCount)}</div>}
                  </div>
                  {briefing?.allocAction && <div style={{ fontStyle: 'italic', marginTop: 6 }}>{briefing.allocAction}</div>}
                  <div style={{ marginTop: 6 }}><a href="#" onClick={(e)=>{e.preventDefault(); scrollToPanel('allocation-panel')}}>View allocation</a></div>
                </div>

                <div style={{ alignSelf: 'start' }}>
                  <button onClick={loadBriefing}>Refresh</button>
                </div>
              </>
            )}
          </div>
          {noData ? (
            <div style={{ padding: 20, border: '1px dashed #ccc', borderRadius: 6, marginBottom: 16 }}>
              No data returned for the selected filters. Try changing the As-Of, Unit, or Market.
            </div>
          ) : null}

          <section style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
            <div id="market-health-panel" style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
              <h4>Market Health</h4>
              {latestMH ? (
                <div>
                  <div><strong>Summary:</strong> {latestMH.summary || latestMH.mh_summary || '—'}</div>
                  <div><strong>Score:</strong> {latestMH.market_health_score ?? '—'}</div>
                  {latestMH.components_json && (
                    <div style={{ marginTop: 8 }}>
                      <strong>Components:</strong>
                      <ul>
                        {Object.entries(latestMH.components_json).map(([k,v]) => (
                          <li key={k}>{k}: {String(v)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div>No market health data</div>
              )}
            </div>

            <div id="mission-risk-panel" style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
              <h4>Mission Risk</h4>
              {latestMR ? (
                <div>
                  <div><strong>Summary:</strong> {latestMR.summary || latestMR.mr_summary || '—'}</div>
                  <div><strong>Score:</strong> {latestMR.mission_risk_score ?? '—'}</div>
                  {latestMR.top_risk_factors && (
                    <div style={{ marginTop: 8 }}>
                      <strong>Top Factors:</strong>
                      <ol>
                        {latestMR.top_risk_factors.slice(0,5).map((f, i) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              ) : (
                <div>No mission risk data</div>
              )}
            </div>

            <div id="allocation-panel" style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
              <h4>Allocation Snapshot</h4>
                {allocation && allocation.length ? (
                <div>
                  <div><strong>Companies returned:</strong> {allocation.length}</div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 12, alignItems: 'center' }}>
                      <div>
                        <div style={{ fontSize: 12, color: '#666' }}>Recommended</div>
                        <div style={{ fontWeight: 700, fontSize: 18 }}>{recommendedTotal != null ? recommendedTotal : '—'}</div>
                        <div style={{ fontSize: 12, color: '#666' }}>Recommended based on current supportability and risk</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 12, color: '#666' }}>Approved</div>
                        <input type="number" value={approvedAllocation ?? ''} onChange={e => setApprovedAllocation(e.target.value)} style={{ marginLeft: 8, width: 140, fontSize: 16, padding: '6px 8px', border: (recommendedTotal != null && approvedAllocation !== '' && Number(approvedAllocation) !== Number(recommendedTotal)) ? '2px solid #c0392b' : '1px solid #ccc' }} />
                        {(recommendedTotal != null && approvedAllocation !== '' && Number(approvedAllocation) !== Number(recommendedTotal)) && (
                          <div style={{ color: '#c0392b', fontSize: 12, marginTop: 6 }}>Commander-approved allocation differs from engine recommendation</div>
                        )}
                      </div>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <label>
                        Decision Status:
                        <select value={decisionStatus} onChange={e => setDecisionStatus(e.target.value)} style={{ marginLeft: 8 }}>
                          <option value="recommended">recommended</option>
                          <option value="approved">approved</option>
                          <option value="adjusted">adjusted</option>
                          <option value="rejected">rejected</option>
                        </select>
                      </label>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <label>Decision Notes:</label>
                      <div><textarea value={decisionNotes} onChange={e => setDecisionNotes(e.target.value)} rows={3} style={{ width: '100%', marginTop: 6 }} /></div>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <label>Approved By: <input type="text" value={approvedBy} onChange={e => setApprovedBy(e.target.value)} style={{ marginLeft: 8 }} /></label>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      {decisionError && <div style={{ color: 'crimson', marginBottom: 6 }}>{decisionError}</div>}
                      {decisionSuccess && <div style={{ color: 'green', marginBottom: 6 }}>{decisionSuccess}</div>}
                      <button onClick={() => {
                        setDecisionError(null)
                        setDecisionSuccess(null)
                        if (!runId) { setDecisionError('No run available to save decision'); return }
                        setSavingDecision(true)
                        fetch(`/api/v2/mission-allocation/runs/${encodeURIComponent(runId)}/decision`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({approved_allocation: approvedAllocation !== '' ? Number(approvedAllocation) : null, decision_status: decisionStatus, decision_notes: decisionNotes, approved_by: approvedBy})})
                          .then(r => r.json())
                          .then(j => {
                            if (j && j.status === 'ok') {
                              // refresh decision state
                              fetch(`/api/v2/mission-allocation/runs/${encodeURIComponent(runId)}/decision`).then(rr => rr.json()).then(d => {
                                if (d && d.status === 'ok') {
                                  setApprovedAllocation(d.approved_allocation ?? '')
                                  setDecisionStatus(d.decision_status ?? 'recommended')
                                  setDecisionNotes(d.decision_notes ?? '')
                                  setApprovedBy(d.approved_by ?? '')
                                  setApprovedAt(d.approved_at ?? null)
                                  setDecisionExists(Boolean(d.decision_status || d.approved_allocation || d.decision_notes || d.approved_by || d.approved_at))
                                  setDecisionSuccess('Decision saved')
                                } else {
                                  setDecisionError('Decision saved but failed to reload')
                                }
                              }).catch(() => setDecisionError('Decision saved but failed to reload'))
                            } else {
                              setDecisionError('Failed to save decision: ' + (j && j.message ? j.message : JSON.stringify(j)))
                            }
                          }).catch(e => setDecisionError('Failed to save decision: ' + String(e))).finally(() => setSavingDecision(false))
                      }}>{savingDecision ? 'Saving…' : 'Save / Approve'}</button>
                    </div>
                  <div style={{ marginTop: 8, maxHeight: 160, overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr>
                          <th style={{ textAlign: 'left', borderBottom: '1px solid #eee' }}>Company</th>
                          <th style={{ textAlign: 'left', borderBottom: '1px solid #eee' }}>Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {allocation.slice(0,10).map((c, i) => (
                          <tr key={i}>
                            <td style={{ padding: '6px 4px' }}>{c.company_name || c.company || c.company_rsid || '—'}</td>
                            <td style={{ padding: '6px 4px' }}>{(c.score ?? c.final_score ?? c.compute_score) ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {/* Decision metadata and empty-state */}
                  <div style={{ marginTop: 10, fontSize: 13 }}>
                    {!decisionLoaded ? (
                      <div>Loading decision…</div>
                    ) : (!decisionExists ? (
                      <div style={{ color: '#666' }}>No commander decision recorded yet.</div>
                    ) : (
                      <div>
                        <div><strong>Decision Status:</strong> {decisionStatus}</div>
                        <div><strong>Approved By:</strong> {approvedBy || '—'}</div>
                        <div><strong>Approved At:</strong> {approvedAt || '—'}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div>No allocation data</div>
              )}
            </div>
          </section>

          <section style={{ display: 'flex', gap: 16 }}>
            <div id="targeting-panel" style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
              <h4>Top Target Schools</h4>
              {targeting && targeting.length ? (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left', borderBottom: '1px solid #eee' }}>School</th>
                      <th style={{ textAlign: 'left', borderBottom: '1px solid #eee' }}>Priority / Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {targeting.slice(0,25).map((s, i) => (
                      <tr key={i}>
                        <td style={{ padding: '6px 4px' }}>{s.name || s.school || s.school_name || '—'}</td>
                        <td style={{ padding: '6px 4px' }}>{s.priority ?? s.score ?? s.targeting_score ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div>No target schools</div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  )
}
