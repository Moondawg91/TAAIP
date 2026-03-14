import React, { useEffect, useState } from 'react'

export default function CommandCenter() {
  const [marketHealth, setMarketHealth] = useState(null)
  const [missionRisk, setMissionRisk] = useState(null)
  const [targeting, setTargeting] = useState([])
  const [allocation, setAllocation] = useState(null)

  useEffect(() => {
    fetch('/api/v2/market-health/latest')
      .then(r => r.json())
      .then(d => setMarketHealth(d.results || d))
      .catch(() => setMarketHealth(null))

    fetch('/api/v2/mission-risk/latest')
      .then(r => r.json())
      .then(d => setMissionRisk(d.results || d))
      .catch(() => setMissionRisk(null))

    fetch('/api/v2/targeting/schools')
      .then(r => r.json())
      .then(d => setTargeting(d.results || d || []))
      .catch(() => setTargeting([]))

    fetch('/api/v2/mission-allocation/latest')
      .then(r => r.json())
      .then(d => setAllocation(d.results || d))
      .catch(() => setAllocation(null))
  }, [])

  const latestMH = marketHealth && marketHealth[0]
  const latestMR = missionRisk && missionRisk[0]

  return (
    <div style={{ padding: 20 }}>
      <h2>Command Center (MVP)</h2>

      <section style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
        <div style={{ flex: 1, padding: 12, border: '1px solid #ddd' }}>
          <h4>Market Health</h4>
          {latestMH ? (
            <div>
              <div>Summary: {latestMH.summary || latestMH.mh_summary || '—'}</div>
              <div>Score: {latestMH.market_health_score ?? '—'}</div>
            </div>
          ) : (
            <div>Loading...</div>
          )}
        </div>

        <div style={{ flex: 1, padding: 12, border: '1px solid #ddd' }}>
          <h4>Mission Risk</h4>
          {latestMR ? (
            <div>
              <div>Summary: {latestMR.summary || latestMR.mr_summary || '—'}</div>
              <div>Score: {latestMR.mission_risk_score ?? '—'}</div>
            </div>
          ) : (
            <div>Loading...</div>
          )}
        </div>

        <div style={{ flex: 1, padding: 12, border: '1px solid #ddd' }}>
          <h4>Allocation</h4>
          {allocation ? <div>Companies: {(allocation.length || allocation.results?.length) ?? '—'}</div> : <div>Loading...</div>}
        </div>
      </section>

      <section style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <h4>Top Target Schools</h4>
          <ol>
            {targeting && targeting.length ? (
              targeting.slice(0, 10).map((s, i) => <li key={i}>{s.name || s.school || JSON.stringify(s)}</li>)
            ) : (
              <li>Loading...</li>
            )}
          </ol>
        </div>
      </section>
    </div>
  )
}
