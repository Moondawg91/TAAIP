import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Typography } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import { getHomeUpcoming } from '../../api/client'

export default function UpcomingPanel(){
  const [items, setItems] = useState([])
  // read-only upcoming panel

  useEffect(()=>{ let cancelled=false; getHomeUpcoming().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeUpcoming().then(r=>setItems(r.items||[]) ).catch(()=>{}) }

  return (
    <HomeSectionShell title="Upcoming / Professional Development">
      <List dense sx={{ maxHeight:260, overflow:'auto', p:0 }}>
        {items.length===0 ? (<ListItem><Typography variant="body2" sx={{ color:'text.secondary' }}>No upcoming items</Typography></ListItem>) : items.map(i=> (
          <ListItem key={i.id} sx={{ py:0.5, display:'flex', flexDirection:'column', alignItems:'flex-start' }}>
            <Typography variant="subtitle2">{i.title} <Typography component="span" variant="caption" sx={{ color:'text.secondary' }}> — {i.event_date}</Typography></Typography>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>{i.body}</Typography>
          </ListItem>
        ))}
      </List>

      {/* Posting controls removed from home page — use Admin to create upcoming items */}
    </HomeSectionShell>
  )
}
