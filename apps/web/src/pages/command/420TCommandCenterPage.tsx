import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Card, Chip } from '@mui/material'
import * as api from '../../api/client'

export default function _420TCommandCenterPage(){
  const [market, setMarket] = useState(null)
  const [mission, setMission] = useState(null)
  const [resource, setResource] = useState(null)

  useEffect(()=>{
    (async ()=>{
      try{ setMarket(await api.getScoringMarketCapacity()) }catch(e){ setMarket(null) }
      try{ setMission(await api.getScoringMissionFeasibility()) }catch(e){ setMission(null) }
      try{ setResource(await api.getScoringMissionFeasibility()) }catch(e){ setResource(null) }
    })()
  },[])

  const Panel = ({title, data}) => (
    <Card sx={{ p:2, bgcolor: 'background.paper', borderRadius: '4px' }}>
      <Typography variant="subtitle2">{title}</Typography>
      {!data ? (
        <Typography variant="h6">No data</Typography>
      ) : (
        <Box sx={{ mt:1 }}>
          <Typography variant="h4">{data.score ?? 0}</Typography>
          <Chip label={data.tier || 'LOW'} color="default" />
        </Box>
      )}
    </Card>
  )

  return (
    <Box sx={{ p:3 }}>
      <Box sx={{ mb:2 }}>
        <Typography variant="h4">420T Command Center</Typography>
        <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>420T decision-support</Typography>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}><Panel title="Market Capacity" data={market} /></Grid>
        <Grid item xs={12} md={4}><Panel title="Mission Feasibility" data={mission} /></Grid>
        <Grid item xs={12} md={4}><Panel title="Resource Alignment" data={resource} /></Grid>
      </Grid>
      <Box sx={{ mt:2 }}>
        <Typography variant="h6">Top constraints</Typography>
        <Typography variant="body2" sx={{ color:'text.secondary' }}>No constraints detected.</Typography>
      </Box>
      <Box sx={{ mt:1 }}>
        <Typography variant="h6">Top opportunities</Typography>
        <Typography variant="body2" sx={{ color:'text.secondary' }}>No opportunities detected.</Typography>
      </Box>
    </Box>
  )
}
import React, {useEffect, useState} from 'react'
import api from '../../api/client'
import { Box, Typography, Paper, Grid, Button } from '@mui/material'

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
