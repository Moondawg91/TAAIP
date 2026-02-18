import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText, IconButton, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { Link } from 'react-router-dom'
import { listRoles, createRole, deleteRole, updateRole, deleteRoleForce } from '../../api/client'
import { assignRole } from '../../api/client'
import { TextField, Button } from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import DeleteForeverIcon from '@mui/icons-material/DeleteForever'

export default function AdminRolesPage(){
  const [roles, setRoles] = useState([])
  const [username, setUsername] = useState('')
  const [selectedRole, setSelectedRole] = useState('')
  const [newRoleName, setNewRoleName] = useState('')
  const [newRoleDesc, setNewRoleDesc] = useState('')
  const [editOpen, setEditOpen] = useState(false)
  const [editRole, setEditRole] = useState<any>(null)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [forceOpen, setForceOpen] = useState(false)
  const [forceRole, setForceRole] = useState<any>(null)
  const [forceConfirm, setForceConfirm] = useState('')
  useEffect(()=>{ load() }, [])
  async function load(){
    try{ const r = await listRoles(); setRoles(r || []) }catch(e){ console.error('load roles', e) }
  }

  async function handleCreateRole(){
    if(!newRoleName) return alert('role name required')
    try{
      await createRole({ name: newRoleName, description: newRoleDesc })
      setNewRoleName('')
      setNewRoleDesc('')
      await load()
    }catch(e){ console.error(e); alert('create failed') }
  }

  async function handleDeleteRole(r){
    if(!confirm(`Delete role ${r.name}? This will remove the role from all users. Currently assigned users: ${r.user_count || 0}`)) return
    try{
      await deleteRole(r.id)
      await load()
    }catch(e){ console.error(e); alert('delete failed') }
  }

  async function handleEditRole(r){
    setEditRole(r)
    setEditName(r.name)
    setEditDesc(r.description || '')
    setEditOpen(true)
  }

  async function handleEditSave(){
    if(!editRole) return
    try{
      await updateRole(editRole.id, { name: editName, description: editDesc })
      setEditOpen(false)
      setEditRole(null)
      await load()
    }catch(e){ console.error(e); alert(e?.body || 'update failed') }
  }

  function openForceDialog(r){
    setForceRole(r)
    setForceConfirm('')
    setForceOpen(true)
  }

  async function handleForceDelete(){
    if(!forceRole) return
    if(forceConfirm !== (forceRole?.name || '')){ return alert('Please type the role name to confirm') }
    try{
      await deleteRoleForce(forceRole.id)
      setForceOpen(false)
      setForceRole(null)
      setForceConfirm('')
      await load()
    }catch(e){ console.error(e); alert(e?.body || 'force delete failed') }
  }

  async function handleAssign(){
    if(!username || !selectedRole) return alert('username and role required')
    try{
      await assignRole({ username, role: selectedRole })
      alert('role assigned')
      setUsername('')
      setSelectedRole('')
    }catch(e){ console.error(e); alert('assign failed') }
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Role & Scope Control</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Define roles and scope access for users.</Typography>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Roles</Typography>
          <Box sx={{ display:'flex', gap:1, mb:2 }}>
            <TextField size="small" label="Username" value={username} onChange={e=>setUsername(e.target.value)} />
            <TextField select size="small" label="Role" value={selectedRole} onChange={e=>setSelectedRole(e.target.value)} sx={{ minWidth:200 }} SelectProps={{ native: true }}>
              <option value=""></option>
              {(roles || []).map((r:any)=> (<option key={r.id} value={r.name}>{r.name}</option>))}
            </TextField>
            <Button variant="contained" onClick={handleAssign}>Assign Role</Button>
          </Box>

          <Box sx={{ display:'flex', gap:1, alignItems:'center', mb:2 }}>
            <TextField size="small" label="Role name" value={newRoleName} onChange={e=>setNewRoleName(e.target.value)} />
            <TextField size="small" label="Description" value={newRoleDesc} onChange={e=>setNewRoleDesc(e.target.value)} sx={{ minWidth:300 }} />
            <Button variant="outlined" onClick={handleCreateRole}>Create Role</Button>
          </Box>
          <List>
            {(roles || []).map((r:any)=> (
              <ListItem key={r.id} secondaryAction={<>
                  <IconButton edge="end" onClick={()=>handleEditRole(r)} aria-label="edit"><EditIcon/></IconButton>
                  <IconButton edge="end" onClick={()=>handleDeleteRole(r)} aria-label="delete" disabled={r.user_count>0}><DeleteIcon/></IconButton>
                  {r.user_count>0 && (
                    <IconButton edge="end" onClick={()=>openForceDialog(r)} aria-label="force-delete"><DeleteForeverIcon color="error"/></IconButton>
                  )}
                </>}>
                <ListItemText primary={<Link to={`/admin/roles/${r.id}`}>{r.name} {r.user_count ? `(${r.user_count})` : ''}</Link>} secondary={r.description} />
              </ListItem>
            ))}
          </List>

          <Dialog open={editOpen} onClose={()=>setEditOpen(false)}>
            <DialogTitle>Edit Role</DialogTitle>
            <DialogContent>
              <Box sx={{ display:'flex', flexDirection:'column', gap:2, mt:1 }}>
                <TextField label="Name" value={editName} onChange={e=>setEditName(e.target.value)} />
                <TextField label="Description" value={editDesc} onChange={e=>setEditDesc(e.target.value)} />
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={()=>setEditOpen(false)}>Cancel</Button>
              <Button variant="contained" onClick={handleEditSave}>Save</Button>
            </DialogActions>
          </Dialog>
          <Dialog open={forceOpen} onClose={()=>setForceOpen(false)}>
            <DialogTitle>Force Delete Role</DialogTitle>
            <DialogContent>
              <Typography>Role: {forceRole?.name}</Typography>
              <Typography sx={{ mt:1 }}>This will remove the role and unassign it from {forceRole?.user_count || 0} users. This action cannot be undone.</Typography>
              <Typography sx={{ mt:2, fontWeight:500 }}>Type the role name to confirm:</Typography>
              <TextField size="small" fullWidth value={forceConfirm} onChange={e=>setForceConfirm(e.target.value)} placeholder={forceRole?.name} />
            </DialogContent>
            <DialogActions>
              <Button onClick={()=>{ setForceOpen(false); setForceConfirm('') }}>Cancel</Button>
              <Button color="error" variant="contained" onClick={handleForceDelete} disabled={forceConfirm !== (forceRole?.name || '')}>Force Delete</Button>
            </DialogActions>
          </Dialog>
        </CardContent>
      </Card>
    </Box>
  )
}
