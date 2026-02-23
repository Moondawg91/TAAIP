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
import React, {useEffect, useState} from 'react'
import api from '../../api/client'
import { Box, Typography, Paper } from '@mui/material'

export default function MDMPWorkspacePage(){
  const [coas, setCoas] = useState([])
  useEffect(()=>{ let mounted=true; api.getCOARecommendations().then(r=>{ if(mounted) setCoas(r.coas||[]) }).catch(()=>{}); return ()=>{ mounted=false } },[])
  return (
    <Box sx={{p:3, bgcolor:'background.default', color:'text.primary'}}>
      <Typography variant="h4">MDMP Workspace</Typography>
      <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1, mt:2}}>
        <Typography variant="h6">Problem Statement</Typography>
        <Typography sx={{mt:1}}>Automatically generated problem statements and COAs appear below.</Typography>
        <Typography variant="h6" sx={{mt:2}}>COA List</Typography>
        {coas.length===0 ? <div>No COAs</div> : (
          <ul>{coas.map(c=> <li key={c.id}>{c.title} — {c.rationale}</li>)}</ul>
        )}
      </Paper>
    </Box>
  )
}
