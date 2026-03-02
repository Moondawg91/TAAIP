import React, { useEffect, useState } from 'react'
import { Box, Typography, TextField, Button, List, ListItem, ListItemText, ListItemSecondaryAction, IconButton, Divider, MenuItem, Select, FormControl, InputLabel } from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import SaveIcon from '@mui/icons-material/Save'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import * as api from '../../api/client'
import { useEchelon } from '../../contexts/ScopeContext'
import { useFilters } from '../../contexts/FilterContext'

type Loe = {
  id: number | string
  org_unit_id?: number
  fy?: string
  qtr?: string
  name: string
  description?: string
}

export default function LinesOfEffortPage(){
  const { echelon } = useEchelon()
  const [loes, setLoes] = useState<Loe[]>([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [newScope, setNewScope] = useState('')
  const [editingId, setEditingId] = useState<number|string|null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [editScope, setEditScope] = useState('')
  const { filters } = useFilters()

  async function load(){
    setLoading(true)
    try{
      const items = await api.listLOEsForScope(echelon)
      setLoes(items || [])
    }catch(e){
      console.error('load loes', e)
    }finally{
      setLoading(false)
    }
  }

  useEffect(()=>{ load() }, [echelon])

  async function handleCreate(){
    if(!newTitle) return
    try{
      const orgUnit = parseInt(newScope, 10)
      await api.createLOE({ name: newTitle, description: newDesc, fy: filters?.fy || null, qtr: filters?.qtr || null, org_unit_id: Number.isFinite(orgUnit) ? orgUnit : null })
      setNewTitle('')
      setNewDesc('')
      // FY/QTR controlled globally; don't reset them locally
      setNewScope('')
      setCreating(false)
      load()
    }catch(e){ console.error(e) }
  }

  function startEdit(item:Loe){
    setEditingId(item.id)
    setEditTitle(item.name)
    setEditDesc(item.description || '')
    setEditScope(item.org_unit_id ? String(item.org_unit_id) : '')
  }

  async function saveEdit(id: number|string){
    try{
      const orgUnit = parseInt(editScope, 10)
      await api.updateLOE(id, { name: editTitle, description: editDesc, fy: filters?.fy || null, qtr: filters?.qtr || null, org_unit_id: Number.isFinite(orgUnit) ? orgUnit : null })
      setEditingId(null)
      load()
    }catch(e){ console.error(e) }
  }

  async function handleDelete(id: number|string){
    if(!window.confirm('Delete LOE? This cannot be undone.')) return
    try{
      await api.deleteLOE(id)
      load()
    }catch(e){ console.error(e) }
  }

  return (
    <Box>
      <Typography variant="h4">Lines of Effort (LOE)</Typography>
      <Typography variant="body2" color="text.secondary">Create and manage Lines of Effort. Changes are persisted to the database.</Typography>

      <Box sx={{ mt:2, mb:2 }}>
        {creating ? (
          <Box sx={{ display:'flex', gap:1, alignItems:'center' }}>
            <TextField label="Title" size="small" value={newTitle} onChange={e=>setNewTitle(e.target.value)} />
            <TextField label="Description" size="small" value={newDesc} onChange={e=>setNewDesc(e.target.value)} />
            {/* FY/QTR are controlled globally via filters */}
            <TextField label="Unit ID" size="small" value={newScope} onChange={e=>setNewScope(e.target.value)} />
            <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>Create</Button>
            <Button variant="text" onClick={()=>setCreating(false)}>Cancel</Button>
          </Box>
        ) : (
          <Button variant="contained" startIcon={<AddIcon />} onClick={()=>setCreating(true)}>Add LOE</Button>
        )}
      </Box>

      <Divider sx={{ mb:2 }} />

      <List>
        {loes.map((l:Loe)=> (
          <ListItem key={String(l.id)} sx={{ alignItems:'flex-start' }}>
            <ListItemText primary={editingId===l.id ? (
              <TextField size="small" value={editTitle} onChange={e=>setEditTitle(e.target.value)} fullWidth />
            ) : (
              <Typography sx={{ fontWeight:700 }}>{l.name}</Typography>
            )} secondary={editingId===l.id ? (
              <Box>
                <TextField size="small" value={editDesc} onChange={e=>setEditDesc(e.target.value)} fullWidth sx={{ mb:1 }} />
                <Box sx={{ display:'flex', gap:1 }}>
                  <TextField size="small" label="Unit ID" value={editScope} onChange={e=>setEditScope(e.target.value)} />
                </Box>
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" color="text.secondary">{l.description}</Typography>
                <Typography variant="caption" sx={{ color:'text.secondary' }}>FY: {l.fy || 'N/A'} • QTR: {l.qtr || 'N/A'} • Unit: {l.org_unit_id || '—'}</Typography>
              </Box>
            )} />
            <ListItemSecondaryAction>
              {editingId===l.id ? (
                <IconButton edge="end" onClick={()=>saveEdit(l.id)}><SaveIcon /></IconButton>
              ) : (
                <Box sx={{ display:'flex', alignItems:'center' }}>
                  <IconButton edge="end" onClick={()=>startEdit(l)}><EditIcon /></IconButton>
                  <IconButton edge="end" onClick={()=>handleDelete(l.id)}><DeleteIcon /></IconButton>
                </Box>
              )}
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>
    </Box>
  )
}
