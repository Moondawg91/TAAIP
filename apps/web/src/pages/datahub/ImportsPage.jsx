import React, {useEffect, useState} from 'react'
import { getMe, dataHubUpload, dataHubListRegistry, dataHubListRuns, dataHubGetRun, dataHubDownloadErrors } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'

export default function DataHubImports(){
  const [importers, setImporters] = useState([])
  const [loading, setLoading] = useState(true)

  // Upload flow state
  const [file, setFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [needsDataset, setNeedsDataset] = useState(null)
  const [selectedDataset, setSelectedDataset] = useState('')
  const [legacyJobId, setLegacyJobId] = useState(null)
  const [preview, setPreview] = useState([])
  const [columns, setColumns] = useState([])
  const [statusMessage, setStatusMessage] = useState(null)
  const [validResult, setValidResult] = useState(null)
  const [commitResult, setCommitResult] = useState(null)
  const [analyticsStatus, setAnalyticsStatus] = useState(null)
  const [postCommitInfo, setPostCommitInfo] = useState(null)
  const [runDetailsMap, setRunDetailsMap] = useState({})
  const [expandedRunId, setExpandedRunId] = useState(null)
  const [destinationPath, setDestinationPath] = useState(null)
  const [canUpload, setCanUpload] = useState(false)
  const [runs, setRuns] = useState([])

  useEffect(()=>{
    let mounted = true
    ;(async ()=>{
      try{
        const registry = await dataHubListRegistry()
        const items = Array.isArray(registry) ? registry : (registry && registry.specs) ? registry.specs : (registry && registry.importers) ? registry.importers : []
        if (mounted) setImporters(items)
        const runsResp = await dataHubListRuns()
        if (mounted) setRuns(runsResp || [])
      }catch(e){ if (mounted) { setImporters([]); setRuns([]) } }
      finally{ if (mounted) setLoading(false) }
    })()
    return ()=>{ mounted = false }
  },[])

  const { hasPerm } = useAuth()
  useEffect(()=>{
    let canceled = false
    try{
      if(!canceled && hasPerm && hasPerm('datahub.upload')) setCanUpload(true)
    }catch(e){}
    return ()=>{ canceled = true }
  },[hasPerm])

  async function handleUpload(e){
    e.preventDefault()
    setStatusMessage('Uploading…')
    setJobId(null); setPreview([]); setColumns([]); setValidResult(null); setCommitResult(null)
    if(!file){ setStatusMessage('Choose a file first'); return }
    try{
      // Always call the preview endpoint first to avoid hitting upload validation
      const fd = new FormData()
      fd.append('file', file)

      const token = localStorage.getItem('taaip_jwt')
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`

      const res = await fetch('/api/v2/datahub/preview', { method: 'POST', body: fd, headers })
      let j = null
      try{ j = await res.json() }catch(e){ j = null }
      if (!res.ok) {
        // If preview failed with a validation-style error, surface it
        const err = (j && (j.error || j.message)) ? (j.error || j.message) : 'preview failed'
        throw new Error(err)
      }

      const jid = j && (j.run_id || j.runId || j.id)
      setJobId(jid || null)

      // handle low-confidence gating response from preview
      if (j && j.status === 'needs_dataset_selection'){
        setNeedsDataset({ suggested: j.suggested_dataset, confidence: j.detected_confidence, preview_rows: j.preview_rows || j.previewRows || j.preview || [] })
        if(j.suggested_dataset) setSelectedDataset(j.suggested_dataset)
        setStatusMessage('Dataset selection required — please choose dataset')
        const previewRows = j && (j.preview_rows || j.preview || j.previewRows)
        if(previewRows && Array.isArray(previewRows)){
          setPreview(previewRows)
          const cols = previewRows.length>0 ? Object.keys(previewRows[0]) : []
          setColumns(cols)
        }
        return
      }

      // Normal preview result
      const previewRows = j && (j.preview_rows || j.preview || j.previewRows)
      if(previewRows && Array.isArray(previewRows)){
        setPreview(previewRows)
        const cols = previewRows.length>0 ? Object.keys(previewRows[0]) : []
        setColumns(cols)
        setStatusMessage(`Preview ready — ${previewRows.length} rows`)
      } else {
        setStatusMessage('Preview complete — no preview rows returned')
      }
      // refresh runs list
      try{ const runsResp = await dataHubListRuns(); setRuns(runsResp || []) }catch(e){}
    }catch(err){
      // If backend returned structured JSON, render a readable error summary
      try{
        if(err && err.body){
          const b = err.body
          if (b && b.errors && Array.isArray(b.errors)){
            setStatusMessage('Upload validation errors: ' + b.errors.length)
            setPreview([])
            setColumns([])
            // expose structured validation object for UI if needed
            setValidResult(b)
            return
          }
          if (b && (b.error || b.message)){
            setStatusMessage('Upload error: ' + (b.error || b.message))
            return
          }
        }
      }catch(e){}
      setStatusMessage('Upload error: ' + String(err))
    }
  }

  async function continueWithDataset(){
    if(!file) { setStatusMessage('No file to continue'); return }
    if(!selectedDataset) { setStatusMessage('Choose a dataset first'); return }
    setStatusMessage('Uploading with selected dataset…')
    try{
      const fd = new FormData()
      fd.append('file', file)
      fd.append('dataset_key', selectedDataset)
      const j = await dataHubUpload(fd, true)
      const jid = j && (j.run_id || j.runId || j.run_id || j.id)
      setJobId(jid || null)
      setNeedsDataset(null)
      const previewRows = j && (j.preview_rows || j.preview || j.previewRows)
      if(previewRows && Array.isArray(previewRows)){
        setPreview(previewRows)
        const cols = previewRows.length>0 ? Object.keys(previewRows[0]) : []
        setColumns(cols)
        setStatusMessage(`Preview ready — ${previewRows.length} rows`)
      } else {
        setStatusMessage('Upload complete — preview not available')
      }
      try{ const runsResp = await dataHubListRuns(); setRuns(runsResp || []) }catch(e){}
    }catch(e){ setStatusMessage('Upload error: ' + String(e)) }
  }

  

  async function refreshRunDetail(runId){
    try{
      const detail = await dataHubGetRun(runId)
      return detail
    }catch(e){ return null }
  }

  async function handleValidate(){
    if(!jobId){ setStatusMessage('No job to validate'); return }
    setStatusMessage('Validating…')
    try{
      const res = await fetch(`/api/v2/datahub/runs/${encodeURIComponent(jobId)}/validate`, { method: 'POST' })
      let body = null
      try{ body = await res.json() }catch(e){ body = null }
      if(!res.ok){ setStatusMessage('Validate error: ' + (body && (body.error || body.message) ? (body.error || body.message) : 'validate failed')); return }
      setValidResult(body)
      setStatusMessage(`Validation complete — errors: ${body && body.errors ? body.errors : 0}`)
    }catch(err){ setStatusMessage('Validate error: ' + String(err)) }
  }

  async function handleCommit(){
    if(!jobId){ setStatusMessage('No job to commit'); return }
    setStatusMessage('Committing…')
    setAnalyticsStatus(null)
    try{
      // call v2 commit endpoint which will process the previously uploaded file
      const res = await fetch(`/api/v2/datahub/runs/${encodeURIComponent(jobId)}/commit`, { method: 'POST' })
      let body = null
      try{ body = await res.json() }catch(e){ body = null }
      if(!res.ok){
        setStatusMessage('Commit error: ' + (body && (body.error || body.message) ? (body.error || body.message) : 'commit failed'))
        return
      }
      setCommitResult(body)
      setCommitResult(body)
      setCommitResult(body)
      setPostCommitInfo(body)
      try{
        sessionStorage.setItem('datahub_last_commit', JSON.stringify(body))
      }catch(e){}
      setStatusMessage(`Commit complete — imported: ${body.rows_loaded || 0}`)
      // determine destination workspace based on dataset_key
      try{
        const dk = (body && (body.dataset_key || body.datasetKey || body.dataset)) ? (body.dataset_key || body.datasetKey || body.dataset) : null
        let dest = null
        if(dk){
          const lower = dk.toLowerCase()
          if(lower.includes('school') || lower.includes('school_program') || lower.includes('school_program_fact') || lower.includes('rsid')) dest = '/planning/targeting-board'
          else if(lower.includes('market') || lower.includes('market_potential') || lower.includes('market_health')) dest = '/command-center'
          else if(lower.includes('mission') || lower.includes('mission_allocation')) dest = '/command-center/mission-assessment'
          else if(lower.includes('event') || lower.includes('emm') || lower.includes('marketing')) dest = '/roi'
          else dest = null
        }
        setDestinationPath(dest)
      }catch(e){ setDestinationPath(null) }

      // kick off a lightweight analytics check: poll the expected endpoint until results appear or timeout
      (async function pollAnalytics(){
        setAnalyticsStatus('pending')
        const max = 6
        let ok = false
        for(let i=0;i<max;i++){
          try{
            if(destinationPath === '/planning/targeting-board'){
              const r = await fetch('/api/v2/targeting/schools')
              const j = await r.json()
              if(j && Array.isArray(j.schools) && j.schools.length>0){ ok = true; break }
            } else if(destinationPath === '/command-center'){
              const r = await fetch('/api/command-center/overview')
              const j = await r.json()
              if(j && j.summary) { ok = true; break }
            } else if(destinationPath === '/command-center/mission-assessment'){
              const r = await fetch('/api/v2/mission-allocation/runs')
              const j = await r.json()
              if(j && j.status === 'ok') { ok = true; break }
            } else if(destinationPath === '/roi'){
              const r = await fetch('/api/v2/roi/kpis')
              if(r && r.ok){ ok = true; break }
            } else {
              // unknown destination: consider analytics done
              ok = true; break
            }
          }catch(e){}
          await new Promise(res=>setTimeout(res, 1000))
        }
        setAnalyticsStatus(ok ? 'done' : 'failed')
        // reflect analytics status into the post-commit card if present
        setPostCommitInfo(prev => prev ? Object.assign({}, prev, { analytics_check: ok ? 'done' : 'failed' }) : prev)
      })()
    }catch(err){ setStatusMessage('Commit error: ' + (err && err.message ? err.message : String(err))) }
  }

  return (
    <div style={{padding:24}}>
      <h2>Data Hub — Imports</h2>
      <p>Centralized importer registry and upload workflow.</p>

      <section style={{marginBottom:24}}>
        <h3>Upload a file</h3>
        {canUpload ? (
          <form onSubmit={handleUpload}>
            <input type="file" onChange={e => setFile(e.target.files && e.target.files[0])} />
            <button type="submit" style={{marginLeft:8}}>Upload & Preview</button>
          </form>
        ) : (
          <div>Uploads are restricted. You do not have permission to upload to the Data Hub.</div>
        )}
        {statusMessage && <div style={{marginTop:8}}><strong>{statusMessage}</strong></div>}
        {jobId && <div style={{marginTop:8}}>Job ID: {jobId} {legacyJobId && <em>(legacy {legacyJobId})</em>}</div>}
        {needsDataset && (
          <div style={{marginTop:12, padding:8, border:'1px dashed #ccc'}}>
            <div><strong>Dataset selection required</strong> — suggested: {needsDataset.suggested || '(none)'} (confidence: {needsDataset.confidence || 0})</div>
            <div style={{marginTop:8}}>
              <select value={selectedDataset} onChange={e=>setSelectedDataset(e.target.value)}>
                <option value=''>-- choose dataset --</option>
                {importers.map(i=> <option key={i.dataset_key||i.id} value={i.dataset_key||i.id}>{i.display_name||i.dataset_key||i.id}</option>)}
              </select>
              <button onClick={continueWithDataset} style={{marginLeft:8}}>Use selected dataset and continue</button>
            </div>
          </div>
        )}
        <div style={{marginTop:8}}>
          <button onClick={handleValidate} disabled={!jobId}>Validate</button>
          <button onClick={handleCommit} disabled={!jobId} style={{marginLeft:8}}>Commit</button>
        </div>
        {/* Simple workflow step labels */}
        <div style={{marginTop:12, display:'flex', gap:12, alignItems:'center'}}>
          {[
            {key:'file', label:'File selected', ok: !!file},
            {key:'preview', label:'Preview ready', ok: preview && preview.length>0},
            {key:'dataset', label:'Dataset confirmed', ok: !!selectedDataset},
            {key:'validation', label:'Validation complete', ok: validResult && (validResult.errors ? validResult.errors.length===0 : true)},
            {key:'commit', label:'Commit complete', ok: commitResult != null}
          ].map(s => (
            <div key={s.key} style={{padding:'6px 10px', borderRadius:6, background: s.ok ? '#e6ffed' : '#fafafa', border: '1px solid #ddd'}}>
              <strong style={{color: s.ok ? '#007a2f' : '#333'}}>{s.ok ? '✓ ' : ''}{s.label}</strong>
            </div>
          ))}
        </div>
      </section>
      {/* Inline run detail (replaces alert popup) */}
      {expandedRunId && runDetailsMap && runDetailsMap[expandedRunId] && (
        <section style={{marginTop:12, padding:12, border:'1px solid #e0e0e0', borderRadius:6}}>
          <h3 style={{marginTop:0}}>Run Details — {expandedRunId}</h3>
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:8}}>
            {Object.entries(runDetailsMap[expandedRunId]).map(([k,v]) => (
              <div key={k} style={{padding:6, borderBottom:'1px solid #fafafa'}}>
                <strong style={{display:'block'}}>{k}</strong>
                <div style={{fontSize:12, color:'#333'}}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</div>
              </div>
            ))}
          </div>
          <div style={{marginTop:8}}>
            <button onClick={()=>setExpandedRunId(null)}>Close</button>
          </div>
        </section>
      )}
      {/* Post-commit success panel */}
      {postCommitInfo && (
        <section style={{marginBottom:24, padding:16, border:'1px solid #cfeadf', background:'#f4fffa', borderRadius:6}}>
          <h3 style={{marginTop:0}}>Import Success</h3>
          <div><strong>Dataset:</strong> {postCommitInfo.dataset_key || postCommitInfo.dataset || 'unknown'}</div>
          <div><strong>Rows loaded:</strong> {postCommitInfo.rows_loaded || 0}</div>
          <div><strong>Run ID:</strong> {postCommitInfo.run_id || postCommitInfo.id}</div>
          <div><strong>Commit status:</strong> {postCommitInfo.status || 'committed'}</div>
          <div><strong>Analytics check:</strong> {postCommitInfo.analytics_check || analyticsStatus || 'pending'}</div>
          <div><strong>Timestamp:</strong> {postCommitInfo.committed_at || postCommitInfo.finished_at || postCommitInfo.created_at || ''}</div>
          <div style={{marginTop:8}}>
            <button onClick={async ()=>{
              const rid = postCommitInfo.run_id || postCommitInfo.id
              if(!rid) return
              const d = await refreshRunDetail(rid)
              if(d){ setRunDetailsMap(m => Object.assign({}, m, { [rid]: d })); setExpandedRunId(rid) }
            }}>Inspect run</button>
            {destinationPath && <a style={{marginLeft:8}} href={destinationPath}>Go to destination</a>}
          </div>
        </section>
      )}
      {validResult && validResult.errors && Array.isArray(validResult.errors) && (
        <section style={{marginBottom:24}}>
          <h3>Upload Validation — Errors</h3>
          <div style={{overflowX:'auto'}}>
            <table style={{width:'100%', borderCollapse:'collapse'}}>
              <thead>
                <tr>
                  <th style={{padding:6}}>row_num</th>
                  <th style={{padding:6}}>column_name</th>
                  <th style={{padding:6}}>error_code</th>
                  <th style={{padding:6}}>message</th>
                </tr>
              </thead>
              <tbody>
                {validResult.errors.map((err, idx) => (
                  <tr key={idx}>
                    <td style={{padding:6}}>{err.row_num || err.row || ''}</td>
                    <td style={{padding:6}}>{err.column_name || err.column || ''}</td>
                    <td style={{padding:6}}>{err.error_code || err.code || ''}</td>
                    <td style={{padding:6}}>{err.message || err.msg || JSON.stringify(err)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section style={{marginBottom:24}}>
        <h3>Preview</h3>
        {columns.length === 0 && preview.length === 0 && <div>No preview available.</div>}
        {columns.length > 0 && (
          <div style={{overflowX:'auto'}}>
            <table style={{borderCollapse:'collapse', width:'100%'}}>
              <thead>
                <tr>
                  {columns.map(c => <th key={c} style={{border:'1px solid #ddd', padding:6, textAlign:'left'}}>{c}</th>)}
                </tr>
              </thead>
              <tbody>
                {preview.map((r, idx) => (
                  <tr key={idx}>
                    {columns.map(c => <td key={c} style={{border:'1px solid #eee', padding:6}}>{String((r && r[c]) || '')}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <h3>Available Importers</h3>
      {loading && <div>Loading importers…</div>}
      {!loading && importers.length === 0 && <div>No importers found.</div>}
      <ul>
        {importers.map(i => (
          <li key={i.dataset_key || i.id} style={{marginBottom:8}}>
            <strong>{i.display_name || i.displayName || i.dataset_key || i.id}</strong> — <em>{i.source_system || i.sourceSystem}</em>
          </li>
        ))}
      </ul>

      <section style={{marginTop:24}}>
        <h3>Recent Runs</h3>
        {runs.length === 0 && <div>No recent runs.</div>}
        {runs.length > 0 && (
          <table style={{width:'100%', borderCollapse:'collapse'}}>
            <thead>
              <tr>
                <th>run_id</th><th>dataset_key</th><th>status</th><th>rows_in</th><th>rows_loaded</th><th>error_summary</th><th>actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.run_id}>
                  <td style={{padding:6}}>{r.run_id}</td>
                  <td style={{padding:6}}>{r.dataset_key}</td>
                  <td style={{padding:6}}>{r.status}</td>
                  <td style={{padding:6}}>{r.rows_in}</td>
                  <td style={{padding:6}}>{r.rows_loaded}</td>
                  <td style={{padding:6}}>{r.error_summary}</td>
                  <td style={{padding:6}}>
                    <button onClick={async ()=>{
                      const d = await refreshRunDetail(r.run_id)
                      if(d){
                        setRunDetailsMap(m => Object.assign({}, m, { [r.run_id]: d }))
                        setExpandedRunId(r.run_id)
                      }
                    }}>View</button>
                    {r.error_summary && <a style={{marginLeft:8}} href={dataHubDownloadErrors(r.run_id)}>Download Errors</a>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
