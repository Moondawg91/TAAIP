import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, List, ListItem, ListItemText } from '@mui/material'
import { getRoiKpis, getRoiBreakdown, getRoiFunnel } from '../../api/client'
import ExportMenu from '../../components/ExportMenu'

export default function RoiPage(){
  const [kpis, setKpis] = useState(null)
  const [breakdown, setBreakdown] = useState(null)
  const [funnel, setFunnel] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{ let mounted = true
    async function load(){
      try{
        const [kp, br, fu] = await Promise.all([getRoiKpis(), getRoiBreakdown(), getRoiFunnel()])
        if(!mounted) return
        setKpis(kp)
        setBreakdown(br)
        setFunnel(fu)
      }catch(e){
        if(!mounted) return
        setKpis(null); setBreakdown(null); setFunnel(null)
      }finally{ if(mounted) setLoading(false) }
    }
    load()
    return ()=>{ mounted = false }
  },[])

  const hasData = kpis && (kpis.kpis && (kpis.kpis.leads_total || kpis.kpis.contracts_total || kpis.kpis.spread_total || kpis.kpis.spend_total || kpis.kpis.leads_total))

  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — ROI</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Event ROI and attribution</Typography>
        </Box>
        <ExportMenu data={kpis ? [kpis] : []} filename="school_roi" />
      </Box>

      { loading ? (
        <Typography>Loading ROI data...</Typography>
      ) : (!hasData) ? (
        <Paper sx={{ p:2, mt:2 }}>
          <Typography variant="h6">No ROI data</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>No event ROI data published for your selection. Upload `event_roi` datasets and commit to publish ROI outputs.</Typography>
        </Paper>
      ) : (
        <Box sx={{ mt:2 }}>
          <Paper sx={{ p:2, mb:2 }}>
            <Typography variant="h6">KPIs</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(kpis, null, 2)}</pre>
          </Paper>
          <Paper sx={{ p:2, mb:2 }}>
            <Typography variant="h6">Breakdown</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(breakdown, null, 2)}</pre>
          </Paper>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Funnel</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(funnel, null, 2)}</pre>
          </Paper>
        </Box>
      ) }
    </Box>
  )
}
