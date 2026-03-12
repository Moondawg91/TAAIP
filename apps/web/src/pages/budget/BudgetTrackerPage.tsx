import React from 'react'
import { Box, Typography } from '@mui/material'
import PageFrame from '../../components/layout/PageFrame'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
// Filters are rendered centrally by the shell when route policy enables them
import ExportMenu from '../../components/ExportMenu'
import EmptyState from '../../components/EmptyState'

export default function BudgetTrackerPage(){
  return (
    <PageFrame>
      <Box sx={{ p:2 }}>
        <Box sx={{ display:'flex', alignItems:'center', gap:2 }}>
          <Typography variant="h5">Budget Tracker</Typography>
          <Box sx={{ ml:'auto' }}>
            <ExportMenu />
          </Box>
        </Box>

        <DashboardToolbar title="Budget Tracker" subtitle="Budget rollups & breakdowns" filters={{}} onFiltersChange={()=>{}} />

        <Box sx={{ mt:2 }}>
          <EmptyState title="No data loaded" subtitle="Data not loaded. Load datasets in Data Hub." />
        </Box>
      </Box>
    </PageFrame>
  )
}
