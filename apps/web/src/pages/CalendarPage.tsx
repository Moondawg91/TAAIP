import React, {useState} from 'react'
import { Box, Typography, TextField, Button, Paper } from '@mui/material'
import { createCalendarEvent } from '../api/client'

export default function CalendarPage(){
  const [title, setTitle] = useState('')
  const [startDt, setStartDt] = useState('')
  const [endDt, setEndDt] = useState('')

  async function handleCreate(){
    const res = await createCalendarEvent({ title, start_dt: startDt, end_dt: endDt })
    alert('Calendar event created: ' + res.id)
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
    </Box>
  )
}
