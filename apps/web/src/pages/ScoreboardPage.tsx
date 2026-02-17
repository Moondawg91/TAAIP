import React from 'react'
import { Box, Typography, Card, CardContent } from '@mui/material'
import DashboardLayout from '../components/DashboardLayout'

export default function ScoreboardPage(){
  return (
    <DashboardLayout filters={<div/>} kpis={<div/>}>
      <Box>
        <Typography variant="h5">Company Standings</Typography>
        <Card sx={{mt:2}}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">No standings data available yet.</Typography>
          </CardContent>
        </Card>
      </Box>
    </DashboardLayout>
  )
}
