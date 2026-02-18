import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText, TextField, Button } from '@mui/material'
import { createUser, listUsers } from '../../api/client'

export default function AdminUsersPage(){
  const [users, setUsers] = useState([])
  const [newUser, setNewUser] = useState({ username:'', display_name:'', email:'' })

  async function handleCreate(){
    if(!newUser.username) return alert('username required')
    try{
      await createUser(newUser)
      setNewUser({ username:'', display_name:'', email:'' })
      // no listing endpoint; show success
      alert('user created/ensured')
    }catch(e){ console.error(e); alert('create failed') }
  }

  useEffect(()=>{ loadUsers() }, [])
  async function loadUsers(){
    try{ const u = await listUsers(); setUsers(u || []) }catch(e){ console.error('list users', e) }
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">User Management</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Manage users, roles, and access scopes.</Typography>
      <Card sx={{ bgcolor:'background.paper', mb:2 }}>
        <CardContent>
          <Typography variant="h6">Create User</Typography>
          <Box sx={{ display:'flex', gap:1, mt:1 }}>
            <TextField size="small" label="Username" value={newUser.username} onChange={e=>setNewUser(s=>({ ...s, username: e.target.value }))} />
            <TextField size="small" label="Display Name" value={newUser.display_name} onChange={e=>setNewUser(s=>({ ...s, display_name: e.target.value }))} />
            <TextField size="small" label="Email" value={newUser.email} onChange={e=>setNewUser(s=>({ ...s, email: e.target.value }))} />
            <Button variant="contained" onClick={handleCreate}>Create</Button>
          </Box>
        </CardContent>
      </Card>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Users</Typography>
          <List>
            {(users || []).map((u:any)=> <ListItem key={u.id}><ListItemText primary={u.username} secondary={u.display_name || u.email || ''} /></ListItem>)}
          </List>
        </CardContent>
      </Card>
    </Box>
  )
}
