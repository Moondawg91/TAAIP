import React from 'react'
import { Box, Typography, Button, List, ListItem, ListItemText, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material'
import api from '../../api/client'
import { useScope } from '../../contexts/ScopeContext'

export default function CommandPrioritiesPage(){
  const { scope } = useScope()
  const [loading, setLoading] = React.useState(true)
  const [priorities, setPriorities] = React.useState([])
  const [open, setOpen] = React.useState(false)
  const [edit, setEdit] = React.useState(null)
  const [title, setTitle] = React.useState('')

  React.useEffect(()=>{
    let mounted = true
    setLoading(true)
    api.listCommandPriorities(scope).then(r=>{
      if(!mounted) return
      setPriorities(r || [])
    }).catch(()=>{}).finally(()=> mounted && setLoading(false))
    return ()=>{ mounted = false }
  }, [scope])

  function openNew(){ setEdit(null); setTitle(''); setOpen(true) }
  function openEdit(p){ setEdit(p); setTitle(p.title||''); setOpen(true) }
  async function save(){
    try{
      if(edit && edit.id){
        await api.updateCommandPriority(edit.id, { title })
      } else {
        await api.createCommandPriority({ title })
      }
      const refreshed = await api.listCommandPriorities(scope)
      setPriorities(refreshed||[])
    }catch(e){}
    setOpen(false)
  }

  return (
    <Box>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', mb:2 }}>
        <Typography variant="h4">Command Priorities</Typography>
        <Button variant="contained" onClick={openNew}>New Priority</Button>
      </Box>
      <List>
        {loading ? <ListItem><ListItemText primary="Loading..." /></ListItem> : (priorities.length ? priorities.map(p=> (
          <ListItem key={p.id} secondaryAction={<Button onClick={()=>openEdit(p)}>Edit</Button>}>
            <ListItemText primary={p.title} secondary={p.description} />
          </ListItem>
        )) : <ListItem><ListItemText primary="No priorities" /></ListItem>)}
      </List>

      <Dialog open={open} onClose={()=>setOpen(false)}>
        <DialogTitle>{edit ? 'Edit Priority' : 'New Priority'}</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={title} onChange={(e)=>setTitle(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setOpen(false)}>Cancel</Button>
          <Button onClick={save} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
