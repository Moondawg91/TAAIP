import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText, Divider } from '@mui/material'
import { importJobs } from '../../api/client'

export default function TargetingDataPage(){
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ load() }, [])

  async function load(){
    setLoading(true)
    try{
      const j = await importJobs()
      setJobs(j || [])
    }catch(e){ console.error('load import jobs', e) }
    finally{ setLoading(false) }
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Targeting Data</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Recent import jobs and datasets.</Typography>

      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Recent Imports</Typography>
          <List>
            {(jobs || []).map((j:any)=> (
              <React.Fragment key={j.id}>
                <ListItem>
                  <ListItemText primary={j.dataset_key || j.filename || `import ${j.id}`} secondary={`status: ${j.status} • rows: ${j.row_count || 0} • errors: ${j.error_count || 0}` } />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
            {(!jobs || jobs.length===0) && <ListItem><ListItemText primary={loading ? 'Loading...' : 'No recent imports'} /></ListItem>}
          </List>
        </CardContent>
      </Card>
    </Box>
  )
}
