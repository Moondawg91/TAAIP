import React from 'react'
import { Box, Typography } from '@mui/material'
// Filters are now rendered centrally by the shell when enabled by route policy
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'
import { exportToCsv } from '../../utils/exportCsv'
import ExportMenu from '../../components/ExportMenu'

export default function EventsPage(){
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — Events</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Events and engagements for schools</Typography>
        </Box>
        <ExportMenu data={[]} filename="school_events" />
      </Box>
      {/* Filters rendered by shell */}
      <Box sx={{ mt:1 }}>
        <EmptyStateWithReadiness title="Events" purpose="Event listings and planned engagements" requiredDatasets={[ 'events' ]} templateLinks={[]} />
      </Box>
    </Box>
  )
}
