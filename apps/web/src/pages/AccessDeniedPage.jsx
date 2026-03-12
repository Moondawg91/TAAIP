import React from 'react'
import { Box, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export default function AccessDeniedPage(){
  const nav = useNavigate()
  return (
    <Box sx={{ p:4 }}>
      <Typography variant="h4">Access denied</Typography>
      <Typography sx={{ mt:2 }}>You do not have permission to view this page or perform that action.</Typography>
      <Button sx={{ mt:2 }} variant="contained" onClick={()=>nav('/command-center')}>Return to Command Center</Button>
    </Box>
  )
}
