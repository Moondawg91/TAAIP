import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, List, ListItem, ListItemText } from '@mui/material'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
import { getMarketIntelSummary, getMarketIntelDemographics } from '../../api/client'

export default function MarketSegmentationPage(){
  const [summary, setSummary] = useState(null)
  const [demo, setDemo] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{ let mounted = true
    async function load(){
      try{
        const s = await getMarketIntelSummary()
        const d = await getMarketIntelDemographics()
        if(!mounted) return
        setSummary(s)
        setDemo(d)
      }catch(e){
        console.error('load market segmentation', e)
        if(mounted){ setSummary(null); setDemo(null) }
      }
      finally{ if(mounted) setLoading(false) }
    }
    load()
    return ()=>{ mounted = false }
  },[])

  const hasData = summary && (summary.kpis || summary.rows || summary.metrics)

  return (
    <Box>
      <DashboardToolbar title="Market Segmentation" subtitle="Audience segmentation & insights" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert('Export unavailable') }} />
      <Typography variant="h4" sx={{ p:2 }}>Market Segmentation</Typography>
      { loading ? (
        <Typography sx={{ p:2 }}>Loading segmentation data...</Typography>
      ) : (!hasData) ? (
        <Paper sx={{ p:2, m:2 }}>
          <Typography variant="h6">No market segmentation data</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Market/ZIP/CBSA datasets are not available for your selection. Import market datasets to enable segmentation views.</Typography>
        </Paper>
      ) : (
        <Box sx={{ p:2 }}>
          <Paper sx={{ p:2, mb:2 }}>
            <Typography variant="subtitle1">Summary</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(summary, null, 2)}</pre>
          </Paper>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle1">Demographics</Typography>
            { demo && demo.rows && demo.rows.length ? (
              <List dense>
                {demo.rows.map((r,i)=>(<ListItem key={i}><ListItemText primary={r.label || r.name || `row ${i}`} secondary={JSON.stringify(r)} /></ListItem>))}
              </List>
            ) : (
              <Typography variant="body2" sx={{ color:'text.secondary' }}>No demographic rollups available.</Typography>
            ) }
          </Paper>
        </Box>
      ) }
    </Box>
  )
}
