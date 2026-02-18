import React, { useState, useEffect } from 'react'
import { Box, Typography, Stepper, Step, StepLabel, Button, Paper, CircularProgress, TextField, Select, MenuItem, FormControl, InputLabel, Table, TableHead, TableRow, TableCell, TableBody, Divider } from '@mui/material'
import * as api from '../api/client'

const steps = ['Upload', 'Preview', 'Map', 'Validate', 'Commit']

export default function ImportCenterPage(){
  const [active, setActive] = useState(0)
  const [file, setFile] = useState(null)
  const [job, setJob] = useState(null)
  const [preview, setPreview] = useState([])
  const [columns, setColumns] = useState([])
  const [mapping, setMapping] = useState({})
  const [mapErrors, setMapErrors] = useState(null)
  const [datasetKey, setDatasetKey] = useState('production')
  const [sourceSystem, setSourceSystem] = useState('manual')
  const [status, setStatus] = useState('')
  const [errors, setErrors] = useState([])
  const [jobs, setJobs] = useState([])
  const [committedRows, setCommittedRows] = useState(null)

  useEffect(()=>{ loadJobs() }, [])

  async function loadJobs(){
    try{ const list = await api.importJobs(); setJobs(list || []) }catch(e){ console.error(e) }
  }

  function onFileChange(e){ setFile(e.target.files && e.target.files[0]) }

  async function doUpload(){
    if(!file) return
    const fd = new FormData()
    fd.append('file', file)
    const res = await api.importUpload(fd)
    setJob(res.import_job_id || res.import_job_id)
    setStatus('uploaded')
    setActive(1)
  }

  async function doParse(){
    if(!job) return
    setStatus('parsing')
    const res = await api.importParse(job)
    setPreview(res.preview_rows || [])
    setColumns(res.columns || [])
    setStatus('parsed')
    setActive(2)
  }

  async function doMap(){
    if(!job) return
    // client-side validation: ensure required fields mapped
    let required = []
    if(datasetKey === 'production') required = ['org_unit_id','date_key','metric_key','metric_value']
    if(datasetKey === 'marketing') required = ['date_key','org_unit_id']
    if(datasetKey === 'event_performance') required = ['event_id']
    const missing = required.filter(f=> !mapping || !mapping[f])
    if(missing.length){
      setMapErrors('Missing mappings: ' + missing.join(', '))
      return
    }
    setMapErrors(null)
    await api.importMap(job, mapping, datasetKey, sourceSystem, null)
    setStatus('mapped')
    setActive(4)
  }

  async function doValidate(){
    if(!job) return
    setStatus('validating')
    const res = await api.importValidate(job)
    setErrors(res.sample_errors || [])
    setStatus('validated')
  }

  async function doCommit(mode){
    if(!job) return
    setStatus('committing')
    const res = await api.importCommit(job, mode)
    setCommittedRows(res.committed_rows || 0)
    setStatus('committed')
    loadJobs()
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Import Center</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary' }}>Upload files, map columns, validate, and commit to the data warehouse.</Typography>

      <Box sx={{ mt:3 }}>
        <Stepper activeStep={active} alternativeLabel>
          {steps.map(s=> (
            <Step key={s}><StepLabel>{s}</StepLabel></Step>
          ))}
        </Stepper>

        <Paper sx={{ mt:2, p:2, bgcolor:'background.paper' }}>
          {active===0 && (
            <Box>
              <input type="file" onChange={onFileChange} />
              <Box sx={{ mt:2 }}>
                <Button variant="contained" onClick={doUpload} disabled={!file}>Upload</Button>
              </Box>
            </Box>
          )}

          {active===1 && (
            <Box>
              <Typography>Uploaded job: {job}</Typography>
              <Box sx={{ mt:2 }}>
                <Button variant="contained" onClick={doParse}>Parse & Preview</Button>
              </Box>
            </Box>
          )}

          {active===2 && (
            <Box>
              <Typography>Parsed preview</Typography>
              <Divider sx={{ my:1 }} />
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {columns.map(c=> <TableCell key={c}>{c}</TableCell>)}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {preview.slice(0,20).map((r, idx)=> (
                    <TableRow key={idx}>{columns.map(c=> <TableCell key={c}>{String(r[c]||'')}</TableCell>)}</TableRow>
                  ))}
                </TableBody>
              </Table>
              <Box sx={{ mt:2 }}>
                <FormControl size="small" sx={{ minWidth:200 }}>
                  <InputLabel>Dataset</InputLabel>
                  <Select value={datasetKey} label="Dataset" onChange={e=>setDatasetKey(e.target.value)}>
                    <MenuItem value="production">production</MenuItem>
                    <MenuItem value="marketing">marketing</MenuItem>
                    <MenuItem value="org_units">org_units</MenuItem>
                    <MenuItem value="event_performance">event_performance</MenuItem>
                  </Select>
                </FormControl>
                <Button variant="contained" sx={{ ml:2 }} onClick={()=>setActive(3)}>Go to Map</Button>
              </Box>
            </Box>
          )}

          {active===3 && (
            <Box>
              <Typography>Map fields</Typography>
              <Box sx={{ mt:1 }}>
                <Typography variant="body2">Map source columns to target dataset fields</Typography>
                <Box sx={{ mt:1 }}>
                  {(datasetKey === 'production') && (
                    <Box>
                      {['org_unit_id','date_key','metric_key','metric_value'].map(f=> (
                        <FormControl key={f} size="small" sx={{ minWidth:240, mr:2, mt:1 }}>
                          <InputLabel>{f}</InputLabel>
                          <Select value={mapping[f] || ''} label={f} onChange={e=>setMapping(Object.assign({}, mapping, {[f]: e.target.value}))}>
                            <MenuItem value="">(none)</MenuItem>
                            {columns.map(c=> <MenuItem key={c} value={c}>{c}</MenuItem>)}
                          </Select>
                        </FormControl>
                      ))}
                    </Box>
                  )}
                  {(datasetKey === 'marketing') && (
                    <Box>
                      {['date_key','org_unit_id','campaign','channel','impressions','engagements','clicks','conversions','cost'].map(f=> (
                        <FormControl key={f} size="small" sx={{ minWidth:240, mr:2, mt:1 }}>
                          <InputLabel>{f}</InputLabel>
                          <Select value={mapping[f] || ''} label={f} onChange={e=>setMapping(Object.assign({}, mapping, {[f]: e.target.value}))}>
                            <MenuItem value="">(none)</MenuItem>
                            {columns.map(c=> <MenuItem key={c} value={c}>{c}</MenuItem>)}
                          </Select>
                        </FormControl>
                      ))}
                    </Box>
                  )}
                  {(datasetKey === 'event_performance') && (
                    <Box>
                      {['event_id','impressions','engagements','captured_at'].map(f=> (
                        <FormControl key={f} size="small" sx={{ minWidth:240, mr:2, mt:1 }}>
                          <InputLabel>{f}</InputLabel>
                          <Select value={mapping[f] || ''} label={f} onChange={e=>setMapping(Object.assign({}, mapping, {[f]: e.target.value}))}>
                            <MenuItem value="">(none)</MenuItem>
                            {columns.map(c=> <MenuItem key={c} value={c}>{c}</MenuItem>)}
                          </Select>
                        </FormControl>
                      ))}
                    </Box>
                  )}
                </Box>
                <Box sx={{ mt:2 }}>
                  <Button variant="contained" onClick={doMap} disabled={!!mapErrors}>Save Mapping</Button>
                  {mapErrors && <Typography color="error" sx={{ mt:1 }}>{mapErrors}</Typography>}
                </Box>
              </Box>
            </Box>
          )}

          {active===4 && (
            <Box>
              <Typography>Validate & Commit</Typography>
              <Box sx={{ mt:2 }}>
                <Button variant="contained" onClick={async ()=>{ await doValidate(); }}>Validate</Button>
                <Button variant="contained" color="secondary" sx={{ ml:2 }} onClick={()=>doCommit('append')}>Commit (append)</Button>
                <Button variant="contained" color="error" sx={{ ml:2 }} onClick={()=>doCommit('replace')}>Commit (replace)</Button>
                <Button variant="contained" color="warning" sx={{ ml:2 }} onClick={()=>doCommit('replace-scope')}>Commit (replace-scope)</Button>
              </Box>
              <Box sx={{ mt:2 }}>
                <Typography>Errors</Typography>
                <Table size="small">
                  <TableHead><TableRow><TableCell>Row</TableCell><TableCell>Field</TableCell><TableCell>Message</TableCell></TableRow></TableHead>
                  <TableBody>
                    {errors.map((e, i)=> (<TableRow key={i}><TableCell>{e.row}</TableCell><TableCell>{e.field}</TableCell><TableCell>{e.message}</TableCell></TableRow>))}
                  </TableBody>
                </Table>
              </Box>
              {committedRows!==null && <Typography sx={{ mt:2 }}>{committedRows} rows committed.</Typography>}
            </Box>
          )}
        </Paper>

        <Paper sx={{ mt:3, p:2, bgcolor:'background.paper' }}>
          <Typography variant="h6">Import History</Typography>
          <Table size="small">
            <TableHead><TableRow><TableCell>ID</TableCell><TableCell>Dataset</TableCell><TableCell>Status</TableCell><TableCell>Rows</TableCell></TableRow></TableHead>
            <TableBody>
              {jobs.map(j=> (<TableRow key={j.id}><TableCell>{j.id}</TableCell><TableCell>{j.dataset_key}</TableCell><TableCell>{j.status}</TableCell><TableCell>{j.row_count}</TableCell></TableRow>))}
            </TableBody>
          </Table>
        </Paper>

      </Box>
    </Box>
  )
}

