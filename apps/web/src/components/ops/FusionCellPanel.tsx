import React from 'react'
import { Box, Grid, Card, CardContent, Typography } from '@mui/material'

export default function FusionCellPanel({ meetings, actions, decisions, risks, onSelect, openDetail }: any){
  return (
    <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Typography variant="h6">Meetings</Typography>
          {meetings && meetings.length>0 ? meetings.map((m:any)=> (
            <Card key={m.id} sx={{ my:1 }} onClick={()=> openDetail({ title: m.title, type:'meeting', payload: m })}>
              <CardContent>
                <Typography variant="body1">{m.title}</Typography>
              </CardContent>
            </Card>
          )) : <Typography variant="body2">No meetings</Typography>}
        </Grid>
        <Grid item xs={6}>
          <Typography variant="h6">Action Items</Typography>
          {actions && actions.length>0 ? actions.map((a:any)=> (
            <Card key={a.id} sx={{ my:1 }} onClick={()=> openDetail({ title: a.title, type:'action', payload: a })}>
              <CardContent>
                <Typography variant="body1">{a.title}</Typography>
              </CardContent>
            </Card>
          )) : <Typography variant="body2">No actions</Typography>}
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt:1 }}>
        <Grid item xs={6}>
          <Typography variant="h6">Decisions</Typography>
          {decisions && decisions.length>0 ? decisions.map((d:any)=> (
            <Card key={d.id} sx={{ my:1 }} onClick={()=> openDetail({ title: d.summary, type:'decision', payload: d })}>
              <CardContent>
                <Typography variant="body2">{d.summary}</Typography>
              </CardContent>
            </Card>
          )) : <Typography variant="body2">No decisions</Typography>}
        </Grid>
        <Grid item xs={6}>
          <Typography variant="h6">Risks / Issues</Typography>
          {risks && risks.length>0 ? risks.map((r:any)=> (
            <Card key={r.id} sx={{ my:1 }} onClick={()=> openDetail({ title: r.title, type:'risk', payload: r })}>
              <CardContent>
                <Typography variant="body2">{r.title}</Typography>
              </CardContent>
            </Card>
          )) : <Typography variant="body2">No risks</Typography>}
        </Grid>
      </Grid>
    </Box>
  )
}
