import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText, TextField, Button, Dialog, DialogTitle, DialogContent, DialogActions, MenuItem, Select, InputLabel, FormControl, IconButton } from '@mui/material'
import EmptyState from '../../components/common/EmptyState'
import { getCurrentUserFromToken } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import { createUser, listUsers, listAdminUsers, inviteAdminUser, importAdminUsers, listRoles, getAdminPermissionsRegistry, getAdminUserPermissions, setAdminUserRoles, setAdminUserPermissionOverrides } from '../../api/client'
import EditIcon from '@mui/icons-material/Edit'

export default function AdminUsersPage(){
  const [users, setUsers] = useState([])
  const [newUser, setNewUser] = useState({ username:'', display_name:'', email:'' })
  const [invite, setInvite] = useState({ email: '', name: '', roles: '' })
  const [userRoles, setUserRoles] = useState<string[]>([])
  const [rolesList, setRolesList] = useState<string[]>([])
  const [permRegistry, setPermRegistry] = useState<any[]>([])
  const editingUserRef = React.useRef<any|null>(null)
  const [editingUserKey, setEditingUserKey] = useState<number|null>(null)
  const [editingOverrides, setEditingOverrides] = useState<Record<string, boolean>>({})

  const auth = useAuth()
  useEffect(()=>{
    try{
      if (!auth.loading && auth.roles) setUserRoles(auth.roles.map(r=>String(r).toLowerCase()))
    }catch(e){}
  },[auth.loading])

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
    try{
      // prefer admin list when available
      const u = await listAdminUsers().catch(()=> listUsers())
      setUsers((u && u.users) || u || [])
    }catch(e){ console.error('list users', e) }
  }

  useEffect(()=>{ (async ()=>{
    try{ const r = await listRoles().catch(()=>[]) ; setRolesList((r || []).map(rr=> rr.key || rr)); }catch(e){}
    try{ const pr = await getAdminPermissionsRegistry().catch(()=>[]); setPermRegistry(pr || []) }catch(e){}
  })() }, [])

  async function handleInvite(){
    if(!invite.email) return alert('email required')
    try{
      const payload = { email: invite.email, name: invite.name, roles: invite.roles ? invite.roles.split(',').map(s=>s.trim()) : [] }
      const res = await inviteAdminUser(payload)
      alert('Invited: ' + (res.invite_link || 'ok'))
      setInvite({ email:'', name:'', roles:'' })
      loadUsers()
    }catch(e){ console.error(e); alert('invite failed') }
  }

  async function handleImport(fileInput:any){
    const f = fileInput?.files?.[0]
    if(!f) return alert('select a CSV file')
    try{
      const res = await importAdminUsers(f)
      alert(`Import done. created:${res.created} updated:${res.updated} skipped:${res.skipped}`)
      loadUsers()
    }catch(e){ console.error(e); alert('import failed') }
  }

  function openEdit(user:any){
    editingUserRef.current = user
    // toggle key to force a re-render and ensure UI picks up the ref change
    setEditingUserKey(null);
    setTimeout(()=> setEditingUserKey(user?.id || null), 0);
    // load overrides
    (async ()=>{
      try{ const perms = await getAdminUserPermissions(user.id).catch(()=>[]); const map:any = {}; perms.forEach(p=> map[p.permission_key]= Boolean(p.granted)); setEditingOverrides(map) }catch(e){}
    })()
  }

  async function saveEdit(){
    const editingUser = editingUserRef.current
    if(!editingUser) return
    try{
      const roles = (editingUser.roles || [])
      await setAdminUserRoles(editingUser.id, roles)
      await setAdminUserPermissionOverrides(editingUser.id, editingOverrides)
      alert('saved')
      editingUserRef.current = null
      setEditingUserKey(null)
      loadUsers()
    }catch(e){ console.error(e); alert('save failed') }
  }

  const canManage = (!auth.loading && (Boolean(auth.permissions && (auth.permissions['ADMIN_MANAGE_USERS'] || auth.permissions['admin.permissions.manage'])) || auth.isAdmin))
  if (!canManage){
    return (
      <Box sx={{ p:3 }}>
        <EmptyState title="No access" subtitle="You do not have permission to manage users." />
      </Box>
    )
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">User Management</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Manage users, roles, and echelon access.</Typography>
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
      <Card sx={{ bgcolor:'background.paper', mb:2 }}>
        <CardContent>
          <Typography variant="h6">Invite User</Typography>
          <Box sx={{ display:'flex', gap:1, mt:1 }}>
            <TextField size="small" label="Email" value={invite.email} onChange={e=>setInvite(s=>({ ...s, email: e.target.value }))} />
            <TextField size="small" label="Name" value={invite.name} onChange={e=>setInvite(s=>({ ...s, name: e.target.value }))} />
            <TextField size="small" label="Roles (comma)" value={invite.roles} onChange={e=>setInvite(s=>({ ...s, roles: e.target.value }))} />
            <Button variant="contained" onClick={handleInvite}>Invite</Button>
          </Box>
          <Box sx={{ mt:2 }}>
            <Typography variant="subtitle2">Import CSV</Typography>
            <input type="file" accept="text/csv" id="users_csv" onChange={e=>handleImport(e.target)} />
          </Box>
        </CardContent>
      </Card>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Users</Typography>
          <List>
            {(users || []).map((u:any)=> (
              <ListItem key={u.id} secondaryAction={
                <IconButton edge="end" aria-label="edit" onClick={()=>openEdit(u)}>
                  <EditIcon />
                </IconButton>
              }>
                <ListItemText primary={u.username} secondary={u.display_name || u.email || ''} />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      <Dialog open={Boolean(editingUserKey)} onClose={()=>{ editingUserRef.current = null; setEditingUserKey(null); setTimeout(()=> setEditingUserKey(null), 0) }} maxWidth="md" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          {editingUserKey && (
            <Box sx={{ display:'flex', gap:2, flexDirection:'column' }}>
              <Typography>{editingUserRef.current?.username}</Typography>
                <FormControl fullWidth>
                <InputLabel>Roles</InputLabel>
                <Select multiple value={editingUserRef.current?.roles || []} onChange={(e:any)=> { editingUserRef.current = {...editingUserRef.current, roles: e.target.value}; setEditingUserKey(null); setTimeout(()=> setEditingUserKey(editingUserRef.current?.id || null), 0) }} label="Roles">
                  {(rolesList || []).map(r=> <MenuItem key={r} value={r}>{r}</MenuItem>)}
                </Select>
              </FormControl>
              <Box>
                <Typography variant="subtitle2">Permission Overrides</Typography>
                {/* Default locked permissions */}
                {['READ_DASHBOARDS','EXPORT_DATA','read_dashboards','export.data'].map(k=> (
                  <Box key={k} sx={{ display:'flex', alignItems:'center', gap:1, opacity:0.8 }}>
                    <label style={{ minWidth:300 }}>{k} — Default granted</label>
                    <Button size="small" variant="contained" disabled>Locked</Button>
                  </Box>
                ))}
                {(permRegistry || []).map(p=> (
                  <Box key={p.key} sx={{ display:'flex', alignItems:'center', gap:1 }}>
                    <label style={{ minWidth:300 }}>{p.key} — {p.description}</label>
                    <Button size="small" variant={editingOverrides[p.key] ? 'contained' : 'outlined'} onClick={()=> setEditingOverrides(s=>({ ...s, [p.key]: !s[p.key] }))}>{editingOverrides[p.key] ? 'Granted' : 'Not granted'}</Button>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={()=>{ editingUserRef.current = null; setEditingUserKey(null); setTimeout(()=> setEditingUserKey(null),0) }}>Cancel</Button>
          <Button variant="contained" onClick={saveEdit}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
