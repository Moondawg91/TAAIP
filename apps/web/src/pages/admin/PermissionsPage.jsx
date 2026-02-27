import React, { useEffect, useState } from 'react'
import { Box, Typography, Select, MenuItem, Grid, Paper, Button, List, ListItem, ListItemText } from '@mui/material'
import { listAdminUsers, getAdminPermissionsRegistry, getAdminUserPermissions, grantAdminPermission, revokeAdminPermission } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'

export default function PermissionsPage(){
  const { isAdmin, permissions } = useAuth()
  const [users, setUsers] = useState([])
  const [registry, setRegistry] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [userPerms, setUserPerms] = useState({})

  useEffect(()=>{
    let mounted = true
    if(!isAdmin && !permissions['admin.permissions.manage']) return
    Promise.all([listAdminUsers(), getAdminPermissionsRegistry()]).then(([u, r])=>{
      if(!mounted) return
      setUsers(u || [])
      setRegistry((r && Array.isArray(r)) ? r : (r && r.data) ? r.data : [])
    }).catch(()=>{})
    return ()=>{ mounted = false }
  },[isAdmin, permissions])

  useEffect(()=>{
    if(!selectedUser) return
    getAdminUserPermissions(selectedUser.id).then(resp=>{
      const map = {}
      if(resp && resp.length){
        resp.forEach(p => map[p.permission_key || p.key || p] = true)
      }
      setUserPerms(map)
    }).catch(()=>{})
  },[selectedUser])

  const toggle = async (perm) => {
    if(!selectedUser) return
    try{
      if(userPerms[perm]){
        await revokeAdminPermission(selectedUser.id, perm)
        setUserPerms(prev => { const n = {...prev}; delete n[perm]; return n })
      } else {
        await grantAdminPermission(selectedUser.id, perm)
        setUserPerms(prev => ({...prev, [perm]: true}))
      }
    }catch(e){ console.error(e) }
  }

  if(!isAdmin && !permissions['admin.permissions.manage']){
    return (
      <Box sx={{ p:3 }}>
        <Typography variant="h5">Access denied</Typography>
        <Typography variant="body2" sx={{ color:'text.secondary' }}>You do not have permission to manage permissions.</Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:1 }}>Permission Management</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Grant or revoke individual permissions for users.</Typography>

      <Box sx={{ mb:2 }}>
        <Select value={selectedUser ? selectedUser.id : ''} onChange={(e)=>{
          const u = users.find(x=>String(x.id) === String(e.target.value))
          setSelectedUser(u)
          setUserPerms({})
        }} displayEmpty sx={{ minWidth:240 }}>
          <MenuItem value="">Select user</MenuItem>
          {users.map(u=> <MenuItem key={u.id} value={u.id}>{u.username || u.display_name || u.id}</MenuItem>)}
        </Select>
      </Box>

      {selectedUser && (
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Permissions for {selectedUser.username || selectedUser.display_name}</Typography>
              <List>
                {registry.map(r => {
                  const key = r.key || r.permission_key || r
                  return (
                    <ListItem key={key} secondaryAction={
                      <Button variant="outlined" size="small" onClick={()=>toggle(key)}>
                        {userPerms[key] ? 'Revoke' : 'Grant'}
                      </Button>
                    }>
                      <ListItemText primary={key} secondary={r.description || r.desc || ''} />
                    </ListItem>
                  )
                })}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  )
}
