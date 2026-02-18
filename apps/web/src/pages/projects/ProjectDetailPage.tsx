import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Box, Typography, Card, CardContent, Table, TableHead, TableRow, TableCell, TableBody, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button } from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import { getProject, listTasks, updateTask, assignTask } from '../../api/client'

function TaskEditDialog({ open, task, onClose, onSaved }:{open:boolean, task:any, onClose:()=>void, onSaved:()=>void}){
  const [form, setForm] = useState({ owner: '', status: '', percent_complete: 0 })
  useEffect(()=>{ if(task){ setForm({ owner: task.owner || '', status: task.status || '', percent_complete: task.percent_complete || 0 }) } }, [task])

  async function save(){
    try{
      await updateTask(task.id, form)
      onSaved()
      onClose()
    }catch(e){ console.error('update task', e); alert('update failed') }
  }

  async function doAssign(){
    try{
      await assignTask(task.id, { assignee: form.owner })
      onSaved()
      onClose()
    }catch(e){ console.error('assign task', e); alert('assign failed') }
  }

  if(!task) return null
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Edit Task</DialogTitle>
      <DialogContent>
        <Box sx={{ display:'flex', flexDirection:'column', gap:2, minWidth:400 }}>
          <TextField label="Owner" value={form.owner} onChange={e=>setForm(s=>({ ...s, owner: e.target.value }))} />
          <TextField label="Status" value={form.status} onChange={e=>setForm(s=>({ ...s, status: e.target.value }))} />
          <TextField label="Percent Complete" type="number" value={form.percent_complete} onChange={e=>setForm(s=>({ ...s, percent_complete: parseInt(e.target.value || '0',10) }))} />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={doAssign}>Assign</Button>
        <Button variant="contained" onClick={save}>Save</Button>
      </DialogActions>
    </Dialog>
  )
}

export default function ProjectDetailPage(){
  const { id } = useParams()
  const [project, setProject] = useState<any>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<any>(null)

  useEffect(()=>{ load() }, [id])

  async function load(){
    setLoading(true)
    try{
      const p = await getProject(Number(id))
      setProject(p)
      const t = await listTasks(Number(id))
      setTasks(t || [])
    }catch(e){ console.error('load project', e) }
    finally{ setLoading(false) }
  }

  function openEdit(task){ setEditingTask(task); setEditOpen(true) }

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h5">Project {id}</Typography>
      <Card sx={{ mt:2, bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Details</Typography>
          {project ? (
            <Box>
              <Typography><strong>Name:</strong> {project.name}</Typography>
              <Typography><strong>Description:</strong> {project.description || '—'}</Typography>
              <Typography><strong>Org Unit:</strong> {project.org_unit_id || '—'}</Typography>
            </Box>
          ) : <Typography>Loading...</Typography>}
        </CardContent>
      </Card>

      <Card sx={{ mt:2, bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Tasks ({tasks.length})</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Percent</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map(t=> (
                <TableRow key={t.id}>
                  <TableCell>{t.title}</TableCell>
                  <TableCell>{t.owner || '—'}</TableCell>
                  <TableCell>{t.status || '—'}</TableCell>
                  <TableCell>{t.percent_complete != null ? t.percent_complete : '—'}</TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={()=>openEdit(t)}><EditIcon /></IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <TaskEditDialog open={editOpen} task={editingTask} onClose={()=>setEditOpen(false)} onSaved={load} />
    </Box>
  )
}
