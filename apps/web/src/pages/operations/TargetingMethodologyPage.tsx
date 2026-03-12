import React from 'react'
import { Box } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
import EmptyState from '../../components/EmptyState'

export default function TargetingMethodologyPage(){
  return (
    <Box sx={{ p:2, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <DashboardToolbar title="Targeting Methodology" subtitle="Guidance & best practices" filters={{}} onFiltersChange={()=>{}} />
      <Box sx={{ mt:2 }}>
        <EmptyState title="Targeting Methodology" subtitle="Guidance and best practices will appear here once data is imported." />
      </Box>
    </Box>
  )
}
