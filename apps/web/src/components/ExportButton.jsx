import React, { useState } from 'react'
import { Button, Dialog, DialogTitle, DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText, FormGroup, FormControlLabel, Tooltip } from '@mui/material'
import { createExport } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useLocation } from 'react-router-dom'

const profiles = [
  { key: 'commander_packet', label: 'Commander Packet (ZIP)', include: ['manifest','table','underlying'] },
  { key: 'brief_pdf', label: 'Brief PDF', include: ['manifest'] },
  { key: 'dashboard_png', label: 'Dashboard PNG', include: ['manifest'] },
  { key: 'table_csv', label: 'Table CSV', include: ['table'] },
  { key: 'underlying_csv', label: 'Underlying CSV', include: ['underlying'] },
  { key: 'raw_csv', label: 'Raw Ingest CSV', include: ['raw'] },
]

export default function ExportButton(){
  const [open, setOpen] = useState(false)
  const [profile, setProfile] = useState('commander_packet')
  const { hasPerm } = useAuth()
  const loc = useLocation()
  const canRaw = (hasPerm && (hasPerm('datahub.runs.view') || hasPerm('datahub.view_runs') || hasPerm('datahub.runs.view'))) || false
  const canExport = (hasPerm && (hasPerm('export.any') || hasPerm('EXPORT_DATA') || hasPerm('*'))) || false

  const onConfirm = async () => {
    const p = profiles.find(x=>x.key===profile)
    const include = p.include.filter(k => k !== 'raw' || canRaw)
    const payload = {
      scope: { unit_rsid: localStorage.getItem('taaip:selected_unit') || null },
      source: { page: loc.pathname, dashboard_key: loc.pathname.replace(/\//g,'_').substring(1) || 'dashboard' },
      format: { include: include, bundle: profile==='commander_packet' },
      options: { filters: {} },
      render: { theme: 'taaip_dark' }
    }
    try{
      // Table CSV is handled client-side
      if(profile === 'table_csv'){
        exportVisibleTableToCsv()
        setOpen(false)
        return
      }
      if(profile === 'raw_csv' && !canRaw){
        window.alert('Raw exports are not permitted for your account')
        return
      }
      const res = await createExport(payload)
      window.alert(`Export requested: ${res.export_id}`)
    }catch(e){
      window.alert('Export request failed')
    }
    setOpen(false)
  }

  function exportVisibleTableToCsv(){
    try{
      const table = document.querySelector('table')
      if(!table) return window.alert('No table found on this page to export')
      const rows = Array.from(table.querySelectorAll('tr'))
      const csvRows = rows.map(r => {
        const cells = Array.from(r.querySelectorAll('th,td'))
        return cells.map(c => '"'+String(c.innerText).replace(/"/g,'""')+'"').join(',')
      })
      const csv = csvRows.join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'table_export.csv'
      a.click()
      URL.revokeObjectURL(url)
    }catch(e){ console.error(e); window.alert('Export failed') }
  }

  return (
    <>
      {canExport ? (
        <Button variant="outlined" size="small" onClick={()=>setOpen(true)}>Export</Button>
      ) : (
        <Tooltip title="Export restricted">
          <Button variant="outlined" size="small" onClick={()=>window.alert('You do not have export permission')}>Export</Button>
        </Tooltip>
      )}
      <Dialog open={open} onClose={()=>setOpen(false)}>
        <DialogTitle>Export</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt:1 }}>
            <InputLabel id="export-profile-label">Profile</InputLabel>
            <Select labelId="export-profile-label" value={profile} label="Profile" onChange={(e)=>setProfile(e.target.value)}>
              {profiles.map(p=> (
                <MenuItem key={p.key} value={p.key}>{p.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormGroup sx={{ mt:2 }}>
            {profiles.find(x=>x.key===profile).include.map(k=> (
              <FormControlLabel key={k} control={<Checkbox checked disabled />} label={k} />
            ))}
            {!canRaw && profile==='raw_csv' && <div style={{color:'red'}}>Raw exports require elevated permission</div>}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={onConfirm}>Request Export</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
