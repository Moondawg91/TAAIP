import React from 'react'
import { Box, Typography, Tab, Tabs, Chip } from '@mui/material'
import { useState } from 'react'
import DualModeTabs from '../../components/DualModeTabs'
import DashboardFilterBar from '../../components/DashboardFilterBar'
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
      <DashboardFilterBar />
      <Tabs value={tab} onChange={(_,v)=>setTab(v)} sx={{ mt:2 }}>
        <Tab label="FY Performance" />
        <Tab label="QTR Assessment" />
        <Tab label="Recruiting Month" />
      </Tabs>
      <Chip label="Status: Coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
