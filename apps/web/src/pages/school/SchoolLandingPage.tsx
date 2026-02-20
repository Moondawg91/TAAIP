import React from 'react'
import { Box, Typography, Chip } from '@mui/material'
import DualModeTabs from '../../components/DualModeTabs'
import DashboardFilterBar from '../../components/DashboardFilterBar'
import ExportMenu from '../../components/ExportMenu'

export default function SchoolLandingPage(){
  return (
    <Box sx={{ p:3 }}>
      <Box sx={{display:'flex', alignItems:'center'}}>
        <Typography variant="h4">School Recruiting Program</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={[]} filename="school_recruiting" />
        </Box>
      </Box>
      <DualModeTabs />
      <DashboardFilterBar />
      <Chip label="Dashboards coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
