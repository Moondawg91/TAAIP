import React, { useEffect, useState } from 'react'
import { Box, List, ListItem, Chip, Typography, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button } from '@mui/material'
import HomeSectionShell from './HomeSectionShell'
import { getHomeFlash, createHomeFlash, getMe } from '../../api/client'

export default function FlashBureauPanel(){
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ title:'', body:'', category:'MUST_KNOW', source:'', effective_date:'' })
  const [isMaster, setIsMaster] = useState(false)

  useEffect(()=>{ let cancelled=false; getHomeFlash().then(r=>{ if(!cancelled) setItems(r.items||[]) }).catch(()=>{}) ; getMe().then(m=>{ if(!cancelled && m && Array.isArray(m.permissions) && m.permissions.includes('*')) setIsMaster(true) }) ; return ()=>{ cancelled=true } },[])

  function refresh(){ getHomeFlash().then(r=>setItems(r.items||[])).catch(()=>{}) }

  async function submit(){
    try{
      await createHomeFlash(form)
      setOpen(false)
      setForm({ title:'', body:'', category:'MUST_KNOW', source:'', effective_date:'' })
      refresh()
    }catch(e){ console.error(e) }
  }

  return (
    <HomeSectionShell title="USAREC & 420T Flash Bureau" canPost={isMaster} onPost={()=>setOpen(true)}>
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

      <Dialog open={open} onClose={()=>setOpen(false)}>
        <DialogTitle>Post Flash</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={form.title} onChange={(e)=>setForm({...form, title:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Body" value={form.body} onChange={(e)=>setForm({...form, body:e.target.value})} multiline rows={4} sx={{ mt:1 }} />
          <TextField fullWidth label="Category" value={form.category} onChange={(e)=>setForm({...form, category:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Source" value={form.source} onChange={(e)=>setForm({...form, source:e.target.value})} sx={{ mt:1 }} />
          <TextField fullWidth label="Effective date (ISO)" value={form.effective_date} onChange={(e)=>setForm({...form, effective_date:e.target.value})} sx={{ mt:1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={submit}>Post</Button>
        </DialogActions>
      </Dialog>
    </HomeSectionShell>
  )
}
