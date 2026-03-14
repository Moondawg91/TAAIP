import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Paper, Table, TableBody, TableCell, TableHead, TableRow, Select, MenuItem } from '@mui/material'

function priorityLabel(score){
  if (score == null) return {label: 'No data', color: '#777'}
  if (score >= 0.75) return {label: 'High', color: '#c62828'}
  if (score >= 0.4) return {label: 'Monitor', color: '#ffb300'}
  return {label: 'Low', color: '#2e7d32'}
}

export default function TargetingBoard(){
  const [schools, setSchools] = useState([])
  const [loading, setLoading] = useState(true)
  const [unit, setUnit] = useState('')

  useEffect(() => {
    // try to load preferred unit from localStorage
    try { const f = JSON.parse(localStorage.getItem('command_center_filters_v1') || '{}'); if (f.unitRsid) setUnit(f.unitRsid) } catch(e){}
    setLoading(true)
    const q = unit ? `?unit_rsid=${encodeURIComponent(unit)}` : ''
    fetch(`/api/v2/targeting/schools${q}`).then(r => r.json()).then(j => {
      const s = j?.schools || j?.results || []
      setSchools(s)
    }).catch(() => setSchools([])).finally(() => setLoading(false))
  }, [unit])

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:1 }}>Targeting Board</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Top-priority schools for commander attention. Priorities are briefing-friendly and show confidence and drivers.</Typography>

      <Box sx={{ mb:2 }}>
        <label style={{ marginRight: 8 }}>Unit:</label>
        <input value={unit} onChange={e=>setUnit(e.target.value)} placeholder="Unit RSID (optional)" />
      </Box>

      <Paper sx={{ p:2 }}>
        {loading ? <Typography>Loading schools…</Typography> : (
          schools && schools.length ? (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>School</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Top Drivers</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {schools.slice(0,50).map((s,i)=>{
                  const score = s.priority ?? s.score ?? s.targeting_score ?? null
                  const conf = s.confidence ?? s.confidence_score ?? s.conf ?? null
                  const pl = priorityLabel(score)
                  const drivers = (s.top_drivers || s.drivers || []).slice(0,3)
                  return (
                    <TableRow key={i}>
                      <TableCell>{s.name || s.school || s.school_name || '—'}</TableCell>
                      <TableCell><span style={{ color: pl.color, fontWeight: 700 }}>{pl.label}</span></TableCell>
                      <TableCell>{score != null ? (Math.round(score*100)/100) : '—'}</TableCell>
                      <TableCell>{conf != null ? (Math.round(conf*100)/100) : '—'}</TableCell>
                      <TableCell>{drivers.length ? drivers.join(', ') : '—'}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          ) : (
            <Typography>No prioritized schools found for the selected unit.</Typography>
          )}
      </Paper>
    </Box>
  )
}
