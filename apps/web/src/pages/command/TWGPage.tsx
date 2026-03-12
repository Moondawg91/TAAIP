import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Divider } from '@mui/material'
import { apiFetch } from '../../api/client'

export default function CommandTWGPage(){
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    let mounted = true
    ;(async ()=>{
      try{
        const data = await apiFetch('/api/v2/twg')
        if (!mounted) return
        setRows(Array.isArray(data) ? data : (data && data.items) ? data.items : [])
      }catch(e){ if (!mounted) return; setRows([]) }
      finally{ if (mounted) setLoading(false) }
    })()
    return ()=>{ mounted = false }
  },[])

  return (
    <Box sx={{px:4, py:3}}>
      <Typography variant="h4">Targeting Working Group (TWG)</Typography>
      <Typography variant="subtitle1" sx={{color:'text.secondary'}}>Collaboration and action tracking for TWG — issues, owners, and status.</Typography>

      <Paper sx={{mt:3, p:2}}>
        <Typography variant="h6">Issues / Actions</Typography>
        <Divider sx={{my:1}} />
        {loading && <div>Loading…</div>}
        {!loading && rows.length === 0 && <div>No TWG items found.</div>}
        {!loading && rows.length > 0 && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Issue</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Due</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r, idx) => (
                <TableRow key={r.id || idx}>
                  <TableCell>{r.title || r.issue}</TableCell>
                  <TableCell>{r.owner}</TableCell>
                  <TableCell>{r.due}</TableCell>
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
