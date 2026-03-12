import React from 'react'
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material'

export default function MarketIntelTargetsPanel({targets}){
  if (!targets || targets.length===0) return <Typography variant="body2">No targets defined for this context.</Typography>
  return (
    <Box>
      <Typography variant="subtitle2" sx={{mb:1}}>Targets</Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Type</TableCell>
            <TableCell>FY</TableCell>
            <TableCell>QTR</TableCell>
            <TableCell>RSID</TableCell>
            <TableCell>ZIP/CBSA</TableCell>
            <TableCell>Rationale</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {targets.map((t,i)=> (
            <TableRow key={i}>
              <TableCell>{t.target_type}</TableCell>
              <TableCell>{t.fy}</TableCell>
              <TableCell>{t.qtr}</TableCell>
              <TableCell>{t.rsid_prefix}</TableCell>
              <TableCell>{t.zip5 || t.cbsa_code || '—'}</TableCell>
              <TableCell>{t.rationale || '—'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  )
}
