import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Divider } from '@mui/material'
import { apiFetch } from '../../api/client'

export default function FusionCellPage(){
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    let mounted = true
    ;(async ()=>{
      try{
        const data = await apiFetch('/api/v2/fusion')
        if (!mounted) return
        setRows(Array.isArray(data) ? data : (data && data.items) ? data.items : [])
      }catch(e){ if (!mounted) return; setRows([]) }
      finally{ if (mounted) setLoading(false) }
    })()
    return ()=>{ mounted = false }
  },[])

  return (
    <Box sx={{px:4, py:3}}>
      <Typography variant="h4">Fusion Cell</Typography>
      <Typography variant="subtitle1" sx={{color:'text.secondary'}}>Fusion Cell recommendations, sync logs and decisions.</Typography>

      <Paper sx={{mt:3, p:2}}>
        <Typography variant="h6">Recommendations / Logs</Typography>
        <Divider sx={{my:1}} />
        {loading && <div>Loading…</div>}
        {!loading && rows.length === 0 && <div>No fusion items found.</div>}
        {!loading && rows.length > 0 && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Item</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r, idx) => (
                <TableRow key={r.id || idx}>
                  <TableCell>{r.title || r.item}</TableCell>
                  <TableCell>{r.type}</TableCell>
                  <TableCell>{r.owner}</TableCell>
                  <TableCell>{r.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Paper sx={{mt:3, p:2}}>
        <Typography variant="h6">Drilldown</Typography>
        <Divider sx={{my:1}} />
        <div>Detail / drilldown panel will display details for selected item.</div>
      </Paper>
    </Box>
  )
}

