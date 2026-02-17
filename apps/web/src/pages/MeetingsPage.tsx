import React, {useState} from 'react'
import { Box, Typography, TextField, Button, Paper } from '@mui/material'
import { createMeeting } from '../api/client'

export default function MeetingsPage(){
  const [title, setTitle] = useState('')
  const [dateTime, setDateTime] = useState('')

  async function handleCreate(){
    const res = await createMeeting({ title, date_time: dateTime, meeting_type: 'working_group' })
    alert('Meeting created: ' + res.id)
  }

  return (
    <Box sx={{p:3}}>
      <Typography variant="h5">Meetings</Typography>
      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Create Meeting</Typography>
        <TextField label="Title" value={title} onChange={(e)=>setTitle(e.target.value)} fullWidth />
        <TextField label="Date/Time" value={dateTime} onChange={(e)=>setDateTime(e.target.value)} fullWidth sx={{mt:1}} />
        <Box sx={{mt:1}}>
          <Button variant="contained" onClick={handleCreate}>Create Meeting</Button>
        </Box>
      </Paper>
    </Box>
  )
}
