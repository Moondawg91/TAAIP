import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Chip, Typography } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import { getHomeFlash } from '../../api/client'

export default function FlashBureauPanel(){
  const [items, setItems] = useState([])
  // read-only home panel

  useEffect(()=>{ let cancelled=false; getHomeFlash().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeFlash().then(r=>setItems(r.items||[])).catch(()=>{}) }

  return (
    <HomeSectionShell title="USAREC & 420T Flash Bureau">
      <List dense sx={{ maxHeight:260, overflow:'auto', p:0 }}>
        {items.length===0 ? (<ListItem><Typography variant="body2" sx={{ color:'text.secondary' }}>No Flash Bureau items posted yet.</Typography></ListItem>) : items.map(i=> (
          <ListItem key={i.id} sx={{ py:0.5, display:'flex', flexDirection:'column', alignItems:'flex-start' }}>
            <Box sx={{ display:'flex', gap:1, alignItems:'center' }}>
              <Chip label={i.category} size="small" sx={{ bgcolor:'transparent', color:'text.secondary' }} />
              <Typography variant="subtitle2">{i.title}</Typography>
            </Box>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>{i.body}</Typography>
            {i.effective_date && <Typography variant="caption" sx={{ color:'text.secondary' }}>{i.effective_date}</Typography>}
          </ListItem>
        ))}
      </List>

      {/* Posting controls removed from home page — use Admin to create flash items */}
    </HomeSectionShell>
  )
}
