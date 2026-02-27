import React, {useEffect, useState} from 'react'
import { getMe } from '../../api/client'

export default function DataHubImports(){
  const [importers, setImporters] = useState([])
  const [loading, setLoading] = useState(true)

  // Upload flow state
  const [file, setFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [legacyJobId, setLegacyJobId] = useState(null)
  const [preview, setPreview] = useState([])
  const [columns, setColumns] = useState([])
  const [statusMessage, setStatusMessage] = useState(null)
  const [validResult, setValidResult] = useState(null)
  const [commitResult, setCommitResult] = useState(null)
  const [canUpload, setCanUpload] = useState(false)

  useEffect(()=>{
    let mounted = true
    fetch('/api/v1/importers')
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(j => { if(mounted) setImporters(j.importers || []) })
      .catch(()=>{ if(mounted) setImporters([]) })
      .finally(()=>{ if(mounted) setLoading(false) })
    return ()=>{ mounted = false }
  },[])

  useEffect(()=>{
    let canceled = false
    getMe().then((me)=>{
      if(canceled) return
      if(me && me.permissions && me.permissions['datahub.upload']) setCanUpload(true)
    }).catch(()=>{} )
    return ()=>{ canceled = true }
  },[])

  async function handleUpload(e){
    e.preventDefault()
    setStatusMessage('Uploading…')
    setJobId(null); setPreview([]); setColumns([]); setValidResult(null); setCommitResult(null)
    if(!file){ setStatusMessage('Choose a file first'); return }
    try{
      const fd = new FormData()
      fd.append('file', file)
      // optional: uploaded_by/current user will be inferred in dev
      const res = await fetch('/api/import/upload', { method: 'POST', body: fd })
      if(!res.ok){ throw new Error('upload failed') }
      const j = await res.json()
      setJobId(j.import_job_id || j.import_job_id || j.import_job_id)
      setLegacyJobId(j.legacy_job_id || null)
      setStatusMessage('Uploaded — parsing preview…')
      // parse/preview using v3 parse endpoint
      const prs = await fetch('/api/import/parse', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ import_job_id: j.import_job_id }) })
      if(!prs.ok){
        const t = await prs.json().catch(()=>({detail:prs.statusText}))
        setStatusMessage('Parse failed: ' + (t.detail || prs.statusText))
        return
      }
      const pj = await prs.json()
      setColumns(pj.columns || [])
      setPreview(pj.preview_rows || [])
      setStatusMessage(`Preview ready — ${pj.row_count || (pj.preview_rows||[]).length} rows`)
    }catch(err){
      setStatusMessage('Upload error: ' + String(err))
    }
  }

  async function handleValidate(){
    if(!jobId){ setStatusMessage('No job to validate'); return }
    setStatusMessage('Validating…')
    try{
      const res = await fetch('/api/import/validate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ import_job_id: jobId }) })
      if(!res.ok){ throw new Error('validate failed') }
      const j = await res.json()
      setValidResult(j)
      setStatusMessage(`Validation complete — errors: ${j.errors || 0}`)
    }catch(err){ setStatusMessage('Validate error: ' + String(err)) }
  }

  async function handleCommit(){
    if(!jobId){ setStatusMessage('No job to commit'); return }
    setStatusMessage('Committing…')
    try{
      const res = await fetch('/api/import/commit', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ import_job_id: jobId }) })
      if(!res.ok){ throw new Error('commit failed') }
      const j = await res.json()
      setCommitResult(j)
      setStatusMessage(`Commit complete — imported: ${j.imported || j.committed_rows || 0}`)
    }catch(err){ setStatusMessage('Commit error: ' + String(err)) }
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
        <div style={{marginTop:8}}>
          <button onClick={handleValidate} disabled={!jobId}>Validate</button>
          <button onClick={handleCommit} disabled={!jobId} style={{marginLeft:8}}>Commit</button>
        </div>
      </section>

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
          <li key={i.id} style={{marginBottom:8}}>
            <strong>{i.displayName || i.id}</strong> — <em>{i.sourceSystem}</em>
          </li>
        ))}
      </ul>
    </div>
  )
}
