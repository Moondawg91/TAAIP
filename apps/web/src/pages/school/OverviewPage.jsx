import React, { useEffect, useState } from 'react'
import { Box, Typography } from '@mui/material'
import ZeroState from '../../components/ZeroState'
// Filters are rendered centrally by the shell when route policy enables them
import EmptyStateWithReadiness from '../../components/EmptyStateWithReadiness'
import { getSchoolSummary } from '../../api/client'
import { exportToCsv } from '../../utils/exportCsv'
import ExportMenu from '../../components/ExportMenu'

export default function OverviewPage(){
  const [summary, setSummary] = useState(null)
  useEffect(()=>{ let mounted=true; getSchoolSummary().then(r=>{ if(mounted) setSummary(r && r.data ? r.data : null) }).catch(()=>{}); return ()=> mounted=false }, [])
  const handleExport = () => {
    const cols = ['metric','value']
    const rows = summary ? Object.keys(summary).map(k=>({ metric: k, value: summary[k] })) : []
    const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')
    exportToCsv(`overview_${ts}.csv`, rows, cols)
  }
  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — Dashboard</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>High level program metrics and readiness</Typography>
        </Box>
        <ExportMenu data={summary ? Object.keys(summary).map(k=>({ metric: k, value: summary[k] })) : []} filename="school_overview" />
      </Box>
      {/* Filters rendered by shell */}
      <Box sx={{ display:'grid', gridTemplateColumns: '1fr', gap:8, mt:1 }}>
        <EmptyStateWithReadiness title="Program Readiness" purpose="Program-level readiness checks" requiredDatasets={[ 'mi_zip_fact', 'mi_school_fact' ]} templateLinks={[]} primaryActions={[]} />
        <Box>
          <ZeroState title={ summary && Object.keys(summary).length>0 ? 'Overview' : 'Data not loaded' } message={ summary ? undefined : 'Overview metrics are unavailable; import required datasets or check API.' } />
          { summary ? <Box sx={{ mt:1 }}><Typography>Schools covered: {summary.schools_covered || 0}</Typography></Box> : null }
        </Box>
      </Box>
    </Box>
  )
}
