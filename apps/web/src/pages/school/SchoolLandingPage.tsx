import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Grid } from '@mui/material'
import ZeroState from '../../components/ZeroState'
import DualModeTabs from '../../components/DualModeTabs'
import ExportMenu from '../../components/ExportMenu'
import { getSchoolProgramReadiness } from '../../api/client'

export default function SchoolLandingPage(){
  const [ready, setReady] = useState(null)

  useEffect(()=>{
    let mounted = true
    getSchoolProgramReadiness().then(r=>{ if(mounted) setReady(r) }).catch(()=>{ if(mounted) setReady(null) })
    return ()=>{ mounted = false }
  },[])

  const loaded = ready && Array.isArray(ready.datasets) && ready.datasets.some(d=>d.dataset_key==='school_program_fact' && d.loaded)

  return (
    <Box sx={{ p:3 }}>
      <Box sx={{display:'flex', alignItems:'center'}}>
        <Typography variant="h4">School Recruiting Program</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={[]} filename="school_recruiting" />
        </Box>
      </Box>
      <DualModeTabs />

      { ready === null ? (
        <ZeroState title="Loading" message="Checking school program data availability..." />
      ) : (loaded ? (
        <Paper sx={{ p:2 }}>
          <Typography variant="subtitle1">School program datasets are loaded and recent. Use the Program tab for detailed KPIs and breakdowns.</Typography>
        </Paper>
      ) : (
        <ZeroState title="Data not loaded" message="No program dashboards available — import datasets or check API connectivity." />
      )) }
    </Box>
  )
}
