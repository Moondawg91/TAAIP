import React from 'react'
import { Box, Typography } from '@mui/material'
// TopFilterBar rendered centrally by shell
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'
import { exportToCsv } from '../../utils/exportCsv'
import ExportMenu from '../../components/ExportMenu'

export default function LeadsPage(){
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — Leads</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Lead capture and funnel for school engagements</Typography>
        </Box>
        <ExportMenu data={[]} filename="school_leads" />
      </Box>
      {/* TopFilterBar rendered by shell */}
      <Box sx={{ mt:1 }}>
        <EmptyStateWithReadiness title="Leads" purpose="Lead capture and funnel" requiredDatasets={[ 'leads' ]} templateLinks={[]} />
      </Box>
    </Box>
  )
}
