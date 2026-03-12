import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Paper, Grid, List, ListItem, ListItemText, Divider, Link } from '@mui/material'
import { getHealth, getMe, listDocuments, importJobs } from '../api/client'

export default function NotLoadedPage({ title = 'Not Loaded', subtitle = 'Data not loaded. Load datasets in Data Hub.' }) {
  return (
    <Box sx={{ minHeight: '100vh', px: 4, py: 6, bgcolor: 'background.default', color: 'text.primary' }}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
      <Typography variant="subtitle1" sx={{ color: 'text.secondary', mt: 1 }}>{subtitle}</Typography>

      <Grid container spacing={2} sx={{ mt: 3 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Not Loaded</Typography>
            <Divider sx={{ my:1 }} />
            <Typography variant="body2" sx={{ mb:1 }}>This page has no operational datasets available. Load datasets in the Data Hub to enable full functionality.</Typography>
            <Link href="/data-hub" variant="button" sx={{ mr:1 }}>Go to Data Hub</Link>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Why you see this</Typography>
            <Divider sx={{ my:1 }} />
            <List dense>
              <ListItem>
                <ListItemText primary="No datasets imported" secondary="Required source tables are empty or missing." />
              </ListItem>
              <ListItem>
                <ListItemText primary="RBAC" secondary="You may need proper permissions to view this page's data." />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt:3 }}>
        <Button variant="text" onClick={() => window.location.reload()}>Refresh</Button>
      </Box>
    </Box>
  )
}

  export { NotLoadedPage }
