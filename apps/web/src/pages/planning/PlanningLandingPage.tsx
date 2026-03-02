import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Divider } from '@mui/material'
import { apiFetch } from '../../api/client'

export default function PlanningLandingPage(){
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    let mounted = true
    ;(async ()=>{
      try{
        const resp = await apiFetch('/api/v2/planning/overview')
        if (!mounted) return
        setItems((resp && resp.items) ? resp.items : [])
      }catch(e){
        if (!mounted) return
        setItems([])
      }finally{ if (mounted) setLoading(false) }
    })()
    return ()=>{ mounted = false }
  },[])

  return (
    <Box sx={{px:4, py:3}}>
      <Typography variant="h4" sx={{fontWeight:700}}>Planning</Typography>
      <Typography variant="subtitle1" sx={{color:'text.secondary', mt:1}}>Quarterly planning, TWG and Fusion coordination workspace.</Typography>

      <Paper sx={{mt:3, p:2}}>
        <Typography variant="h6">QTR Objectives</Typography>
        <Divider sx={{my:1}} />
        {loading && <div>Loading…</div>}
        {!loading && items.length === 0 && <div>No objectives found. Use Planning tools to create milestones.</div>}
        {!loading && items.length > 0 && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Objective</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Due</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((it, idx) => (
                <TableRow key={idx}>
                  <TableCell>{it.title}</TableCell>
                  <TableCell>{it.owner}</TableCell>
                  <TableCell>{it.due}</TableCell>
                  <TableCell>{it.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Paper sx={{mt:3, p:2}}>
        <Typography variant="h6">Calendar</Typography>
        <Divider sx={{my:1}} />
        <div>Calendar view placeholder — integrate with the calendar service.</div>
      </Paper>
    </Box>
  )
}
