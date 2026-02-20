import React, { useEffect, useState } from 'react'
import { Box, Typography, Chip, Button, Menu, MenuItem } from '@mui/material'
import { getMissionAssessment, exportDashboard } from '../../api/client'

export default function OpsBudgetPage(){
  const [summary, setSummary] = useState(null)
  const [anchorEl, setAnchorEl] = useState(null)

  useEffect(()=>{
    let mounted = true
    getMissionAssessment().then(d=>{ if(mounted) setSummary(d) }).catch(()=>{})
    return ()=>{ mounted = false }
  },[])

  function handleExportClick(e){ setAnchorEl(e.currentTarget) }
  function handleExportClose(){ setAnchorEl(null) }

  async function doExport(type, format){
    handleExportClose()
    try{
      const text = await exportDashboard(type, format)
      const filename = `${type}.${format === 'csv' ? 'csv' : 'json'}`
      const blob = new Blob([text], { type: format === 'csv' ? 'text/csv' : 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    }catch(e){ console.error('export failed', e) }
  }

  return (
    <Box>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <Typography variant="h4">Budget Tracker</Typography>
        <Box>
          <Button variant="contained" color="primary" onClick={handleExportClick}>Export</Button>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleExportClose}>
            <MenuItem onClick={()=>doExport('budget','csv')}>Budget — CSV</MenuItem>
            <MenuItem onClick={()=>doExport('budget','json')}>Budget — JSON</MenuItem>
          </Menu>
        </Box>
      </Box>

      <Box sx={{ mt:2 }}>
        {summary ? (
          <Box>
            <Typography variant="subtitle1">Budget snapshot</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(summary.tactical_rollup?.budget || summary.tactical_rollup || {}, null, 2)}</pre>
          </Box>
        ) : (
          <Chip label="Loading rollup..." sx={{ mt:2 }} />
        )}
      </Box>
    </Box>
  )
}
