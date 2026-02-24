import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Typography, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import { getHomeUpcoming, createHomeUpcoming, getMe } from '../../api/client'

export default function UpcomingPanel(){
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ title:'', body:'', event_date:'', tag:'' })
  const [isMaster, setIsMaster] = useState(false)

  useEffect(()=>{ let cancelled=false; getHomeUpcoming().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; getMe().then(m=>{ if(!cancelled && m && Array.isArray(m.permissions) && m.permissions.includes('*')) setIsMaster(true) }) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeUpcoming().then(r=>setItems(r.items||[])).catch(()=>{}) }

  async function submit(){
    try{
      await createHomeUpcoming(form)
      setOpen(false)
      setForm({ title:'', body:'', event_date:'', tag:'' })
      refresh()
    }catch(e){ console.error(e) }
  }

  return (
    <HomeSectionShell title="Upcoming / Professional Development" canPost={isMaster} onPost={()=>setOpen(true)}>
      <List dense sx={{ maxHeight:260, overflow:'auto', p:0 }}>
        {items.length===0 ? (<ListItem><Typography variant="body2" sx={{ color:'text.secondary' }}>No upcoming items</Typography></ListItem>) : items.map(i=> (
          <ListItem key={i.id} sx={{ py:0.5, display:'flex', flexDirection:'column', alignItems:'flex-start' }}>
            <Typography variant="subtitle2">{i.title} <Typography component="span" variant="caption" sx={{ color:'text.secondary' }}> — {i.event_date}</Typography></Typography>
            <Typography variant="body2" sx={{ color:'text.secondary' }}>{i.body}</Typography>
          </ListItem>
        ))}
      </List>

      <Dialog open={open} onClose={()=>setOpen(false)}>
        <DialogTitle>Post Upcoming Item</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={form.title} onChange={(e)=>setForm({...form, title:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Body" value={form.body} onChange={(e)=>setForm({...form, body:e.target.value})} multiline rows={3} sx={{ mt:1 }} />
          <TextField fullWidth label="Event date (ISO)" value={form.event_date} onChange={(e)=>setForm({...form, event_date:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Tag (WOPD|COURSE|CERT|DEADLINE|EVENT)" value={form.tag} onChange={(e)=>setForm({...form, tag:e.target.value})} sx={{ mt:1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={submit}>Post</Button>
        </DialogActions>
      </Dialog>
    </HomeSectionShell>
  )
}
