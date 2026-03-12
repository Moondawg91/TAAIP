import React, {useEffect, useState} from 'react'
import api from '../../api/client'
import { Box, Typography, Paper, Grid } from '@mui/material'

export default function _420TCommandCenterPage(){
  const [marketScore, setMarketScore] = useState(null)
  const [missionScore, setMissionScore] = useState(null)
  const [coas, setCoas] = useState([])

  useEffect(()=>{
    let mounted = true
    api.getMarketCapacityScore().then(r=>{ if(mounted) setMarketScore(r) }).catch(()=>{})
    api.getMissionFeasibility().then(r=>{ if(mounted) setMissionScore(r) }).catch(()=>{})
    api.getCOARecommendations().then(r=>{ if(mounted) setCoas(r.coas || []) }).catch(()=>{})
    return ()=>{ mounted = false }
  },[])

  return (
    <Box sx={{p:3, bgcolor:'background.default', color:'text.primary'}}>
      <Typography variant="h4">420T Command Center</Typography>
      <Grid container spacing={2} sx={{mt:2}}>
        <Grid item xs={12} md={6}>
          <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
            <Typography variant="h6">Market Capacity</Typography>
            {marketScore ? <div>Score: {marketScore.score} — Tier: {marketScore.tier}</div> : <div>No data</div>}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
            <Typography variant="h6">Mission Feasibility</Typography>
            {missionScore ? <div>Score: {missionScore.score} — Tier: {missionScore.tier}</div> : <div>No data</div>}
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
            <Typography variant="h6">COA Recommendations</Typography>
            {coas.length===0 ? <div>No COAs generated</div> : (
              <ul>
                {coas.map(c=> <li key={c.id}><b>{c.title}</b> — {c.rationale}</li>)}
              </ul>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
