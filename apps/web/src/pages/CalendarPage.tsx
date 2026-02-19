import React, {useState, useEffect} from 'react'
import { Box, Typography, TextField, Button, Paper } from '@mui/material'
import { createCalendarEvent, listCalendarEvents, deleteCalendarEvent } from '../api/client'

export default function CalendarPage(){
  const [title, setTitle] = useState('')
  const [startDt, setStartDt] = useState('')
  const [endDt, setEndDt] = useState('')
  const [events, setEvents] = useState([])

  useEffect(()=>{ loadEvents() }, [])

  async function loadEvents(){
    try{
      const res = await listCalendarEvents()
      setEvents(res || [])
    }catch(err){
      console.error('loadEvents', err)
    }
  }

  async function handleCreate(){
    const res = await createCalendarEvent({ title, start_dt: startDt, end_dt: endDt })
    setTitle('')
    setStartDt('')
    setEndDt('')
    await loadEvents()
    alert('Calendar event created: ' + res.id)
  }

  async function handleDelete(id){
    if(!confirm('Delete this event?')) return
    try{
      await deleteCalendarEvent(id)
      await loadEvents()
    }catch(err){
      console.error('delete', err)
      alert('Delete failed')
    }
  }

  return (
    <Box sx={{p:3}}>
      <Typography variant="h5">Calendar</Typography>
      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Create Event</Typography>
        <TextField label="Title" value={title} onChange={(e)=>setTitle(e.target.value)} fullWidth />
        <TextField label="Start" value={startDt} onChange={(e)=>setStartDt(e.target.value)} fullWidth sx={{mt:1}} />
        <TextField label="End" value={endDt} onChange={(e)=>setEndDt(e.target.value)} fullWidth sx={{mt:1}} />
        <Box sx={{mt:1}}>
          <Button variant="contained" onClick={handleCreate}>Create Event</Button>
        </Box>
      </Paper>
      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Events</Typography>
        {events.map((e:any)=> (
          <Paper key={e.id} sx={{p:1, mt:1}}>
            <Box sx={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
              <Box>
                <Typography>{e.title}</Typography>
                <Typography variant="caption">{e.start_dt} - {e.end_dt}</Typography>
              </Box>
              <Box>
                <Button color="error" onClick={()=>handleDelete(e.id)}>Delete</Button>
              </Box>
            </Box>
          </Paper>
        ))}
      </Paper>
    </Box>
  )
}
