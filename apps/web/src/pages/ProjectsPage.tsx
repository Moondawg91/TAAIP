import React, {useState, useEffect} from 'react'
import { Box, Typography, TextField, Button, Paper, Table, TableHead, TableRow, TableCell, TableBody, IconButton } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import { createProject, createTask, listProjects, listTasks } from '../api/client'
import { useNavigate } from 'react-router-dom'

export default function ProjectsPage(){
  const [projectName, setProjectName] = useState('')
  const [taskTitle, setTaskTitle] = useState('')
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [tasks, setTasks] = useState([])
  const [filter, setFilter] = useState('')

  useEffect(()=>{ loadProjects() }, [])

  async function loadProjects(){
    try{
      const res = await listProjects()
      setProjects(res || [])
    }catch(e){ console.error('list projects', e) }
  }

  async function handleCreateProject(){
    try{
      const res = await createProject({ name: projectName })
      setProjectName('')
      await loadProjects()
      setSelectedProject(res.id)
      alert('Project created: ' + res.id)
    }catch(e){ console.error(e); alert('create project failed') }
  }

  async function handleCreateTask(){
    if (!selectedProject) return alert('Select a project first')
    try{
      const res = await createTask({ project_id: selectedProject, title: taskTitle })
      setTaskTitle('')
      await loadTasks(selectedProject)
      alert('Task created: ' + res.id)
    }catch(e){ console.error(e); alert('create task failed') }
  }

  async function loadTasks(projectId){
    try{
      const res = await listTasks(projectId)
      setTasks(res || [])
    }catch(e){ console.error('list tasks', e); setTasks([]) }
  }

  const navigate = useNavigate()
  function selectProject(p){
    navigate(`/projects/${p.id}`)
  }

  const filtered = projects.filter(p => !filter || (p.name || '').toLowerCase().includes(filter.toLowerCase()) || String(p.org_unit_id || '').includes(filter))

  return (
    <Box sx={{p:3}}>
      <Typography variant="h5">Projects</Typography>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Projects</Typography>
        <Box sx={{ display:'flex', gap:1, mb:1 }}>
          <TextField size="small" placeholder="Filter by name or scope id" value={filter} onChange={e=>setFilter(e.target.value)} />
          <Button size="small" onClick={loadProjects}>Refresh</Button>
        </Box>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Org Unit</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map(p=> (
              <TableRow key={p.id} selected={selectedProject===p.id}>
                <TableCell>{p.name}</TableCell>
                <TableCell>{p.org_unit_id || '—'}</TableCell>
                <TableCell>{p.status || '—'}</TableCell>
                <TableCell>
                  <IconButton size="small" onClick={()=>selectProject(p)} title="Open tasks"><PlayArrowIcon /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Create Project</Typography>
        <Box sx={{ display:'flex', gap:1, mt:1 }}>
          <TextField label="Project name" value={projectName} onChange={(e)=>setProjectName(e.target.value)} fullWidth />
          <Button variant="contained" onClick={handleCreateProject}>Create</Button>
        </Box>
      </Paper>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Tasks {selectedProject ? `(Project ${selectedProject})` : ''}</Typography>
        <Box sx={{ display:'flex', gap:1, mt:1 }}>
          <TextField label="Task title" value={taskTitle} onChange={(e)=>setTaskTitle(e.target.value)} fullWidth />
          <Button variant="contained" onClick={handleCreateTask}>Create Task</Button>
        </Box>
        <Table size="small" sx={{ mt:1 }}>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(tasks||[]).map(t=> (
              <TableRow key={t.id}>
                <TableCell>{t.title}</TableCell>
                <TableCell>{t.owner || '—'}</TableCell>
                <TableCell>{t.status || '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  )
}
