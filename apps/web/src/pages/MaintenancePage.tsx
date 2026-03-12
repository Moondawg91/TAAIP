import React from 'react'
import { Box, Typography, Paper, Button } from '@mui/material'

export default function MaintenancePage() {
  return (
    <Box display="flex" alignItems="center" justifyContent="center" height="100vh" bgcolor="#121212">
      <Paper elevation={3} style={{ padding: 32, maxWidth: 680 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Scheduled Maintenance
        </Typography>
        <Typography variant="body1" paragraph>
          The system is currently in maintenance mode. We are performing updates to improve stability and add features. Please check back shortly.
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          If you need urgent access, contact your administrator.
        </Typography>
        <Button variant="contained" color="primary" href="/help/system-status">System Status</Button>
      </Paper>
    </Box>
  )
}
