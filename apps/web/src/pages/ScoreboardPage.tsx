import React from 'react'
import { Box, Typography, Paper } from '@mui/material'
import DashboardLayout from '../components/DashboardLayout'

export default function ScoreboardPage(){
  return (
    <DashboardLayout filters={<div/>}>
      <Box>
        <Typography variant="h5">Company Standings</Typography>
        <Box sx={{display:'grid', gridTemplateColumns:'2fr 1fr', gap:2, mt:2}}>
          <Box>
            <Paper sx={{p:2}}>
              <Typography variant="subtitle1">Primary Metrics</Typography>
              <Typography variant="body2" color="text.secondary">No standings data available yet.</Typography>
            </Paper>
            <Paper sx={{p:2, mt:2}}>
              <Typography variant="subtitle1">Details</Typography>
              <Typography variant="body2" color="text.secondary">No details available.</Typography>
            </Paper>
          </Box>
          <Box>
            <Paper sx={{p:2}}>
              <Typography variant="subtitle1">Recent Activity</Typography>
              <Typography variant="body2" color="text.secondary">No activity.</Typography>
            </Paper>
          </Box>
        </Box>
      </Box>
    </DashboardLayout>
  )
}
