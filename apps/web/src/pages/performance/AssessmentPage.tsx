import React from 'react'
import { Box, Typography, Tab, Tabs } from '@mui/material'
import ZeroState from '../../components/ZeroState'
import { useState } from 'react'
import DualModeTabs from '../../components/DualModeTabs'
// TopFilterBar centrally rendered by shell when route policy enables it
import ExportMenu from '../../components/ExportMenu'

export default function PerformanceAssessment(){
  const [tab, setTab] = useState(0)
  return (
    <Box sx={{ p:3 }}>
      <Box sx={{display:'flex', alignItems:'center', gap:2}}>
        <Typography variant="h4">Performance Assessment (All-Up)</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={[]} filename="performance_assessment" />
        </Box>
      </Box>
      <DualModeTabs />
      <Tabs value={tab} onChange={(_,v)=>setTab(v)} sx={{ mt:2 }}>
        <Tab label="FY Performance" />
        <Tab label="QTR Assessment" />
        <Tab label="Recruiting Month" />
      </Tabs>
      <ZeroState title="Feature available soon" message="This route exists but is not enabled yet." />
    </Box>
  )
}
