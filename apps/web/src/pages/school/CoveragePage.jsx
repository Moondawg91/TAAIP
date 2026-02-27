import React from 'react'
import { Box, Typography } from '@mui/material'
// TopFilterBar rendered centrally by shell
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'
import { exportToCsv } from '../../utils/exportCsv'
import ExportMenu from '../../components/ExportMenu'

export default function CoveragePage(){
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — Coverage</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Geographic coverage and market intelligence</Typography>
        </Box>
        <ExportMenu data={[]} filename="school_coverage" />
      </Box>
      {/* TopFilterBar rendered by shell */}
      <Box sx={{ mt:1 }}>
        <EmptyStateWithReadiness title="Coverage" purpose="Geographic coverage for school recruiting" requiredDatasets={[ 'mi_zip_fact' ]} templateLinks={[{ href: '/api/market-intel/import-templates', label: 'Market Intel templates' }]} primaryActions={[]} />
      </Box>
    </Box>
  )
}
