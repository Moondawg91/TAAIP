import React, { useEffect, useState } from 'react'
import DataHubImports from './ImportsPage'
import { dataHubListRuns, dataHubListRegistry, dataHubStorage, dataHubHealth, dataHubGetRun } from '../../api/client'

export default function DataHubPage(){
  const [runs, setRuns] = useState([])
  const [registry, setRegistry] = useState([])
  const [storage, setStorage] = useState(null)
  const [health, setHealth] = useState(null)
  const [runDetailsMap, setRunDetailsMap] = useState({})
  const [expandedRunId, setExpandedRunId] = useState(null)
  const [lastCommit, setLastCommit] = useState(null)
  const storedDatasets = React.useMemo(()=>{
    try{
      const okStatuses = new Set(['success','completed','committed','done','ok'])
      const map = {}
      ;(runs || []).forEach(r => {
        const status = (r && r.status) ? String(r.status).toLowerCase() : ''
        if(!okStatuses.has(status)) return // only include successful runs
        const key = r.dataset_key || r.detected_dataset_key || r.dataset || 'unknown'
        if(!map[key]) map[key] = r
        else {
          const cur = map[key]
          const curTs = new Date(cur.ended_at || cur.updated_at || cur.finished_at || cur.created_at || cur.started_at || 0).getTime() || 0
          const rTs = new Date(r.ended_at || r.updated_at || r.finished_at || r.created_at || r.started_at || 0).getTime() || 0
          if(rTs > curTs) map[key] = r
        }
      })
      return Object.keys(map).map(k => ({ dataset_key: k, latest: map[k]}))
    }catch(e){ return [] }
  }, [runs])

  function getDestinationFromDatasetKey(dk){
    if(!dk) return null
    const lower = String(dk).toLowerCase()
    if(lower.includes('school') || lower.includes('school_program') || lower.includes('school_program_fact') || lower.includes('rsid')) return '/planning/targeting-board'
    if(lower.includes('market') || lower.includes('market_potential') || lower.includes('market_health')) return '/command-center'
    if(lower.includes('mission') || lower.includes('mission_allocation')) return '/command-center/mission-assessment'
    if(lower.includes('event') || lower.includes('emm') || lower.includes('marketing')) return '/roi'
    return null
  }

  useEffect(()=>{
    let mounted = true
    async function load(){
      try{
        const [r, reg, s, h] = await Promise.all([
          dataHubListRuns().catch(()=>[]),
          dataHubListRegistry().catch(()=>[]),
          dataHubStorage().catch(()=>null),
          dataHubHealth().catch(()=>null)
        ])
        if (!mounted) return
        setRuns(Array.isArray(r)? r : (r && r.items ? r.items : []))
        setRegistry(reg || [])
        setStorage(s)
        setHealth(h)
        // read last commit info persisted by ImportsPage
        try{
          const raw = sessionStorage.getItem('datahub_last_commit')
          if(raw){
            const obj = JSON.parse(raw)
            setLastCommit(obj)
          }
        }catch(e){}
      }catch(e){ /* ignore */ }
    }
    load()
    return ()=>{ mounted = false }
  }, [])

  return (<>
    <div style={{ padding: 16 }}>
      <h1>Data Hub</h1>
      <p style={{ maxWidth: 900 }}>Upload, preview, validate and commit datasets. The Data Hub is the canonical ingestion workspace for the application — it handles detection, validation, header aliasing, and dataset-specific loaders. Use this single workspace for all import operations.</p>

      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        <div style={{ flex: 2 }}>
          <DataHubImports />
          {/* Post-commit success card (render when a commit just occurred) */}
          {lastCommit && (
            <section style={{marginTop:16, padding:16, border:'1px solid #d7f0e6', background:'#f7fffb', borderRadius:8}}>
              <h2 style={{marginTop:0}}>Upload successful</h2>
              <div style={{marginTop:6}}><strong>Data committed successfully</strong></div>
              <div style={{marginTop:8}}><strong>Dataset:</strong> {lastCommit.dataset_key || lastCommit.dataset || 'unknown'}</div>
              <div><strong>Rows loaded:</strong> {lastCommit.rows_loaded || lastCommit.rows_in || 0}</div>
              <div><strong>Run ID:</strong> {lastCommit.run_id || lastCommit.id}</div>
              <div><strong>Commit status:</strong> {lastCommit.status || 'committed'}</div>
              <div><strong>Commit status:</strong> {lastCommit.status || 'committed'}</div>
              <div><strong>Analytics status:</strong> {(lastCommit.analytics_check && String(lastCommit.analytics_check).toLowerCase()==='done') || (lastCommit.analytics_check==='true') ? 'Ready for analytics' : (lastCommit.analytics_check ? String(lastCommit.analytics_check) : 'Analytics verification pending')}</div>
              {lastCommit.processing && (
                <>
                  <div><strong>Analytics ready:</strong> {lastCommit.processing.analytics_ready ? 'Yes' : 'No'}</div>
                  <div><strong>Affected modules:</strong> {(lastCommit.processing.affected_modules && Array.isArray(lastCommit.processing.affected_modules)) ? lastCommit.processing.affected_modules.join(', ') : '—'}</div>
                </>
              )}
              <div><strong>Completed:</strong> {lastCommit.ended_at || lastCommit.updated_at || lastCommit.committed_at || lastCommit.finished_at || lastCommit.created_at || ''}</div>
              <div style={{marginTop:10}}>
                <button onClick={async ()=>{
                  const rid = lastCommit.run_id || lastCommit.id
                  if(!rid) return
                  try{
                    const detail = await dataHubGetRun(rid)
                    setRunDetailsMap(m => Object.assign({}, m, { [rid]: detail }))
                    setExpandedRunId(rid)
                  }catch(e){}
                }}>Inspect run</button>
                <button style={{marginLeft:8}} onClick={async ()=>{
                  const rid = lastCommit.run_id || lastCommit.id
                  if(!rid) return
                  try{
                    const resp = await fetch(`/api/v2/datahub/runs/${encodeURIComponent(rid)}/processing`)
                    const hist = await resp.json()
                    setRunDetailsMap(m => Object.assign({}, m, { [rid]: Object.assign({}, (m[rid]||{}), { processing_history: hist }) }))
                    setExpandedRunId(rid)
                  }catch(e){ console.error('fetch processing history error', e) }
                }}>View processing history</button>
                <button style={{marginLeft:8}} onClick={()=>{ try{ const dest = getDestinationFromDatasetKey(lastCommit.dataset_key || lastCommit.dataset); if(dest) window.location.href = dest }catch(e){} }}>View destination</button>
                <button style={{marginLeft:8}} onClick={()=>{ window.location.href = '/command-center' }}>Go to command center</button>
                <button style={{marginLeft:8}} onClick={()=>{ try{ sessionStorage.removeItem('datahub_last_commit'); setLastCommit(null)}catch(e){} }}>Dismiss</button>
              </div>
            </section>
          )}
        </div>

        <div style={{ flex: 1, minWidth: 280 }}>
          <section style={{ marginBottom: 16, padding: 12, border: '1px solid #e0e0e0', borderRadius: 6 }}>
            <h3 style={{ marginTop: 0 }}>Recent Runs</h3>
            {runs && runs.length>0 ? (
              <ul style={{ margin: 0, paddingLeft: 16 }}>
                {runs.slice(0,6).map(r => <li key={r.run_id || r.id}>{r.run_id || r.id} — {r.status} — {r.dataset_key || r.detected_dataset_key || 'unknown'}</li>)}
              </ul>
            ) : <div>No recent runs</div>}
          </section>

          <section style={{ marginBottom: 16, padding: 12, border: '1px solid #e0e0e0', borderRadius: 6 }}>
            <h3 style={{ marginTop: 0 }}>Supported Datasets</h3>
            {registry && registry.length>0 ? (
              <ul style={{ margin: 0, paddingLeft: 16 }}>
                {registry.map(d => <li key={d.key}>{d.key} — {d.description || d.title || ''}</li>)}
              </ul>
            ) : <div>No registry entries found</div>}
          </section>

          <section style={{marginBottom: 16, padding: 12, border: '1px solid #e0e0e0', borderRadius: 6 }}>
            <h3 style={{ marginTop: 0 }}>Stored Datasets</h3>
            {storedDatasets && storedDatasets.length>0 ? (
              <div style={{overflowX:'auto'}}>
                <table style={{width:'100%', borderCollapse:'collapse'}}>
                  <thead>
                    <tr>
                      <th style={{padding:6}}>dataset_key</th>
                      <th style={{padding:6}}>latest_run</th>
                      <th style={{padding:6}}>rows_loaded</th>
                      <th style={{padding:6}}>last_updated</th>
                      <th style={{padding:6}}>status</th>
                      <th style={{padding:6}}>action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {storedDatasets.map(d => (
                      <tr key={d.dataset_key}>
                        <td style={{padding:6}}>{d.dataset_key}</td>
                        <td style={{padding:6}}>{d.latest && (d.latest.run_id || d.latest.id)}</td>
                        <td style={{padding:6}}>{d.latest && (d.latest.rows_loaded || d.latest.rows_in || 0)}</td>
                        <td style={{padding:6}}>{d.latest && (d.latest.finished_at || d.latest.created_at || d.latest.run_started || '')}</td>
                        <td style={{padding:6}}>{d.latest && d.latest.status}</td>
                        <td style={{padding:6}}>
                          <button onClick={async ()=>{
                            const rid = d.latest.run_id || d.latest.id
                            if(!rid) return
                            const detail = await dataHubGetRun(rid)
                            if(detail){ setRunDetailsMap(m => Object.assign({}, m, { [rid]: detail })); setExpandedRunId(rid) }
                          }}>Inspect</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <div>No stored datasets found</div>}
          </section>

          <section style={{ padding: 12, border: '1px solid #e0e0e0', borderRadius: 6 }}>
            <h3 style={{ marginTop: 0 }}>Storage / Health</h3>
            <div>Storage: {storage ? (storage.files_count || JSON.stringify(storage)) : 'unknown'}</div>
            <div>Health: {health ? (health.status || JSON.stringify(health)) : 'unknown'}</div>
          </section>
        </div>
      </div>
    </div>
    {expandedRunId && runDetailsMap && runDetailsMap[expandedRunId] && (
      <div style={{position:'fixed', right:20, top:80, width:420, maxHeight:'70vh', overflow:'auto', padding:12, border:'1px solid #ddd', background:'#fff', borderRadius:6, boxShadow:'0 6px 20px rgba(0,0,0,0.08)'}}>
        <h4 style={{marginTop:0}}>Run Details — {expandedRunId}</h4>
        <div style={{fontSize:13}}>
              {(() => {
                const detail = runDetailsMap[expandedRunId] || {}
                const preferred = ['dataset_key','status','rows_loaded','rows_in','error_summary','created_at','started_at','finished_at','ended_at','updated_at','committed_at','run_id']
                const rendered = []
                preferred.forEach(k => { if(detail[k] !== undefined) rendered.push([k, detail[k]]) })
                Object.entries(detail).forEach(([k,v]) => { if(!preferred.includes(k)) rendered.push([k,v]) })
                return rendered.map(([k,v]) => (
                  <div key={k} style={{marginBottom:6}}>
                    <strong>{k}:</strong> <span style={{color:'#333'}}>{typeof v === 'object' ? (JSON.stringify(v).length>400 ? JSON.stringify(v).slice(0,400)+'…' : JSON.stringify(v)) : String(v)}</span>
                  </div>
                ))
              })()}
            </div>
        <div style={{marginTop:8}}><button onClick={()=>setExpandedRunId(null)}>Close</button></div>
      </div>
    )}
    </>
  )
}
