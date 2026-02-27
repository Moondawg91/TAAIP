import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Typography, Chip } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import { getHomeMessages } from '../../api/client'

export default function MessagesPanel(){
  const [items, setItems] = useState([])
  // read-only home messages panel

  useEffect(()=>{ let cancelled=false; getHomeMessages().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeMessages().then(r=>setItems(r.items||[]) ).catch(()=>{}) }

  return (
    <HomeSectionShell title="Updates & Messages">
      <List dense sx={{ maxHeight:260, overflow:'auto', p:0 }}>
        {items.length===0 ? (<ListItem><Typography variant="body2" sx={{ color:'text.secondary' }}>No messages posted yet.</Typography></ListItem>) : items.map(i=> (
          <ListItem key={i.id} sx={{ py:0.5, display:'flex', flexDirection:'column', alignItems:'flex-start' }}>
            <Box sx={{ display:'flex', gap:1, alignItems:'center' }}>
              <Chip label={i.priority} size="small" sx={{ bgcolor:'transparent', color:'text.secondary' }} />
              <Typography variant="subtitle2">{i.title}</Typography>
            </Box>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>{i.body}</Typography>
          </ListItem>
        ))}
      </List>

      {/* Posting controls removed from home page — use Admin to create messages */}
    </HomeSectionShell>
  )
}
