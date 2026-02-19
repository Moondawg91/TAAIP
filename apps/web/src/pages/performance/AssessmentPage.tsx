import React from 'react'
import { Box, Typography, Tab, Tabs, Chip } from '@mui/material'
import { useState } from 'react'

export default function PerformanceAssessment(){
  const [tab, setTab] = useState(0)
  return (
    <Box>
      <Typography variant="h4">Performance Assessment (All-Up)</Typography>
      <Tabs value={tab} onChange={(_,v)=>setTab(v)} sx={{ mt:2 }}>
        <Tab label="FY Performance" />
        <Tab label="QTR Assessment" />
        <Tab label="Recruiting Month" />
      </Tabs>
      <Chip label="Status: Coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
