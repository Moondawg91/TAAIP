import React from 'react'
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow, CircularProgress } from '@mui/material'

export default function MarketIntelDemographicsTable({ data, loading }){
  if(loading) return <Box sx={{display:'flex', justifyContent:'center', p:2}}><CircularProgress size={20} /></Box>
  if(!data || (!data.demographics && !data.rows)) return <Typography variant="body2" sx={{p:1}}>No demographic data available.</Typography>

  const rows = data.demographics || data.rows || []

  return (
    <Box>
      <Typography variant="subtitle1" sx={{mb:1}}>Demographics</Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="right">Value</TableCell>
            <TableCell align="right">Gap</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((r, idx)=> (
            <TableRow key={idx}>
              <TableCell>{r.name || r.key || r.label}</TableCell>
              <TableCell align="right">{r.value != null ? (Number(r.value).toLocaleString()) : '-'}</TableCell>
              <TableCell align="right">{r.gap != null ? `${r.gap}%` : '-'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  )
}
