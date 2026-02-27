import React, {useEffect} from 'react'
import { Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem, Button } from '@mui/material'
import { getAnalyticsQBR } from '../api/client'
import { useFilters } from '../contexts/FilterContext'

export default function QBRPage(){
  const { filters, setFy, setQtr } = useFilters()
  const [rows, setRows] = React.useState([])

  async function fetch(){
    const fyVal = filters.fy ? Number(filters.fy) : new Date().getFullYear()
    let qNum = 1
    try{ qNum = filters.qtr && String(filters.qtr).startsWith('Q') ? Number(String(filters.qtr).replace(/^Q/,'')) : Number(filters.qtr) || 1 }catch(e){}
    const res = await getAnalyticsQBR({ fy: fyVal, quarter: qNum })
    setRows(res || [])
  }

  useEffect(()=>{ fetch() }, [filters.fy, filters.qtr])

  return (
    <Box sx={{p:3}}>
      <Typography variant="h4">QBR / Boards</Typography>
      <Paper sx={{p:2, mt:2}}>
        <FormControl sx={{mr:2}} size="small">
          <InputLabel>FY</InputLabel>
          <Select value={filters.fy || String(new Date().getFullYear())} label="FY" onChange={(e)=>setFy(String((e.target as any).value))}>
            {[String(new Date().getFullYear()-1), String(new Date().getFullYear()), String(new Date().getFullYear()+1)].map(y=> <MenuItem key={y} value={y}>{y}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl sx={{mr:2}} size="small">
          <InputLabel>Quarter</InputLabel>
          <Select value={filters.qtr || 'Q1'} label="Quarter" onChange={(e)=>setQtr(String((e.target as any).value))}>
            {['Q1','Q2','Q3','Q4'].map(q=> <MenuItem key={q} value={q}>{q}</MenuItem>)}
          </Select>
        </FormControl>
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
