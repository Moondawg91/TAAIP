import React from 'react'
import { Box, Typography, Chip } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function MarketSegmentationPage(){
  return (
    <Box>
      <DashboardToolbar title="Market Segmentation" subtitle="Audience segmentation & insights" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert(`Export ${t} coming soon`) }} />
      <Typography variant="h4">Market Segmentation</Typography>
      <Chip label="Status: Coming soon" sx={{ mt:2 }} />
    </Box>
  )
}
