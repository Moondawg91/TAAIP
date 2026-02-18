import React, { useEffect, useState } from 'react'
import { Box, Button, TextField, Typography, Card, CardContent, CardActions, Grid, IconButton, MenuItem, Select, FormControl, InputLabel, Chip, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import { listCommandPriorities, createCommandPriority, updateCommandPriority, deleteCommandPriority, listLOEsForScope, listPriorityLOEs, assignLOEToPriority, unassignLOEFromPriority, getCurrentUserFromToken } from '../../api/client'
import { useScope } from '../../contexts/ScopeContext'

export default function CommandPrioritiesPage(){
  const [priorities, setPriorities] = useState([])
  const [loes, setLoes] = useState([])
  const [loading, setLoading] = useState(false)
  const [userRoles, setUserRoles] = useState([])
  const [assignOpen, setAssignOpen] = useState(false)
  const [assignPriority, setAssignPriority] = useState<any>(null)
  const [assignAvailable, setAssignAvailable] = useState<any[]>([])
  const [selectedLoe, setSelectedLoe] = useState<string | number | null>(null)
  const [editOpen, setEditOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ title:'', description:'', rank:0 })

  useEffect(()=>{ refresh() }, [])
  const { scope } = useScope()

  useEffect(()=>{
    const u = getCurrentUserFromToken()
    setUserRoles((u && u.roles) || [])
  }, [])

  async function refresh(){
    setLoading(true)
    try{
      const p = await listCommandPriorities(scope) || []
      const allLoes = await listLOEsForScope(scope) || []
      // load assigned LOEs for each priority
      const withLoes = await Promise.all((p || []).slice(0,10).map(async (pr:any) => {
        try{
          const assigned = await listPriorityLOEs(pr.id, scope) || []
          pr.loes = assigned
        }catch(e){ pr.loes = [] }
        return pr
      }))
      setPriorities(withLoes)
      setLoes(allLoes)
    }catch(e){
      console.error(e)
    }finally{ setLoading(false) }
  }

  async function handleCreate(){
    if(priorities.length >= 3) return alert('Maximum of 3 priorities in UI')
    const payload = { title: form.title || 'New Priority', description: form.description || '', rank: form.rank || 0 }
    const res = await createCommandPriority(payload)
    setForm({ title:'', description:'', rank:0 })
    refresh()
    setEditOpen(false)
  }

  async function handleUpdate(){
    if(!editing) return
    await updateCommandPriority(editing.id, form)
    setEditing(null)
    setForm({ title:'', description:'', rank:0 })
    setEditOpen(false)
    refresh()
  }

  async function handleDelete(id){
    if(!confirm('Delete priority?')) return
    await deleteCommandPriority(id)
    refresh()
  }

  async function openEdit(p){
    setEditing(p)
    setForm({ title: p.title || '', description: p.description || '', rank: p.rank || 0 })
    setEditOpen(true)
  }

  async function handleAssign(priority){
    const assigned = await listPriorityLOEs(priority.id, scope) || []
    const assignedIds = (assigned || []).map(a=>a.id)
    const available = loes.filter(l=>!assignedIds.includes(l.id)).slice(0,50)
    if(assigned.length >= 5) return alert('Priority already has 5 LOEs')
    if(available.length===0) return alert('No available LOEs to assign')
    setAssignPriority(priority)
    setAssignAvailable(available)
    setSelectedLoe(available[0]?.id ?? null)
    setAssignOpen(true)
  }

  async function confirmAssign(){
    if(!assignPriority || !selectedLoe) return
    await assignLOEToPriority(assignPriority.id, selectedLoe)
    setAssignOpen(false)
    setAssignPriority(null)
    setAssignAvailable([])
    setSelectedLoe(null)
    refresh()
  }

  async function handleUnassign(priority, loe){
    if(!confirm('Remove LOE from priority?')) return
    await unassignLOEFromPriority(priority.id, loe.id)
    refresh()
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', mb:3 }}>
        <div>
          <Typography variant="h5">Command Priorities</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Configure up to 3 commander priorities and assign LOEs (max 5 each).</Typography>
        </div>
        <div>
          <Button startIcon={<AddIcon />} variant="contained" color="primary" onClick={()=>{ setEditing(null); setForm({ title:'', description:'', rank:0 }); setEditOpen(true) }} disabled={!userRoles.includes('usarec_admin') && !userRoles.includes('commander')}>New Priority</Button>
        </div>
      </Box>

      <Grid container spacing={2}>
        {priorities.map((p:any)=> (
          <Grid item xs={12} md={4} key={p.id}>
            <Card sx={{ bgcolor:'background.paper', color:'text.primary' }}>
              <CardContent>
                <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                  <Typography variant="h6">{p.title || 'Untitled'}</Typography>
                  <Box>
                    <IconButton size="small" onClick={()=>openEdit(p)} sx={{ color:'text.secondary' }} disabled={!userRoles.includes('usarec_admin') && !userRoles.includes('commander')}><EditIcon /></IconButton>
                    <IconButton size="small" onClick={()=>handleDelete(p.id)} sx={{ color:'text.secondary' }} disabled={!userRoles.includes('usarec_admin')}><DeleteIcon /></IconButton>
                  </Box>
                </Box>
                <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>{p.description}</Typography>

                <Box sx={{ mt:2 }}>
                  <Typography variant="subtitle2" sx={{ color:'text.secondary' }}>Assigned LOEs</Typography>
                  <Box sx={{ display:'flex', gap:1, flexWrap:'wrap', mt:1 }}>
                    {(p.loes || []).map((l:any)=>(
                      <Chip key={l.id} label={l.title || l.name || 'LOE'} onDelete={()=>handleUnassign(p,l)} />
                    ))}
                    <Button size="small" onClick={()=>handleAssign(p)} disabled={(p.loes||[]).length>=5} sx={{ ml:1 }}>Assign LOE</Button>
                  </Box>
                </Box>

              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={editOpen} onClose={()=>setEditOpen(false)}>
        <DialogTitle>{editing ? 'Edit Priority' : 'New Priority'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display:'flex', flexDirection:'column', gap:2, width:480, mt:1 }}>
            <TextField label="Title" value={form.title} onChange={e=>setForm(s=>({ ...s, title: e.target.value }))} fullWidth />
            <TextField label="Description" value={form.description} onChange={e=>setForm(s=>({ ...s, description: e.target.value }))} fullWidth multiline rows={3} />
            <TextField label="Rank" type="number" value={form.rank} onChange={e=>setForm(s=>({ ...s, rank: parseInt(e.target.value || '0',10) }))} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setEditOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={editing ? handleUpdate : handleCreate}>{editing ? 'Save' : 'Create'}</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={assignOpen} onClose={()=>setAssignOpen(false)}>
        <DialogTitle>Assign LOE to Priority</DialogTitle>
        <DialogContent>
          <Box sx={{ mt:1, minWidth:360 }}>
            <FormControl fullWidth size="small">
              <InputLabel id="select-loe-label">Select LOE</InputLabel>
              <Select labelId="select-loe-label" value={selectedLoe ?? ''} label="Select LOE" onChange={(e:any)=>setSelectedLoe(e.target.value)}>
                {assignAvailable.map(a=> (
                  <MenuItem key={a.id} value={a.id}>{a.title || a.name || `LOE ${a.id}`}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>setAssignOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={confirmAssign}>Assign</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
