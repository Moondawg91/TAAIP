import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Link, Typography } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import ReferenceRails from './ReferenceRails'
import { getHomeReferenceRails } from '../../api/client'

export default function ReferenceRailsPanel(){
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ title:'', kind:'DOC', target:'' })

  useEffect(()=>{ let cancelled=false; getHomeReferenceRails().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeReferenceRails().then(r=>setItems(r.items||[]) ).catch(()=>{}) }

  return (
    <HomeSectionShell title="Quick Reference Rails">
      {items.length===0 ? (
        <Typography variant="body2" sx={{ color:'text.secondary' }}>No reference rails configured.</Typography>
      ) : (
        <List dense disablePadding>
          {items.map(it => (
            <ListItem key={it.id} sx={{ py:0.5 }}>
              <Link href={it.target}>{it.title}</Link>
            </ListItem>
          ))}
        </List>
      )}

      {/* Posting controls removed from home page — use Admin to add reference rails */}
    </HomeSectionShell>
  )
}
