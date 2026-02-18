import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText, Button } from '@mui/material'
import { listRoles, getRoleUsers, removeRole } from '../../api/client'

export default function RoleDetailPage(){
  const { id } = useParams()
  const [role, setRole] = useState<any>(null)
  const [users, setUsers] = useState<any[]>([])

  useEffect(()=>{ load() }, [id])
  async function load(){
    try{
      const roles = await listRoles()
      const r = (roles || []).find((x:any)=> String(x.id) === String(id))
      setRole(r || null)
      if(r){
        const u = await getRoleUsers(r.id)
        setUsers(u || [])
      }
    }catch(e){ console.error('load role', e) }
  }

  const nav = useNavigate()

  async function handleRemove(u:any){
    if(!role) return
    if(!confirm(`Remove role ${role.name} from ${u.username}?`)) return
    try{
      await removeRole({ username: u.username, role: role.name })
      await load()
    }catch(e){ console.error('remove role', e); alert('remove failed') }
  }

  return (
    <Box sx={{ p:3 }}>
      <Button variant="text" onClick={()=>nav(-1)}>Back</Button>
      <Typography variant="h5">Role Details</Typography>
      <Card sx={{ mt:2, bgcolor:'background.paper' }}>
        <CardContent>
          {role ? (
            <>
              <Typography variant="h6">{role.name}</Typography>
              <Typography variant="body2" sx={{ color:'text.secondary' }}>{role.description}</Typography>
            </>
          ) : <Typography>Loading...</Typography>}
        </CardContent>
      </Card>

      <Card sx={{ mt:2, bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Assigned Users</Typography>
          <List>
            {(users || []).map(u=> (
              <ListItem key={u.id} secondaryAction={<Button color="error" size="small" onClick={()=>handleRemove(u)}>Remove</Button>}>
                <ListItemText primary={u.username} secondary={u.display_name || u.email} />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  )
}
