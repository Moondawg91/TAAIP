import React, { useEffect, useState } from 'react'
import { AppBar, Toolbar, Typography, Box, Chip } from '@mui/material'
import api from '../api/client'

export default function TopHeader({ title }: { title?: string }){
  const [status, setStatus] = useState('unknown')
  useEffect(()=>{
    let mounted = true
    api.getHealth().then(()=> mounted && setStatus('online')).catch(()=> mounted && setStatus('offline'))
    return ()=>{ mounted = false }
  }, [])

  return (
    <AppBar position="static" color="default" elevation={0} sx={{borderBottom:'1px solid #e6e9ef'}}>
      <Toolbar sx={{minHeight:56}}>
        <Box sx={{flex:1}}>
          <Typography variant="h6">{title || 'TAAIP'}</Typography>
        </Box>
        <Box>
          <Chip label={`API: ${status}`} size="small" color={status==='online'?'success':'default'} />
        </Box>
      </Toolbar>
    </AppBar>
  )
}
