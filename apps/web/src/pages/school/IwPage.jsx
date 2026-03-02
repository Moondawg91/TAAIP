import React from 'react'
import { Box, Typography, Button } from '@mui/material'
import ZeroState from '../../components/ZeroState'
import { exportToCsv } from '../../utils/exportCsv'
// Filters rendered centrally by the shell when route policy enables them

export default function IwPage(){
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — I&W</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:2 }}>Indicators & Warnings for school recruiting</Typography>
        </Box>
        <Button variant="outlined" size="small" onClick={()=>{
          const cols = ['indicator','status']
          const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')
          exportToCsv(`iw_${ts}.csv`, [], cols)
        }}>Export CSV</Button>
      </Box>
      {/* Filters rendered by shell */}
      <ZeroState title="Data not loaded" message="I&W indicators unavailable — no source data present." />
    </Box>
  )
}
