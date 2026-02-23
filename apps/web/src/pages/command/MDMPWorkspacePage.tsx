import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Card, List, ListItem, Button } from '@mui/material'
import * as api from '../../api/client'
import COAComparisonView from '../../components/command/COAComparisonView'

export default function MDMPWorkspacePage(){
  const [coasResp, setCoasResp] = useState(null)

  useEffect(()=>{ (async ()=>{
    try{ setCoasResp(await api.getCOARecommendations()) }catch(e){ setCoasResp(null) }
  })() },[])

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4">MDMP Workspace</Typography>
      <Grid container spacing={2} sx={{ mt:1 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ p:2, bgcolor:'background.paper', borderRadius: '4px' }}>
            <Typography variant="subtitle2">Mission</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>Not available.</Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ p:2, bgcolor:'background.paper', borderRadius: '4px' }}>
            <Typography variant="subtitle2">Environment Summary</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>No summary available.</Typography>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ p:2, bgcolor:'background.paper', borderRadius: '4px' }}>
            <Typography variant="subtitle2">Problem Statement</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>{coasResp?.problem_statement || 'Not available.'}</Typography>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card sx={{ p:2, bgcolor:'background.paper', borderRadius: '4px' }}>
            <Typography variant="h6">COA List</Typography>
            {!coasResp || !coasResp.coas || coasResp.coas.length===0 ? (
              <Typography variant="body2" sx={{ color:'text.secondary' }}>No COAs available.</Typography>
            ) : (
              <List>
                {coasResp.coas.map(c=> (
                  <ListItem key={c.id}>
                    <Box sx={{ display:'flex', flexDirection:'column' }}>
                      <Typography variant="subtitle2">{c.title}</Typography>
                      <Typography variant="body2" sx={{ color:'text.secondary' }}>{c.rationale}</Typography>
                      <Button sx={{ mt:1 }} size="small" variant="outlined">Compare</Button>
                    </Box>
                  </ListItem>
                ))}
              </List>
            )}
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ p:2, bgcolor:'background.paper', borderRadius: '4px' }}>
            <Typography variant="h6">Recommendation</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>No recommendation selected.</Typography>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <COAComparisonView coas={coasResp?.coas || []} />
        </Grid>
      </Grid>
    </Box>
  )
}

