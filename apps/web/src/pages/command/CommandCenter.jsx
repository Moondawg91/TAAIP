import React, { useEffect, useState } from 'react'

export default function CommandCenter() {
  const [marketHealth, setMarketHealth] = useState(null)
  const [missionRisk, setMissionRisk] = useState(null)
  const [targeting, setTargeting] = useState([])
  const [allocation, setAllocation] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch('/api/v2/market-health/latest').then(r => r.json()).catch(() => null),
      fetch('/api/v2/mission-risk/latest').then(r => r.json()).catch(() => null),
      fetch('/api/v2/targeting/schools').then(r => r.json()).catch(() => ({ results: [] })),
      fetch('/api/v2/mission-allocation/latest').then(r => r.json()).catch(() => ({ results: [] })),
    ]).then(([mh, mr, st, ma]) => {
      setMarketHealth(mh?.results || mh || null)
      setMissionRisk(mr?.results || mr || null)
      setTargeting(st?.results || [])
      setAllocation(ma?.results || [])
      setLoading(false)
    })
  }, [])

  const latestMH = marketHealth && marketHealth[0]
  const latestMR = missionRisk && missionRisk[0]

  return (
    <div style={{ padding: 20 }}>
      <h2>Command Center (MVP)</h2>

      {loading && <div>Loading engine data…</div>}

      {!loading && (
        <>
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
