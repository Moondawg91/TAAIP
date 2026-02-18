import React, { useEffect, useState } from 'react'
import { Box, Typography, TextField, Button, List, ListItem, ListItemText, ListItemSecondaryAction, IconButton, Divider, MenuItem, Select, FormControl, InputLabel } from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import SaveIcon from '@mui/icons-material/Save'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import * as api from '../../api/client'
import { useScope } from '../../contexts/ScopeContext'

type Loe = {
  id: number | string
  org_unit_id?: number
  fy?: string
  qtr?: string
  name: string
  description?: string
}

export default function LinesOfEffortPage(){
  const { scope } = useScope()
  const [loes, setLoes] = useState<Loe[]>([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [newFY, setNewFY] = useState('FY26')
  const [newQTR, setNewQTR] = useState('Q1')
  const [newScope, setNewScope] = useState('')
  const [editingId, setEditingId] = useState<number|string|null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [editFY, setEditFY] = useState('FY26')
  const [editQTR, setEditQTR] = useState('Q1')
  const [editScope, setEditScope] = useState('')

  async function load(){
    setLoading(true)
    try{
      const items = await api.listLOEsForScope(scope)
      setLoes(items || [])
    }catch(e){
      console.error('load loes', e)
    }finally{
      setLoading(false)
    }
  }

  useEffect(()=>{ load() }, [scope])

  async function handleCreate(){
    if(!newTitle) return
    try{
      const orgUnit = parseInt(newScope, 10)
      await api.createLOE({ name: newTitle, description: newDesc, fy: newFY, qtr: newQTR, org_unit_id: Number.isFinite(orgUnit) ? orgUnit : null })
      setNewTitle('')
      setNewDesc('')
      setNewFY('FY26')
      setNewQTR('Q1')
      setNewScope('')
      setCreating(false)
      load()
    }catch(e){ console.error(e) }
  }

  function startEdit(item:Loe){
    setEditingId(item.id)
    setEditTitle(item.name)
    setEditDesc(item.description || '')
    setEditFY(item.fy || 'FY26')
    setEditQTR(item.qtr || 'Q1')
    setEditScope(item.org_unit_id ? String(item.org_unit_id) : '')
  }

  async function saveEdit(id: number|string){
    try{
      const orgUnit = parseInt(editScope, 10)
      await api.updateLOE(id, { name: editTitle, description: editDesc, fy: editFY, qtr: editQTR, org_unit_id: Number.isFinite(orgUnit) ? orgUnit : null })
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
            <FormControl size="small" sx={{ minWidth:100 }}>
              <InputLabel>FY</InputLabel>
              <Select value={newFY} label="FY" onChange={e=>setNewFY(String(e.target.value))}>
                <MenuItem value="FY26">FY26</MenuItem>
                <MenuItem value="FY25">FY25</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth:100 }}>
              <InputLabel>QTR</InputLabel>
              <Select value={newQTR} label="QTR" onChange={e=>setNewQTR(String(e.target.value))}>
                <MenuItem value="Q1">Q1</MenuItem>
                <MenuItem value="Q2">Q2</MenuItem>
                <MenuItem value="Q3">Q3</MenuItem>
                <MenuItem value="Q4">Q4</MenuItem>
              </Select>
            </FormControl>
            <TextField label="Scope ID" size="small" value={newScope} onChange={e=>setNewScope(e.target.value)} />
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
                  <FormControl size="small" sx={{ minWidth:100 }}>
                    <InputLabel>FY</InputLabel>
                    <Select value={editFY} label="FY" onChange={e=>setEditFY(String(e.target.value))}>
                      <MenuItem value="FY26">FY26</MenuItem>
                      <MenuItem value="FY25">FY25</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small" sx={{ minWidth:100 }}>
                    <InputLabel>QTR</InputLabel>
                    <Select value={editQTR} label="QTR" onChange={e=>setEditQTR(String(e.target.value))}>
                      <MenuItem value="Q1">Q1</MenuItem>
                      <MenuItem value="Q2">Q2</MenuItem>
                      <MenuItem value="Q3">Q3</MenuItem>
                      <MenuItem value="Q4">Q4</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField size="small" label="Scope ID" value={editScope} onChange={e=>setEditScope(e.target.value)} />
                </Box>
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" color="text.secondary">{l.description}</Typography>
                <Typography variant="caption" sx={{ color:'text.secondary' }}>FY: {l.fy || 'N/A'} • QTR: {l.qtr || 'N/A'} • Scope: {l.org_unit_id || '—'}</Typography>
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
