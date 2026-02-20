import React, { useEffect, useState } from 'react'
import { Box, Typography, List, ListItem, ListItemText, Card, CardContent } from '@mui/material'
import api from '../../api/client'

export default function EventPerformancePage(){
  const [events, setEvents] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{ let mounted = true; setLoading(true); api.getEventsRollup().then(d=>{ if(!mounted) return; setEvents(d ? d.events || [] : [] ) }).catch(()=>{ if(mounted) setEvents([]) }).finally(()=> mounted && setLoading(false)); return ()=> mounted = false }, [])

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Event ROI & Performance</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Event-level ROI and outcomes.</Typography>
      <Card sx={{ mb:2 }}>
        <CardContent>
          {loading ? <Typography>Loading...</Typography> : (events && events.length ? (
            <List>
              {events.map(ev => (
                <ListItem key={ev.event_id || ev.id}>
                  <ListItemText primary={ev.name || ev.title} secondary={`Planned: ${ev.planned_cost || 0} • Actual: ${ev.actual_cost || 0} • Marketing: ${ev.marketing_cost || 0}`} />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography sx={{ color:'text.secondary' }}>No event updates published.</Typography>
          ))}
        </CardContent>
      </Card>
    </Box>
  )
}
