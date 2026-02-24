import React from 'react'
import { Box, Typography, Grid } from '@mui/material'
import FlashBureauPanel from '../components/home/FlashBureauPanel'
import MessagesPanel from '../components/home/MessagesPanel'
import RecognitionPanel from '../components/home/RecognitionPanel'
import UpcomingPanel from '../components/home/UpcomingPanel'
import ReferenceRailsPanel from '../components/home/ReferenceRailsPanel'
import VirtualTechnicianBrief from '../components/home/VirtualTechnicianBrief'
import { Button, Link } from '@mui/material'

export default function HomePage(){
  // Quick Actions + System Readiness on left; Strategic + Upcoming center; Reference + Data Status right
  const quickActions = [
    { label: '420T Command Center', href: '/command-center/420t' },
    { label: 'MDMP Workspace', href: '/command-center/mdmp' },
    { label: 'Market Intelligence', href: '/operations/market-intelligence' },
    { label: 'School Recruiting', href: '/school-recruiting/program' },
    { label: 'Imports Center', href: '/import-center' }
  ]

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary', p:3 }}>
      <Box sx={{ maxWidth: 1400, mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb:2 }}>
          <Typography variant="h4">Home — 420T Command Decision Support Portal</Typography>
          <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>Command decision support for 420T operations</Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
              <Box sx={{ p:0 }}>
                <Box sx={{ mb:1 }}>
                  {quickActions.map(a => (<Button key={a.href} size="small" variant="outlined" href={a.href} sx={{ mr:1, mb:1 }}>{a.label}</Button>))}
                </Box>
                <Box sx={{ mt:1 }}>
                  <Typography variant="h6">System Readiness</Typography>
                  {/* keep System Readiness concise */}
                  <Box sx={{ mt:1 }}><Typography variant="body2" sx={{ color:'text.secondary' }}>Check platform readiness and import missing datasets in the Imports Center.</Typography></Box>
                </Box>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
              <FlashBureauPanel />
              <MessagesPanel />
              <RecognitionPanel />
            </Box>
          </Grid>

          <Grid item xs={12} md={3}>
            <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
              <UpcomingPanel />
              <ReferenceRailsPanel />
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}
