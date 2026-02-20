import React, {useEffect, useState} from 'react'
import {Box, Typography, Paper, Grid, Button} from '@mui/material'
import {getSystemFreshness, getSystemAlerts, getSystemStatus} from '../../api/client'

export default function SystemStatusPage(){
  const [fresh, setFresh] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [status, setStatus] = useState({mode:'normal'})

  useEffect(()=>{ async function load(){ try{ setFresh(await getSystemFreshness()) }catch(e){} try{ setAlerts(await getSystemAlerts()) }catch(e){} try{ setStatus(await getSystemStatus()) }catch(e){} } load() },[])

  return (
    <Box>
      <Typography variant="h5" sx={{mb:2}}>System Status</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{p:2, bgcolor:'background.paper', borderRadius:1}}>
            <Typography variant="subtitle2">Mode</Typography>
            <Typography variant="body1">{status && status.mode}</Typography>
            {status && status.mode==='maintenance' && (
              <Typography variant="caption" sx={{display:'block', mt:1}}>Maintenance mode active (controlled via environment variable or system settings)</Typography>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{p:2, bgcolor:'background.paper', borderRadius:1}}>
            <Typography variant="subtitle2">Data Freshness</Typography>
            <Typography variant="body1">{fresh && fresh.data_as_of ? fresh.data_as_of : 'Data not available'}</Typography>
            <Typography variant="subtitle2" sx={{mt:1}}>Last Import</Typography>
            <Typography variant="body2">{fresh && fresh.last_import_at ? `${fresh.last_import_at} (${fresh.last_import_job_id || ''})` : 'n/a'}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{p:2, bgcolor:'background.paper', borderRadius:1}}>
            <Typography variant="subtitle2">Alerts</Typography>
            <Typography variant="body2">{alerts ? JSON.stringify(alerts.alerts) : 'loading'}</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
