import React, { useState, useEffect } from 'react'
import { Box, Typography, Button, TextField, Paper, Table, TableHead, TableRow, TableCell, TableBody, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import * as api from '../../api/client'

export default function AdminMaintenancePage(){
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [days, setDays] = useState(90)
  const [dryRun, setDryRun] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [previewResult, setPreviewResult] = useState(null)
  const [schedules, setSchedules] = useState([])
  const [runs, setRuns] = useState([])
  const [newInterval, setNewInterval] = useState(60)

  useEffect(()=>{ loadData() }, [])

  async function loadData(){
    try{ const s = await api.listSchedules(); setSchedules(s || []) }catch(e){ console.error(e) }
    try{ const r = await api.listMaintenanceRuns(50); setRuns(r || []) }catch(e){ console.error(e) }
  }

  async function doDedupe(){
    setRunning(true); setResult(null)
    try{ const r = await api.runDeduplicate(); setResult(r); await loadData() }catch(e){ setResult({error: e.message || String(e)}) }
    setRunning(false)
  }

  async function doPurge(){
    // preview using dry-run to show impact before destructive action
    setRunning(true); setResult(null); setPreviewResult(null)
    try{
      const preview = await api.runPurge(days, true)
      setPreviewResult(preview)
      setConfirmOpen(true)
    }catch(e){ setResult({error: e.message || String(e)}) }
    setRunning(false)
  }

  async function confirmPurge(){
    setRunning(true); setResult(null)
    try{
      const r = await api.runPurge(days, false)
      setResult(r)
      setConfirmOpen(false)
      await loadData()
    }catch(e){ setResult({error: e.message || String(e)}) }
    setRunning(false)
  }

  async function createSchedule(){
    try{
      await api.createSchedule({ name: 'auto-maint', enabled: true, interval_minutes: Number(newInterval), params: { tasks: ['dedupe','purge'], days, dry_run: dryRun } })
      await loadData()
    }catch(e){ console.error(e) }
  }

  async function trigger(id){
    try{ const r = await api.triggerSchedule(id); setResult(r); await loadData() }catch(e){ setResult({error: e.message || String(e)}) }
  }

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h5">Maintenance</Typography>
      <Typography variant="body2" sx={{ mb:2 }}>Run deduplication and archived purge tasks. Create schedules to run periodically.</Typography>

      <Paper sx={{ p:2, mb:2 }}>
        <Button variant="contained" color="primary" onClick={doDedupe} disabled={running}>Run Deduplicate</Button>
        <Box component="span" sx={{ ml:2 }}>
          <TextField size="small" label="Purge days" type="number" value={days} onChange={e=>setDays(Number(e.target.value))} sx={{ width:120 }} />
          <label style={{ marginLeft: 12, display: 'inline-flex', alignItems: 'center' }}>
            <input type="checkbox" checked={dryRun} onChange={e=>setDryRun(e.target.checked)} />
            <span style={{ marginLeft: 6 }}>Dry run</span>
          </label>
          <Button variant="contained" color="error" sx={{ ml:2 }} onClick={doPurge} disabled={running}>Purge Archived</Button>
        </Box>
      </Paper>

      <Paper sx={{ p:2, mb:2 }}>
        <Typography variant="h6">Create Schedule</Typography>
        <Box sx={{ mt:1 }}>
          <TextField size="small" label="Interval (min)" type="number" value={newInterval} onChange={e=>setNewInterval(Number(e.target.value))} sx={{ width:140 }} />
          <Button variant="contained" sx={{ ml:2 }} onClick={createSchedule}>Create</Button>
        </Box>
      </Paper>

      <Paper sx={{ p:2, mb:2 }}>
        <Typography variant="h6">Schedules</Typography>
        <Table size="small">
          <TableHead><TableRow><TableCell>ID</TableCell><TableCell>Name</TableCell><TableCell>Enabled</TableCell><TableCell>Interval</TableCell><TableCell>Last run</TableCell><TableCell>Actions</TableCell></TableRow></TableHead>
          <TableBody>
            {schedules.map(s=> (
              <TableRow key={s.id}><TableCell>{s.id}</TableCell><TableCell>{s.name}</TableCell><TableCell>{s.enabled}</TableCell><TableCell>{s.interval_minutes}</TableCell><TableCell>{s.last_run_at}</TableCell><TableCell><Button size="small" onClick={()=>trigger(s.id)}>Trigger</Button></TableCell></TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ p:2 }}>
        <Typography variant="h6">Recent Runs</Typography>
        <Table size="small">
          <TableHead><TableRow><TableCell>ID</TableCell><TableCell>Schedule</TableCell><TableCell>Type</TableCell><TableCell>Started</TableCell><TableCell>Finished</TableCell><TableCell>Result</TableCell></TableRow></TableHead>
          <TableBody>
            {runs.map(r=> (
              <TableRow key={r.id}><TableCell>{r.id}</TableCell><TableCell>{r.schedule_id}</TableCell><TableCell>{r.run_type}</TableCell><TableCell>{r.started_at}</TableCell><TableCell>{r.finished_at}</TableCell><TableCell><pre style={{ whiteSpace:'pre-wrap', maxHeight:100, overflow:'auto' }}>{r.result_json}</pre></TableCell></TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ p:2, mt:2 }}>
        <Typography variant="subtitle1">Result</Typography>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{result ? JSON.stringify(result, null, 2) : 'No result yet'}</pre>
      </Paper>

      <Dialog open={confirmOpen} onClose={()=>setConfirmOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Purge Preview</DialogTitle>
        <DialogContent>
          <Typography variant="body2">This is a dry-run preview of rows that would be deleted. Confirm to execute the purge.</Typography>
          <pre style={{ whiteSpace: 'pre-wrap', maxHeight: 300, overflow: 'auto' }}>{previewResult ? JSON.stringify(previewResult, null, 2) : 'No preview available'}</pre>
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setConfirmOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={confirmPurge} disabled={running}>Confirm Purge</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
