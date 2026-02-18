import React, {useEffect, useState} from 'react'
import { Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem, Button } from '@mui/material'
import { getAnalyticsQBR } from '../api/client'

export default function QBRPage(){
  const [fy, setFy] = useState(new Date().getFullYear())
  const [quarter, setQuarter] = useState(1)
  const [rows, setRows] = useState([])

  async function fetch(){
    const res = await getAnalyticsQBR({fy, quarter})
    setRows(res || [])
  }

  useEffect(()=>{ fetch() }, [])

  return (
    <Box sx={{p:3}}>
      <Typography variant="h4">QBR / Boards</Typography>
      <Paper sx={{p:2, mt:2}}>
        <FormControl sx={{mr:2}}><InputLabel>FY</InputLabel><Select value={fy} label="FY" onChange={(e)=>setFy(Number((e.target as any).value))}>{[2024,2025,2026].map(y=> <MenuItem key={y} value={y}>{y}</MenuItem>)}</Select></FormControl>
        <FormControl sx={{mr:2}}><InputLabel>Quarter</InputLabel><Select value={quarter} label="Quarter" onChange={(e)=>setQuarter(Number((e.target as any).value))}>{[1,2,3,4].map(q=> <MenuItem key={q} value={q}>{q}</MenuItem>)}</Select></FormControl>
        <Button onClick={fetch}>Refresh</Button>
      </Paper>
      <Paper sx={{p:2, mt:2}}>
        {rows.length===0 ? <div>No data</div> : (
          <table style={{width:'100%'}}>
            <thead><tr>{Object.keys(rows[0]).map(k=> <th key={k}>{k}</th>)}</tr></thead>
            <tbody>{rows.map((r,i)=>(<tr key={i}>{Object.keys(r).map(k=> <td key={k}>{String(r[k] ?? '')}</td>)}</tr>))}</tbody>
          </table>
        )}
      </Paper>
    </Box>
  )
}
