import React, {useState, useEffect} from 'react'
import { Button, Box, Typography, Paper, TextField, Stepper, Step, StepLabel, Grid, FormControl, InputLabel, Select, MenuItem, Chip } from '@mui/material'
import client, { uploadImport, parseImport, getImport, mapImport, validateImport, commitImport } from '../api/client'

export default function ImportCenterPage(){
  const [file, setFile] = useState<File | null>(null)
  const [jobId, setJobId] = useState<number | null>(null)
  const [preview, setPreview] = useState<any[]>([])
  const [columns, setColumns] = useState<string[]>([])
  const [mapping, setMapping] = useState<string>('{}')
  const [logs, setLogs] = useState<any[]>([])
  const [status, setStatus] = useState<string>('idle')
  const [activeStep, setActiveStep] = useState<number>(0)

  const steps = ['Upload','Preview','Map','Validate','Commit']

  async function handleUpload(e:any){
    const f = e.target.files && e.target.files[0]
    if (!f) return
    setFile(f)
    const fd = new FormData()
    fd.append('file', f)
    setStatus('uploading')
    const res = await uploadImport(fd)
    setJobId(res.import_job_id)
    setStatus('uploaded')
    setActiveStep(1)
  }

  async function handleParse(){
    if (!jobId) return
    setStatus('parsing')
    try{
      await parseImport(jobId)
      const full = await getImport(jobId)
      setPreview(full.preview || [])
      setColumns(full.columns || [])
      setLogs(full.logs || [])
      setStatus('preview_ready')
      setActiveStep(2)
    } catch(e){
      setStatus('parse_failed')
      console.error(e)
    }
  }

  // mapping fields state for nicer UI (source -> target)
  const [mappingFields, setMappingFields] = useState<Record<string,string>>({})

  // sync mapping JSON from mappingFields
  function syncMappingJsonFromFields(){
    const fm: Record<string,string> = {}
    Object.keys(mappingFields).forEach(k => { if (mappingFields[k]) fm[k] = mappingFields[k] })
    const obj = { target_domain: 'generic', field_map: fm, created_by: 'ui' }
    setMapping(JSON.stringify(obj, null, 2))
  }

  // when mapping JSON changes, update mappingFields for the editor
  function syncFieldsFromMappingJson(){
    try{
      const obj = JSON.parse(mapping)
      const fm = obj.field_map || {}
      setMappingFields(fm)
    } catch(e){
      // ignore parse errors
    }
  }

  function handleFieldChange(src:string, val:string){
    setMappingFields(prev => ({...prev, [src]: val}))
  }

  useEffect(()=>{
    // when columns change, initialize mappingFields for nicer UX
    const init: Record<string,string> = {}
    columns.forEach(c => { init[c] = mappingFields[c] || '' })
    setMappingFields(init)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [columns.join('|')])

  function autoMap(){
    const fm:any = {}
    columns.forEach(c => { fm[c] = c })
    const obj = { target_domain: 'generic', field_map: fm, created_by: 'ui_auto' }
    setMapping(JSON.stringify(obj, null, 2))
  }

  async function handleMap(){
    if (!jobId) return
    let mappingObj = {}
    try{ mappingObj = JSON.parse(mapping) } catch(e){ alert('Mapping must be valid JSON'); return }
    const res = await mapImport(jobId, mappingObj)
    setStatus(res.status || 'mapping_saved')
    setActiveStep(3)
  }

  async function handleValidate(){
    if (!jobId) return
    setStatus('validating')
    const res = await validateImport(jobId)
    const full = await getImport(jobId)
    setLogs(full.logs || [])
    setStatus(res.errors>0 ? 'validation_failed' : 'ready_to_commit')
    setActiveStep(4)
  }

  async function handleCommit(){
    if (!jobId) return
    setStatus('committing')
    const res = await commitImport(jobId)
    setStatus('completed')
    setActiveStep(4)
    alert(`Imported ${res.imported} rows`)
  }

  return (
    <Box sx={{p:3}}>
      <Typography variant="h5">Import Center</Typography>

      <Box sx={{mt:2}}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((s)=> (
            <Step key={s}><StepLabel>{s}</StepLabel></Step>
          ))}
        </Stepper>
      </Box>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Step 1 — Upload</Typography>
        <input data-testid="file-input" type="file" onChange={handleUpload} />
        <div style={{marginTop:12}}>
          <Button variant="contained" onClick={handleParse} disabled={!jobId}>Parse & Preview</Button>
        </div>
      </Paper>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Step 2 — Preview</Typography>
        {preview && preview.length>0 ? (
          <div style={{maxHeight:300, overflow:'auto'}}>
            <table style={{width:'100%', borderCollapse:'collapse'}}>
              <thead>
                <tr>{columns.map((c)=> <th key={c} style={{border:'1px solid #eee', padding:6}}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {preview.map((r, i)=> (
                  <tr key={i}>{columns.map((c)=> <td key={c} style={{border:'1px solid #f6f6f6', padding:6}}>{String(r[c] ?? '')}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (<div>No preview available</div>)}
      </Paper>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Step 3 — Map Columns</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField label="Mapping JSON" value={mapping} onChange={(e)=>setMapping(e.target.value)} multiline rows={6} fullWidth />
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="body2">Quick mapping tools</Typography>
            <Box sx={{mt:1}}>
              <Button variant="outlined" onClick={autoMap} sx={{mr:1}}>Auto-map same-name</Button>
              <Button variant="outlined" onClick={syncFieldsFromMappingJson} sx={{mr:1}}>Sync JSON → fields</Button>
              <Button variant="outlined" onClick={syncMappingJsonFromFields} sx={{mr:1}}>Apply fields → JSON</Button>
              <Button variant="contained" onClick={handleMap} disabled={!jobId}>Save Mapping</Button>
            </Box>
            <Box sx={{mt:2}}>
              <Typography variant="caption">Columns detected:</Typography>
              <div style={{marginTop:6}}>
                {columns.map(c=> <Chip key={c} label={c} style={{marginRight:6, marginBottom:6}} />)}
              </div>
            </Box>

            {columns.length>0 && (
              <Box sx={{mt:2}}>
                <Typography variant="caption">Per-column mapping (source → target field)</Typography>
                <div style={{marginTop:8}}>
                  {columns.map(src => (
                    <Box key={src} sx={{display:'flex', alignItems:'center', gap:1, mb:1}}>
                      <Chip label={src} />
                      <TextField placeholder="target field" size="small" value={mappingFields[src] || ''} onChange={(e)=>handleFieldChange(src, e.target.value)} />
                    </Box>
                  ))}
                </div>
              </Box>
            )}
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Step 4 — Validate & Commit</Typography>
        <Box sx={{mt:1}}>
          <Button variant="contained" onClick={handleValidate} disabled={!jobId}>Validate</Button>
          <Button variant="contained" onClick={handleCommit} disabled={!jobId} sx={{ml:2}}>Commit</Button>
        </Box>
        <Box sx={{mt:2}}>
          <Typography variant="subtitle2">Logs</Typography>
          <div style={{maxHeight:200, overflow:'auto', background:'#fff', padding:8}}>
            {logs.map((l, i)=> <div key={i}>{l.created_at} [{l.level}] {l.message} {l.field_name?`(${l.field_name})`:''}</div>)}
          </div>
        </Box>
      </Paper>
    </Box>
  )
}

