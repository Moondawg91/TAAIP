import React from 'react'
import { Box, Typography, Grid, Card, CardContent, Button } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

export default function HomePage(){
  return (
    <Box>
      <Box sx={{mb:2}}>
        <Typography variant="h4">TAAIP</Typography>
        <Typography variant="subtitle1" color="text.secondary">Talent Acquisition Analytics & Intelligence Platform</Typography>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6">Quick Links</Typography>
              <Box sx={{display:'flex', gap:1, mt:2}}>
                <Button variant="contained" component={RouterLink} to="/dashboards/command-center">Command Center</Button>
                <Button variant="outlined" component={RouterLink} to="/dashboards/scoreboard">Scoreboard</Button>
                <Button variant="outlined" component={RouterLink} to="/ingest">Ingest</Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1">Recent Activity</Typography>
              <Typography variant="body2" color="text.secondary">No recent activity available.</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
