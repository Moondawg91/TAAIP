import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'
import { importJobs } from '../../api/client'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
import EmptyState from '../../components/EmptyState'

export default function TargetingDataPage(){
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ load() }, [])

  async function load(){
    setLoading(true)
    try{
      const j = await importJobs()
      setJobs(j || [])
    }catch(e){ console.error('load import jobs', e) }
    finally{ setLoading(false) }
  }

  return (
    <Box sx={{ p:2, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <DashboardToolbar title="Targeting Data" subtitle="Import jobs & datasets" filters={{}} onFiltersChange={()=>{}} />
      <Box sx={{ mt:2 }}>
        <EmptyState title="Targeting Data" subtitle="View and manage import jobs here. Load datasets in Data Hub." />
      </Box>
    </Box>
  )
}
