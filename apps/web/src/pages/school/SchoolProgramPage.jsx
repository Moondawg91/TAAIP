import React from 'react'
import { Box, Typography, Button } from '@mui/material'
import { exportToCsv } from '../../utils/exportCsv'
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'

export default function SchoolProgramPage(){
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — Program</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Coverage, Engagement, Attribution, and CEP placeholders</Typography>
        </Box>
        <Button variant="outlined" size="small" onClick={()=>{
          const cols = ['section','note']
          const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')
          exportToCsv(`program_${ts}.csv`, [], cols)
        }}>Export CSV</Button>
      </Box>

      <Box sx={{ display:'grid', gridTemplateColumns: '1fr', gap:8 }}>
        <EmptyStateWithReadiness title="Coverage" purpose="Geographic coverage for school recruiting" requiredDatasets={[ 'mi_zip_fact' ]} templateLinks={[{ href: '/api/market-intel/import-templates', label: 'Market Intel templates' }]} primaryActions={[]} />

        <EmptyStateWithReadiness title="Engagement" purpose="Recruiting engagement data" requiredDatasets={[ 'school_recruiting_engagement' ]} templateLinks={[]} primaryActions={[]} />

        <EmptyStateWithReadiness title="Production attribution" purpose="Attribution metrics and production counts" requiredDatasets={[ 'production_events' ]} templateLinks={[]} />

        <EmptyStateWithReadiness title="Career Exploration Program (CEP)" purpose="ASVAB/SASVAB placeholders; no analysis until datasets imported" requiredDatasets={[ 'cep_assessments' ]} templateLinks={[]} />
      </Box>
    </Box>
  )
}
