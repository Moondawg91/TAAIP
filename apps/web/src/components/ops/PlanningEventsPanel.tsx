import React from 'react'
import { Box, Button, Select, MenuItem, Grid, Card, CardContent, Typography } from '@mui/material'

export default function PlanningEventsPanel({ quarter, onQuarterChange, events, tasks, onCreateEvent, onSelectEvent, onSelectTask, openDetail }: any){
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap:2, height: '100%' }}>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <Box>
          <Select value={quarter} onChange={(e)=> onQuarterChange(e.target.value)} size="small">
            <MenuItem value={'Q1'}>Q1</MenuItem>
            <MenuItem value={'Q2'}>Q2</MenuItem>
            <MenuItem value={'Q3'}>Q3</MenuItem>
            <MenuItem value={'Q4'}>Q4</MenuItem>
          </Select>
        </Box>
        <Button variant="contained" onClick={onCreateEvent}>Create Event</Button>
      </Box>

      <Grid container spacing={2} sx={{ flex:1 }}>
        <Grid item xs={8} sx={{ height: '100%' }}>
          <Box sx={{ display:'grid', gridTemplateColumns: 'repeat(2,1fr)', gap:2 }}>
            {events && events.length>0 ? events.map((e:any)=> (
              <Card key={e.id} onClick={()=> openDetail({ title: e.name, type: 'event', payload: e })} sx={{ cursor:'pointer' }}>
                <CardContent>
                  <Typography variant="subtitle1">{e.name}</Typography>
                  <Typography variant="caption">{e.start} → {e.end}</Typography>
                </CardContent>
              </Card>
            )) : <Typography variant="body2" sx={{ p:2 }}>No events found for this quarter.</Typography>}
          </Box>
        </Grid>
        <Grid item xs={4} sx={{ height: '100%' }}>
          <Box sx={{ display:'flex', flexDirection:'column', gap:1 }}>
            <Typography variant="subtitle2">Tasks</Typography>
            {tasks && tasks.length>0 ? tasks.map((t:any)=> (
              <Card key={t.id} onClick={()=> openDetail({ title: t.title, type: 'task', payload: t })} sx={{ cursor:'pointer' }}>
                <CardContent>
                  <Typography variant="body2">{t.title}</Typography>
                </CardContent>
              </Card>
            )) : <Typography variant="body2">No tasks</Typography>}
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}
