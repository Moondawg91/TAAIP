import React from 'react'
import { Box, Typography } from '@mui/material'
// Filters rendered centrally by the shell
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'
import { exportToCsv } from '../../utils/exportCsv'
import ExportMenu from '../../components/ExportMenu'

export default function RoiPage(){
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — ROI</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Event ROI and attribution</Typography>
        </Box>
        <ExportMenu data={[]} filename="school_roi" />
      </Box>
      {/* Filters rendered by shell */}
      <Box sx={{ mt:1 }}>
        <EmptyStateWithReadiness title="ROI" purpose="Return on investment for school events" requiredDatasets={[ 'event_roi' ]} templateLinks={[]} />
      </Box>
    </Box>
  )
}
