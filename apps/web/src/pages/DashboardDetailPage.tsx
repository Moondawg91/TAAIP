import React, {useEffect, useState} from 'react'
import { Box, Typography, Paper, Button } from '@mui/material'
import client from '../api/client'
import { useLocation } from 'react-router-dom'

function useQuery(){ return new URLSearchParams(useLocation().search) }

export default function DashboardDetailPage(){
  const q = useQuery()
  const stage = q.get('stage')
  const [rows, setRows] = useState([])

  useEffect(()=>{ fetchRows() }, [stage])

  async function fetchRows(){
    const res = await client.getFunnelEvents ? await client.getFunnelEvents({stage_key: stage}) : []
    setRows(res)
  }

  function exportCsv(){
    if (!rows || rows.length===0) return
    const keys = Object.keys(rows[0])
    const csv = [keys.join(',')].concat(rows.map(r=> keys.map(k=> JSON.stringify(r[k] ?? '')).join(','))).join('\n')
    const blob = new Blob([csv], {type:'text/csv'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `detail_${stage || 'all'}.csv`; a.click(); URL.revokeObjectURL(url)
  }

  return (
    <Box sx={{p:3}}>
      <Typography variant="h5">Detail — {stage}</Typography>
      <Paper sx={{p:2, mt:2}}>
        {rows.length===0 ? <div>No data imported</div> : (
          <div>
            <Button variant="contained" onClick={exportCsv}>Export CSV</Button>
            <div style={{maxHeight:400, overflow:'auto'}}>
              <table style={{width:'100%'}}>
                <thead><tr>{Object.keys(rows[0]).map(k=> <th key={k}>{k}</th>)}</tr></thead>
                <tbody>{rows.map((r,i)=>(<tr key={i}>{Object.keys(r).map(k=> <td key={k}>{String(r[k] ?? '')}</td>)}</tr>))}</tbody>
              </table>
            </div>
          </div>
        )}
      </Paper>
    </Box>
  )
}
