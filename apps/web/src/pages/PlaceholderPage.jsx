import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Paper, Grid, List, ListItem, ListItemText, Divider } from '@mui/material'
import { getHealth, getMe, listDocuments, importJobs } from '../api/client'

export default function PlaceholderPage({ title = 'Coming Soon', subtitle = 'This page is wired and ready for future implementation.' }) {
  const [health, setHealth] = useState(null)
  const [me, setMe] = useState(null)
  const [docs, setDocs] = useState([])
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      try {
        const [h, u, d, j] = await Promise.allSettled([getHealth(), getMe(), listDocuments(), importJobs()])
        if (!mounted) return
        setHealth(h.status === 'fulfilled' ? h.value : null)
        setMe(u.status === 'fulfilled' ? u.value : null)
        setDocs(d.status === 'fulfilled' ? (d.value || []).slice(0,10) : [])
        setJobs(j.status === 'fulfilled' ? (j.value || []).slice(0,10) : [])
      } catch (e) {
        console.error('load error', e)
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  return (
    <Box sx={{ minHeight: '100vh', px: 4, py: 6, bgcolor: 'background.default', color: 'text.primary' }}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
      <Typography variant="subtitle1" sx={{ color: 'text.secondary', mt: 1 }}>{subtitle}</Typography>

      <Grid container spacing={2} sx={{ mt: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">System Health</Typography>
            <Divider sx={{ my:1 }} />
            <Typography variant="body2">Status: {health ? (health.status || 'ok') : (loading ? 'loading…' : 'unavailable')}</Typography>
            {health && health.uptime && <Typography variant="caption" sx={{ display:'block', mt:1 }}>Uptime: {health.uptime}</Typography>}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Current User</Typography>
            <Divider sx={{ my:1 }} />
            {me ? (
              <Box>
                <Typography variant="body2">{me.username || me.display_name || 'User'}</Typography>
                <Typography variant="caption" sx={{ display:'block', color:'text.secondary' }}>{(me.roles||[]).join(', ')}</Typography>
              </Box>
            ) : (
              <Typography variant="body2">Not signed in</Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Quick Actions</Typography>
            <Divider sx={{ my:1 }} />
            <Button variant="contained" sx={{ mr:1 }} href="/import-center">Import Center</Button>
            <Button variant="outlined" href="/resources/doc-library">Document Library</Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Recent Documents</Typography>
            <Divider sx={{ my:1 }} />
            <List dense>
              {docs.length ? docs.map(d => (
                <ListItem key={d.id} secondaryAction={<a href={(d.id && `/api/documents/${d.id}/download`) || '#'} target="_blank" rel="noreferrer">Download</a>}>
                  <ListItemText primary={d.filename || d.file || 'file'} secondary={d.uploaded_at || ''} />
                </ListItem>
              )) : <Typography variant="body2">No documents</Typography>}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Recent Import Jobs</Typography>
            <Divider sx={{ my:1 }} />
            <List dense>
              {jobs.length ? jobs.map(j => (
                <ListItem key={j.id}>
                  <ListItemText primary={j.id} secondary={`${j.dataset_key || ''} • ${j.status || ''}`} />
                </ListItem>
              )) : <Typography variant="body2">No recent import jobs</Typography>}
            </List>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt:3 }}>
        <Button variant="contained" color="primary" onClick={() => window.location.reload()}>Refresh</Button>
      </Box>
    </Box>
  )
}
