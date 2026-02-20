import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText } from '@mui/material'
import api from '../../api/client'

export default function MarketingROIPage(){
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{ let mounted = true; setLoading(true); api.getMarketingRollup().then(d=>{ if(!mounted) return; setData(d || {} ) }).catch(()=>{ if(mounted) setData({totals:{}, by_channel:[]}) }).finally(()=> mounted && setLoading(false)); return ()=> mounted = false }, [])

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Marketing ROI</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Marketing totals and channel efficiency.</Typography>
      <Card sx={{ mb:2 }}>
        <CardContent>
          {loading ? <Typography>Loading...</Typography> : (
            <Box>
              <Typography sx={{ fontWeight:700 }}>Totals</Typography>
              <Typography>Impressions: {data.totals?.impressions || 0}</Typography>
              <Typography>Engagements: {data.totals?.engagements || 0}</Typography>
              <Typography>Conversions: {data.totals?.conversions || 0}</Typography>
              <Typography>Cost: {data.totals?.cost || 0}</Typography>
              <Typography sx={{ mt:2, fontWeight:700 }}>By Channel</Typography>
              <List>
                {(data.by_channel || []).map((c,idx)=> (
                  <ListItem key={idx}><ListItemText primary={c.channel || 'Unknown'} secondary={`Cost: ${c.cost || 0} • Impr: ${c.impressions || 0}`} /></ListItem>
                ))}
                {(!data.by_channel || data.by_channel.length===0) && <ListItem><ListItemText primary="No marketing activities" secondary="No marketing data available." /></ListItem>}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
