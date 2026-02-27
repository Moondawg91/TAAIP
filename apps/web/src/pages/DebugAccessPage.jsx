import React from 'react'
import { Box, Typography, Table, TableBody, TableRow, TableCell } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'

export default function DebugAccessPage(){
  const auth = useAuth()
  return (
    <Box sx={{p:3}}>
      <Typography variant="h5">Debug Access</Typography>
      <Table>
        <TableBody>
          <TableRow><TableCell>authLoading</TableCell><TableCell>{String(auth.loading)}</TableCell></TableRow>
          <TableRow><TableCell>user roles</TableCell><TableCell>{(auth.roles||[]).join(', ')}</TableCell></TableRow>
          <TableRow><TableCell>isAdmin</TableCell><TableCell>{String(auth.isAdmin)}</TableCell></TableRow>
          <TableRow><TableCell>permissions (count)</TableCell><TableCell>{(auth.permissions||[]).length}</TableCell></TableRow>
          <TableRow><TableCell>sample perms</TableCell><TableCell>{(auth.permissions||[]).slice(0,10).join(', ')}</TableCell></TableRow>
        </TableBody>
      </Table>
    </Box>
  )
}
