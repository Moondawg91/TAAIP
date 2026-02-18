import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText } from '@mui/material'
import { getKpis } from '../../api/client'

export default function PerformanceMarketSegmentationPage(){
  const [kpis, setKpis] = useState([])
  useEffect(()=>{ load() }, [])
  async function load(){
    try{
      const data = await getKpis('USAREC')
      setKpis(Array.isArray(data) ? data : (data.rows || []))
    }catch(e){ console.error('load kpis', e) }
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Market Segmentation</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Segmentation views for performance analysis.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">KPIs</Typography>
          <List>
            {(kpis || []).map((k:any)=> (
              <ListItem key={k.id || k.metric_key}>
                <ListItemText primary={k.metric_key || k.name} secondary={String(k.metric_value || k.value || '')} />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  )
}
