import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Typography, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, Chip } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import { getHomeMessages, createHomeMessage, getMe } from '../../api/client'

export default function MessagesPanel(){
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ title:'', body:'', priority:'INFO' })
  const [isMaster, setIsMaster] = useState(false)

  useEffect(()=>{ let cancelled=false; getHomeMessages().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; getMe().then(m=>{ if(!cancelled && m && Array.isArray(m.permissions) && m.permissions.includes('*')) setIsMaster(true) }) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeMessages().then(r=>setItems(r.items||[])).catch(()=>{}) }

  async function submit(){
    try{
      await createHomeMessage(form)
      setOpen(false)
      setForm({ title:'', body:'', priority:'INFO' })
      refresh()
    }catch(e){ console.error(e) }
  }

  return (
    <HomeSectionShell title="Updates & Messages" canPost={isMaster} onPost={()=>setOpen(true)}>
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

      <Dialog open={open} onClose={()=>setOpen(false)}>
        <DialogTitle>Post Message</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={form.title} onChange={(e)=>setForm({...form, title:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Body" value={form.body} onChange={(e)=>setForm({...form, body:e.target.value})} multiline rows={4} sx={{ mt:1 }} />
          <TextField fullWidth label="Priority (INFO|IMPORTANT|ACTION)" value={form.priority} onChange={(e)=>setForm({...form, priority:e.target.value})} sx={{ mt:1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={submit}>Post</Button>
        </DialogActions>
      </Dialog>
    </HomeSectionShell>
  )
}
