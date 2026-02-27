import React from 'react'
import { Box, Typography } from '@mui/material'
import ZeroState from '../../components/ZeroState'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function MarketSegmentationPage(){
  return (
    <Box>
      <DashboardToolbar title="Market Segmentation" subtitle="Audience segmentation & insights" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert('Export unavailable') }} />
      <Typography variant="h4">Market Segmentation</Typography>
      <ZeroState title="Feature available soon" message="This route exists but is not enabled yet." />
    </Box>
  )
}
