import React from 'react'
import { Box, Typography } from '@mui/material'
import ZeroState from '../../components/ZeroState'
// Filters rendered centrally by the shell
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'
import { exportToCsv } from '../../utils/exportCsv'
import ExportMenu from '../../components/ExportMenu'

export default function CompliancePage(){
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — Compliance</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Compliance and regulatory references</Typography>
        </Box>
        <ExportMenu data={[]} filename="school_compliance" />
      </Box>
      {/* Filters rendered by shell */}
      <Box sx={{ mt:1 }}>
        <EmptyStateWithReadiness title="Compliance" purpose="Regulatory references and compliance checks" requiredDatasets={[ 'regulatory_references' ]} templateLinks={[{ href: '/resources/regulatory', label: 'Regulatory Registry' }]} />
        <ZeroState title="Data not loaded" message="Compliance dashboards unavailable until regulatory references are imported." actionLabel="Regulatory Registry" actionHref="/resources/regulatory" />
      </Box>
    </Box>
  )
}
