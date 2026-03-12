import React from 'react'
import { Box, Typography } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
import EmptyState from '../../components/EmptyState'

export default function MissionPlanningPage(){
  return (
    <Box sx={{ p:2, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <DashboardToolbar title="Mission Planning" subtitle="Plan missions and assign resources" filters={{}} onFiltersChange={()=>{}} />
      <Box sx={{ mt:2 }}>
        <EmptyState title="Mission Planning" subtitle="Create mission plans by importing relevant datasets or adjusting filters." />
      </Box>
    </Box>
  )
}
