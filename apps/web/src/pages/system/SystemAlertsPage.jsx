import React, {useEffect, useState} from 'react'
import {Box, Typography, Paper, List, ListItem, ListItemText, Button} from '@mui/material'
import {getSystemAlerts} from '../../api/client'
import {useNavigate} from 'react-router-dom'

export default function SystemAlertsPage(){
  const [alerts, setAlerts] = useState(null)
  const nav = useNavigate()
  useEffect(()=>{ async function load(){ try{ setAlerts(await getSystemAlerts()) }catch(e){ setAlerts({alerts:{}, total:0}) } } load() },[])

  return (
    <Box>
      <Typography variant="h5" sx={{mb:2}}>System Alerts</Typography>
      <Paper sx={{p:2, bgcolor:'background.paper', borderRadius:1}}>
        <List>
          <ListItem>
            <ListItemText primary={`Import errors`} secondary={alerts ? alerts.alerts.import_errors : '0'} />
            <Button size="small" onClick={()=>nav('/imports')}>Import Center</Button>
          </ListItem>
          <ListItem>
            <ListItemText primary={`API errors`} secondary={alerts ? alerts.alerts.api_errors : '0'} />
          </ListItem>
          <ListItem>
            <ListItemText primary={`Proposals pending`} secondary={alerts ? alerts.alerts.proposals_pending : '0'} />
            <Button size="small" onClick={()=>nav('/system/proposals')}>View</Button>
          </ListItem>
        </List>
      </Paper>
    </Box>
  )
}
