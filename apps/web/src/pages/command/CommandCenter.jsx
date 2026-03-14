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

  const loadBriefing = () => {
    setLoadingBriefing(true)
    const buildParams = () => {
      const params = new URLSearchParams()
      if (unitRsid) params.set('unit_rsid', unitRsid)
      // use asOf/customDate to build as_of_date
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
    ]).then(([mr, mh, ma]) => {
      const mrResults = mr?.results || []
      const mhResults = mh?.results || []
      const maResults = ma?.results || []
      const highestMr = mrResults.length ? mrResults.reduce((acc, cur) => (cur.mission_risk_score > (acc.mission_risk_score||-Infinity) ? cur : acc), mrResults[0]) : null
      const weakestMh = mhResults.length ? mhResults.reduce((acc, cur) => (cur.market_health_score < (acc.market_health_score||Infinity) ? cur : acc), mhResults[0]) : null
      setBriefing({ highestMr, weakestMh, allocationCount: maResults.length })
    }).finally(() => setLoadingBriefing(false))
  }

  useEffect(() => { loadBriefing() }, [])
  const latestMH = marketHealth && marketHealth[0]
  const latestMR = missionRisk && missionRisk[0]
  const noData = !marketHealth && !missionRisk && (!allocation || allocation.length === 0) && (!targeting || targeting.length === 0)

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
          {noData ? (
            <div style={{ padding: 20, border: '1px dashed #ccc', borderRadius: 6, marginBottom: 16 }}>
              No data returned for the selected filters. Try changing the As-Of, Unit, or Market.
            </div>
          ) : null}

          <section style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
            <div style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
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

            <div style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
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

            <div style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
              <h4>Allocation Snapshot</h4>
              {allocation && allocation.length ? (
                <div>
                  <div><strong>Companies returned:</strong> {allocation.length}</div>
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
                </div>
              ) : (
                <div>No allocation data</div>
              )}
            </div>
          </section>

          <section style={{ display: 'flex', gap: 16 }}>
            <div style={{ flex: 1, padding: 16, border: '1px solid #ddd', borderRadius: 6 }}>
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
