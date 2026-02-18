import React from 'react'
import { Box, Typography } from '@mui/material'

export default function PerformanceTrackingPage(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">Performance Tracking</Typography>
      <Typography sx={{ mt:2, color:'text.secondary' }}>Production, funnel, and standards comparison dashboards.</Typography>
    </Box>
  )
}
