import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Link, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import ReferenceRails from './ReferenceRails'
import { getHomeReferenceRails, createHomeReferenceRail, getMe } from '../../api/client'

export default function ReferenceRailsPanel(){
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ title:'', kind:'DOC', target:'' })
  const [isMaster, setIsMaster] = useState(false)

  useEffect(()=>{ let cancelled=false; getHomeReferenceRails().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; getMe().then(m=>{ if(!cancelled && m && Array.isArray(m.permissions) && m.permissions.includes('*')) setIsMaster(true) }) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeReferenceRails().then(r=>setItems(r.items||[])).catch(()=>{}) }

  async function submit(){
    try{
      await createHomeReferenceRail(form)
      setOpen(false)
      setForm({ title:'', kind:'DOC', target:'' })
      refresh()
    }catch(e){ console.error(e) }
  }

  return (
    <HomeSectionShell title="Quick Reference Rails" canPost={isMaster} onPost={()=>setOpen(true)}>
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

      <Dialog open={open} onClose={()=>setOpen(false)}>
        <DialogTitle>Add Reference Rail</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={form.title} onChange={(e)=>setForm({...form, title:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Kind (DOC|LINK|CALC)" value={form.kind} onChange={(e)=>setForm({...form, kind:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Target (route or URL)" value={form.target} onChange={(e)=>setForm({...form, target:e.target.value})} sx={{ mt:1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={submit}>Add</Button>
        </DialogActions>
      </Dialog>
    </HomeSectionShell>
  )
}
