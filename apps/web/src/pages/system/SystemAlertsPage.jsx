import React, {useEffect, useState} from 'react'
import {Box, Typography, Paper, List, ListItem, ListItemText, Button} from '@mui/material'
import {useTheme} from '@mui/material/styles'
import {getSystemAlerts, getSystemAlertsList} from '../../api/client'
import {useNavigate} from 'react-router-dom'

export default function SystemAlertsPage(){
  const theme = useTheme()
  const [alerts, setAlerts] = useState(null)
  const nav = useNavigate()
  useEffect(()=>{ async function load(){ try{ setAlerts(await getSystemAlerts()) }catch(e){ setAlerts({alerts:{}, total:0}) } } load() },[])

  const cardBg = theme.palette.background.default

  return (
    <Box>
      <Typography variant="h5" sx={{mb:2}}>System Alerts</Typography>
      <Paper sx={{p:2, bgcolor: cardBg, borderRadius:'4px'}}>
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
