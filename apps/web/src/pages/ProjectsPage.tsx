import React, {useState} from 'react'
import { Box, Typography, TextField, Button, Paper } from '@mui/material'
import { createProject, createTask } from '../api/client'

export default function ProjectsPage(){
  const [projectName, setProjectName] = useState('')
  const [projectId, setProjectId] = useState(null)
  const [taskTitle, setTaskTitle] = useState('')

  async function handleCreateProject(){
    const res = await createProject({ name: projectName })
    setProjectId(res.id)
    alert('Project created: ' + res.id)
  }

  async function handleCreateTask(){
    if (!projectId) return alert('Create a project first')
    const res = await createTask({ project_id: projectId, title: taskTitle })
    alert('Task created: ' + res.id)
  }

  return (
    <Box sx={{p:3}}>
      <Typography variant="h5">Projects</Typography>
      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Create Project</Typography>
        <TextField label="Project name" value={projectName} onChange={(e)=>setProjectName(e.target.value)} fullWidth />
        <Box sx={{mt:1}}>
          <Button variant="contained" onClick={handleCreateProject}>Create</Button>
        </Box>
      </Paper>

      <Paper sx={{p:2, mt:2}}>
        <Typography variant="subtitle1">Create Task (for created project)</Typography>
        <TextField label="Task title" value={taskTitle} onChange={(e)=>setTaskTitle(e.target.value)} fullWidth />
        <Box sx={{mt:1}}>
          <Button variant="contained" onClick={handleCreateTask}>Create Task</Button>
        </Box>
      </Paper>
    </Box>
  )
}
