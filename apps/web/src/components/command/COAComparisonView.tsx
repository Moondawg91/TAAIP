import React from 'react'
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper } from '@mui/material'

export default function COAComparisonView({coas=[]}){
  if(!coas || coas.length===0){
    return (
      <Paper sx={{ p:2, bgcolor:'background.paper', borderRadius:'4px' }}>
        <Typography variant="h6">COA Comparison</Typography>
        <Typography variant="body2" sx={{ color:'text.secondary' }}>No COAs to compare.</Typography>
      </Paper>
    )
  }
  return (
    <Paper sx={{ p:2, bgcolor:'background.paper', borderRadius:'4px' }}>
      <Typography variant="h6">COA Comparison</Typography>
      <Box sx={{ overflowX:'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>COA</TableCell>
              <TableCell>Impact</TableCell>
              <TableCell>Risk</TableCell>
              <TableCell>Resource</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {coas.map(c=> (
              <TableRow key={c.id}>
                <TableCell>{c.title}</TableCell>
                <TableCell>{c.projected_impact_score ?? '-'}</TableCell>
                <TableCell>{c.risk_tier ?? '-'}</TableCell>
                <TableCell>{c.resource_requirement_level ?? '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    </Paper>
  )
}
