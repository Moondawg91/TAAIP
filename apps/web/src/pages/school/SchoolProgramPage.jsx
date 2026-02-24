import React from 'react'
import { Box, Typography } from '@mui/material'
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'

export default function SchoolProgramPage(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">School Recruiting — Program</Typography>
      <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:2 }}>Coverage, Engagement, Attribution, and CEP placeholders</Typography>

      <Box sx={{ display:'grid', gridTemplateColumns: '1fr', gap:16 }}>
        <EmptyStateWithReadiness title="Coverage" purpose="Geographic coverage for school recruiting" requiredDatasets={[ 'mi_zip_fact' ]} templateLinks={[{ href: '/api/market-intel/import-templates', label: 'Market Intel templates' }]} primaryActions={[{ href: '/import-center', label: 'Open Imports Center' }]} />

        <EmptyStateWithReadiness title="Engagement" purpose="Recruiting engagement data" requiredDatasets={[ 'school_recruiting_engagement' ]} templateLinks={[{ href: '/import-center', label: 'Imports Center' }]} primaryActions={[{ href: '/import-center', label: 'Open Imports Center' }]} />

        <EmptyStateWithReadiness title="Production attribution" purpose="Attribution metrics and production counts" requiredDatasets={[ 'production_events' ]} templateLinks={[{ href: '/import-center', label: 'Imports Center' }]} />

        <EmptyStateWithReadiness title="Career Exploration Program (CEP)" purpose="ASVAB/SASVAB placeholders; no analysis until datasets imported" requiredDatasets={[ 'cep_assessments' ]} templateLinks={[{ href: '/import-center', label: 'Imports Center' }]} />
      </Box>
    </Box>
  )
}
