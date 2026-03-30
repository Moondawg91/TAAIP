import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, List, ListItem, ListItemText } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
import { getMarketIntelTargets } from '../../api/client'

export default function USARECTargetingPage() {
  const [targets, setTargets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(()=>{ let mounted = true
    async function load(){
      try{
        const t = await getMarketIntelTargets()
        if(!mounted) return
        // API may return { tables: { targets: [...] } } or direct array
        const rows = (t && t.tables && t.tables.targets) ? t.tables.targets : (t && t.targets) ? t.targets : (Array.isArray(t) ? t : [])
        setTargets(rows)
      }catch(e){ console.error('load targets', e); if(mounted) setTargets([]) }
      finally{ if(mounted) setLoading(false) }
    }
    load()
    return ()=>{ mounted = false }
  },[])

  return (
    <Box sx={{ minHeight: '100%', p: 3, bgcolor: 'background.default', color: 'text.primary' }}>
      <DashboardToolbar title="USAREC Targeting" subtitle="Targeting methodology & datasets" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert('Export unavailable') }} />
      <Paper elevation={0} sx={{ p: 3, bgcolor: 'transparent', color: 'inherit' }}>
        <Typography variant="h4" sx={{ color: 'text.primary' }}>USAREC Targeting</Typography>
        { loading ? (
          <Typography>Loading targets...</Typography>
        ) : ( targets && targets.length ? (
          <List>
            {targets.map((r,i)=>(<ListItem key={i}><ListItemText primary={r.name || r.label || r.zip || r.cbsa || `target ${i}`} secondary={r.note || JSON.stringify(r)} /></ListItem>))}
          </List>
        ) : (
          <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>No targeting outputs published. Upload market datasets and commit to populate targets.</Typography>
        )) }
      </Paper>
    </Box>
  )
}
