import React, { useEffect, useState } from 'react'

function Tile({ title, loading, error, children }){
  return (
    <div style={{ flex:1, minWidth:220, padding:12, border:'1px solid #ddd', borderRadius:6, background:'#fff' }}>
      <div style={{ fontSize:12, color:'#666', marginBottom:8 }}>{title}</div>
      {loading ? <div>Loading…</div> : error ? <div style={{ color:'crimson' }}>{String(error)}</div> : <div>{children}</div>}
    </div>
  )
}

export default function FusionBriefing(){
  const [loading, setLoading] = useState(true)
  const [mr, setMr] = useState([])
  const [mh, setMh] = useState([])
  const [schools, setSchools] = useState([])
  const [alloc, setAlloc] = useState([])
  const [err, setErr] = useState(null)
  const [unit, setUnit] = useState('')

  useEffect(()=>{
    try{ const f = JSON.parse(localStorage.getItem('command_center_filters_v1') || '{}'); if(f.unitRsid) setUnit(f.unitRsid) }catch(e){}
    setLoading(true); setErr(null)
    const q = unit ? `?unit_rsid=${encodeURIComponent(unit)}` : ''
    Promise.all([
      fetch(`/api/v2/mission-risk/latest${q}`).then(r=>r.json()).catch(e=>{throw e}),
      fetch(`/api/v2/market-health/latest${q}`).then(r=>r.json()).catch(e=>{throw e}),
      fetch(`/api/v2/targeting/schools${q}`).then(r=>r.json()).catch(e=>({schools:[]})),
      fetch(`/api/v2/mission-allocation/runs${q}`).then(r=>r.json()).catch(e=>({rows:[]})),
    ]).then(([mrr,mhr,sch,ar])=>{
      setMr(mrr?.results || mrr || [])
      setMh(mhr?.results || mhr || [])
      setSchools(sch?.schools || sch?.results || [])
      // allocation runs listing -> map to runs
      setAlloc(ar?.rows || ar || [])
    }).catch(e=>{ setErr('Failed to load briefing data') }).finally(()=>setLoading(false))
  }, [unit])

  const highestMr = mr && mr.length ? mr.reduce((a,b)=>((b.mission_risk_score||-Infinity)>(a.mission_risk_score||-Infinity)?b:a), mr[0]) : null
  const weakestMh = mh && mh.length ? mh.reduce((a,b)=>((b.market_health_score||Infinity)<(a.market_health_score||Infinity)?b:a), mh[0]) : null
  const topSchools = (schools||[]).slice().sort((a,b)=>( (b.priority||b.score||0)-(a.priority||a.score||0) )).slice(0,5)
  const allocCount = (alloc||[]).length

  return (
    <div style={{ padding:20 }}>
      <h2>Fusion Briefing</h2>
      <div style={{ display:'flex', gap:12, marginBottom:16, flexWrap:'wrap' }}>
        <Tile title="Highest Mission Risk" loading={loading} error={err}>
          {highestMr ? (
            <div>
              <div style={{ fontWeight:700 }}>{highestMr.unit_name || highestMr.company_name || highestMr.company || highestMr.company_rsid || '—'}</div>
              <div>Score: {highestMr.mission_risk_score ?? '—'}</div>
            </div>
          ) : <div>No mission risk items</div>}
        </Tile>

        <Tile title="Weakest Market Health" loading={loading} error={err}>
          {weakestMh ? (
            <div>
              <div style={{ fontWeight:700 }}>{weakestMh.market_name || weakestMh.market || weakestMh.cbsa_code || '—'}</div>
              <div>Score: {weakestMh.market_health_score ?? '—'}</div>
            </div>
          ) : <div>No market health items</div>}
        </Tile>

        <Tile title="Top Priority Schools" loading={loading} error={err}>
          {topSchools && topSchools.length ? (
            <ol>
              {topSchools.map((s,i)=>(<li key={i}>{s.name || s.school || s.school_name || '—'} — {s.priority ?? s.score ?? '—'}</li>))}
            </ol>
          ) : <div>No prioritized schools</div>}
        </Tile>

        <Tile title="Allocation Pressure" loading={loading} error={err}>
          <div style={{ fontWeight:700 }}>{allocCount} runs</div>
          <div style={{ fontSize:12, color:'#666' }}>{allocCount>20 ? 'High pressure' : allocCount>0 ? 'Moderate' : 'No pressure'}</div>
        </Tile>
      </div>

      <div>
        <button onClick={()=>{ try{ window.print() }catch(e){} }}>Print Briefing</button>
      </div>
    </div>
  )
}
